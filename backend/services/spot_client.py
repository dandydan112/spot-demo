# backend/services/spot_client.py
from __future__ import annotations
from typing import AsyncIterator, Dict
import asyncio, io, time, threading
import numpy as np
from PIL import Image
import bosdyn.client
import bosdyn.client.util
from bosdyn.client.robot_command import RobotCommandClient, blocking_stand, blocking_sit, RobotCommandBuilder
from bosdyn.client.lease import LeaseClient, LeaseKeepAlive
from bosdyn.client.image import ImageClient
from bosdyn.api import image_pb2
from bosdyn.api import robot_command_pb2  # Bruger den til rollover
from bosdyn.client.robot_command import RobotCommandBuilder # Rollover
from . import spot_fiducial
import math
from bosdyn.client.math_helpers import SE3Pose   # SE3Pose is here
from bosdyn.geometry import EulerZXY  
from bosdyn.client.robot_state import RobotStateClient

import threading





# ============================================================
# FAKE CLIENT (bruges til test uden Spot)
# ============================================================
class FakeSpotClient:
    name = "spot-001"
    kind = "spot"
    display_name = "Spot (Demo)"

    def __init__(self, placeholder_path: str = "", w: int = 960, h: int = 540):
        self._w, self._h = w, h
        self._placeholder = placeholder_path

    async def mjpeg_frames(self) -> AsyncIterator[bytes]:
        """Simulerer en MJPEG stream ved at sende sorte billeder."""
        while True:
            arr = np.zeros((self._h, self._w, 3), dtype=np.uint8)
            img = Image.fromarray(arr, mode="RGB")
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=75)
            yield buf.getvalue()
            await asyncio.sleep(1/15)  # ~15 fps

    async def perception_stream(self) -> AsyncIterator[Dict]:
        """Simulerer perception data: en firkant der bevæger sig frem og tilbage."""
        t0 = time.time()
        while True:
            t = time.time() - t0
            x = int(100 + 200 * (0.5 + 0.5*np.sin(t)))
            yield {
                "ts": time.time(),
                "image_size": [self._w, self._h],
                "boxes": [
                    {"id": "b1", "label": "object", "score": 0.9, "xywh": [x, 120, 120, 80]}
                ],
            }
            await asyncio.sleep(0.06)  # ~15 Hz
    
    def get_battery_state(self):
        """Returner dummy batteridata til test."""
        return {
            "battery_percentage": 100.0,
            "voltage": 15.0,
            "current": 0.0,
            "temperatures": [25.0],
            "status": "STATUS_UNKNOWN",
        }

# ============================================================
# REAL CLIENT (kræver Spot SDK + en rigtig robot)
# ============================================================
class RealSpotClient:
    name = "spot-001"
    kind = "spot"
    display_name = "Spot (Real)"

    def __init__(self, hostname: str, username: str, password: str):
        try:
            print(f"[RealSpotClient] Forbinder til Spot @ {hostname} som {username}")

            # Init SDK
            self.sdk = bosdyn.client.create_standard_sdk("spot-demo")
            self.robot = self.sdk.create_robot(hostname)

            # Auth + time sync
            self.robot.authenticate(username, password)
            self.robot.start_time_sync()
            print("[RealSpotClient] Auth + Time Sync OK")

            # Clients
            self.command_client = self.robot.ensure_client(RobotCommandClient.default_service_name)
            self.lease_client   = self.robot.ensure_client(LeaseClient.default_service_name)
            self.image_client   = self.robot.ensure_client(ImageClient.default_service_name)

            # Lease: force-take hvis en anden session holder den
            self.lease_keepalive = LeaseKeepAlive(self.lease_client, must_acquire=True, return_at_exit=True)
            print("[RealSpotClient] Lease OK")

            # Fiducial follower reference (bruges til start/stop)
            self._fiducial_follower = None

        except Exception as e:
            print(f"[RealSpotClient] FEJL under init: {e}")
            raise

    # ---------------- DEMOS ----------------
    def hello_spot(self) -> str:
        print("[RealSpotClient] Starter Hello Spot demo...")

        self.robot.power_on(timeout_sec=20)
        assert self.robot.is_powered_on(), "Spot kunne ikke starte"
        print("[RealSpotClient] Power ON OK")

        blocking_stand(self.command_client, timeout_sec=10)
        print("[RealSpotClient] Spot står op")

        # Løft → vent → sænk
        self.command_client.robot_command(RobotCommandBuilder.synchro_stand_command(body_height=0.1))
        time.sleep(2)
        self.command_client.robot_command(RobotCommandBuilder.synchro_stand_command(body_height=-0.1))
        time.sleep(2)
        self.command_client.robot_command(RobotCommandBuilder.synchro_stand_command(body_height=0.0))
        print("[RealSpotClient] Tilbage til normal stand")

        return "Hello Spot demo udført!"
    
    def lay_down(self) -> str:
        print("[RealSpotClient] Lay Spot → Sit")
        self.command_client.robot_command(RobotCommandBuilder.synchro_sit_command())
        return "Spot er sat tilbage i siddende tilstand"

    def power_off(self) -> str:
        print("[RealSpotClient] Powering OFF Spot...")
        self.robot.power_off(cut_immediately=False, timeout_sec=20)
        assert not self.robot.is_powered_on(), "Kunne ikke slukke Spot"
        return "Spot er slukket."

    def power_on(self) -> str:
        print("[RealSpotClient] Powering ON Spot...")
        self.robot.power_on(timeout_sec=20)
        assert self.robot.is_powered_on(), "Kunne ikke tænde Spot"
        return "Spot er tændt."

    def roll_over(self, direction: int = 1) -> str:
        """Få Spot til at gå i 'battery change position' (rollover).
        direction: 1 = højre, 2 = venstre
        """
        print("[RealSpotClient] Rollover (battery change position)")

        # Sørg for at robotten er tændt
        self.robot.power_on(timeout_sec=20)
        assert self.robot.is_powered_on(), "Spot kunne ikke starte"

        # Sørg for at den sidder ned først
        sit_cmd = RobotCommandBuilder.synchro_sit_command()
        self.command_client.robot_command(sit_cmd)
        time.sleep(3)

        # Byg battery change pose kommando
        cmd = robot_command_pb2.RobotCommand()
        cmd.full_body_command.battery_change_pose_request.direction_hint = direction

        # Send kommando
        self.command_client.robot_command(cmd)
        print(f"[RealSpotClient] Spot laver rollover (dir={direction})")

        return "Spot er nu i battery change position (rollover)."

    def stand_up(self) -> str:
            """Få Spot til at stå op i normal position."""
            print("[RealSpotClient] Commanding Spot to stand up...")

            self.robot.power_on(timeout_sec=20)
            assert self.robot.is_powered_on(), "Spot kunne ikke starte"

            blocking_stand(self.command_client, timeout_sec=10)
            print("[RealSpotClient] Spot står nu op.")

            return "Spot står op nu."

    
    def fiducial_follow(
        self,
        distance_margin: float = 0.5,
        limit_speed: bool = True,
        avoid_obstacles: bool = False,
    ) -> str:
        """Start en fiducial follow demo i en separat tråd."""
        if self._fiducial_follower is not None:
            return "Fiducial follow kører allerede."

        print("[RealSpotClient] Starter Fiducial Follow demo...")

        options = type("Options", (), {})()
        options.distance_margin = distance_margin
        options.limit_speed = limit_speed
        options.avoid_obstacles = avoid_obstacles
        options.use_world_objects = True  # eller False hvis du vil bruge apriltag

        follower = spot_fiducial.FollowFiducial(self.robot, options)
        self._fiducial_follower = follower

        def _run():
            try:
                follower.start()
            except Exception as e:
                print("[RealSpotClient] Fiducial follow fejlede:", e)
            finally:
                # frigør reference når tråden dør
                self._fiducial_follower = None

        threading.Thread(target=_run, daemon=True).start()
        return "Fiducial follow startet."

    def fiducial_stop(self) -> str:
        """Stopper fiducial follow hvis det kører."""
        if self._fiducial_follower is None:
            return "Ingen fiducial follow kører."
        try:
            self._fiducial_follower.stop()
        except Exception as e:
            # Returnér en pæn fejl i stedet for 500
            return f"Fejl ved stop af fiducial: {e}"
        # Lad tråden selv rydde op i finally; nulstil alligevel referencen for sikkerhed
        self._fiducial_follower = None
        return "Fiducial follow stoppet."


    def get_battery_state(self):
        """Hent batteritilstand fra den rigtige Spot."""
        state_client: RobotStateClient = self.robot.ensure_client(RobotStateClient.default_service_name)
        state = state_client.get_robot_state()

        if not state.battery_states:
            return None

        battery = state.battery_states[0]  # Spot har kun ét batteri

        # Safely unwrap optional fields
        battery_percentage = battery.charge_percentage.value if battery.HasField("charge_percentage") else None
        voltage = battery.voltage.value if battery.HasField("voltage") else None
        current = battery.current.value if battery.HasField("current") else None
        temperatures = list(battery.temperatures) if battery.temperatures else []
        status = battery.status  # enum int;    

        return {
            "battery_percentage": battery_percentage,
            "voltage": voltage,
            "current": current,
            "temperatures": temperatures,
            "status": status,
        }

    # ---------------- CAMERA STREAM ----------------
    async def mjpeg_frames(self, camera: str = "frontleft_fisheye_image") -> AsyncIterator[bytes]:
        """
        Streamer rigtige kamera billeder fra Spot som MJPEG.
        camera: navnet på Spot's kamera source.
                Gyldige værdier:
                - "frontleft_fisheye_image"
                - "frontright_fisheye_image"
                - "left_fisheye_image"
                - "right_fisheye_image"
                - "back_fisheye_image"
        """
        while True:
            try:
                image_responses = self.image_client.get_image_from_sources([camera])
                img = image_responses[0]

                if img.shot.image.format == image_pb2.Image.FORMAT_JPEG:
                    yield img.shot.image.data
                else:
                    pil_img = Image.frombytes(
                        "RGB",
                        (img.shot.image.cols, img.shot.image.rows),
                        img.shot.image.data,
                    )
                    buf = io.BytesIO()
                    pil_img.save(buf, format="JPEG")
                    yield buf.getvalue()
            except Exception as e:
                print(f"[RealSpotClient] MJPEG frame error ({camera}):", e)

            await asyncio.sleep(1/15)  # ~15 fps




# ============================================================
__all__ = ["FakeSpotClient", "RealSpotClient"]
