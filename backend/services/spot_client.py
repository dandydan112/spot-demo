# backend/services/spot_client.py
from __future__ import annotations
from typing import AsyncIterator, Dict
import asyncio, io, time
import numpy as np
from PIL import Image
import bosdyn.client
import bosdyn.client.util
from bosdyn.client.robot_command import RobotCommandClient, blocking_stand, RobotCommandBuilder
from bosdyn.client.lease import LeaseClient, LeaseKeepAlive
from bosdyn.client.image import ImageClient
from bosdyn.api import image_pb2
from bosdyn.api import robot_command_pb2  # Bruger den til rollover
from bosdyn.client.robot_command import RobotCommandBuilder # Rollover

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
            bosdyn.client.util.authenticate(self.robot)
            print("[RealSpotClient] Auth + Time Sync OK")

            # Clients
            self.command_client = self.robot.ensure_client(RobotCommandClient.default_service_name)
            self.lease_client   = self.robot.ensure_client(LeaseClient.default_service_name)
            self.image_client   = self.robot.ensure_client(ImageClient.default_service_name)

            # Lease: force-take hvis en anden session holder den
            self.lease_keepalive = LeaseKeepAlive(self.lease_client, return_at_exit=True)
            print("[RealSpotClient] Lease OK")

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

    # Nye funktioner, der kan tilføjes
    # def dance(self) -> str:
    #     print("[RealSpotClient] Får Spot til at danse...")
    #     self.command_client.robot_command(RobotCommandBuilder.dance_command())
    #     return "Spot danser nu."

    # ---------------- CAMERA STREAM ----------------
    async def mjpeg_frames(self) -> AsyncIterator[bytes]:
        """Streamer rigtige kamera billeder fra Spot som MJPEG."""
        while True:
            try:
                sources = ["frontleft_fisheye_image"]  # evt. prøv flere kilder
                image_responses = self.image_client.get_image_from_sources(sources)
                img = image_responses[0]

                if img.shot.image.format == image_pb2.Image.FORMAT_JPEG:
                    yield img.shot.image.data
                else:
                    pil_img = Image.frombytes(
                        "RGB", (img.shot.image.cols, img.shot.image.rows), img.shot.image.data
                    )
                    buf = io.BytesIO()
                    pil_img.save(buf, format="JPEG")
                    yield buf.getvalue()
            except Exception as e:
                print("MJPEG frame error:", e)

            await asyncio.sleep(1/15)  # ~15 fps



# ============================================================
__all__ = ["FakeSpotClient", "RealSpotClient"]
