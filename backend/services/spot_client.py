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

    def stand_up(self) -> str:
            """Få Spot til at stå op i normal position."""
            print("[RealSpotClient] Commanding Spot to stand up...")

            self.robot.power_on(timeout_sec=20)
            assert self.robot.is_powered_on(), "Spot kunne ikke starte"

            blocking_stand(self.command_client, timeout_sec=10)
            print("[RealSpotClient] Spot står nu op.")

            return "Spot står op nu."

    
    def fiducial_follow(self, distance_margin: float = 0.5, limit_speed: bool = True, avoid_obstacles: bool = False) -> str:
        """Start en fiducial follow demo i en separat tråd."""
        print("[RealSpotClient] Starter Fiducial Follow demo...")

        options = type("Options", (), {})()
        options.distance_margin = distance_margin
        options.limit_speed = limit_speed
        options.avoid_obstacles = avoid_obstacles
        options.use_world_objects = True  # eller False hvis du vil bruge apriltag lib

        follower = spot_fiducial.FollowFiducial(self.robot, options)

        # Start i en separat tråd, så webapp ikke blokeres
        def _run():
            try:
                follower.start()
            except Exception as e:
                print("[RealSpotClient] Fiducial follow fejlede:", e)

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

        return "Fiducial follow startet."

    def increase_height(self) -> str:
        """Få Spot til at hæve sin højde."""
        print("[RealSpotClient] Commanding Spot to increase height...")

        self.robot.power_on(timeout_sec=20)
        assert self.robot.is_powered_on(), "Spot kunne ikke starte"

        blocking_increase_height(self.command_client, timeout_sec=10)
        print("[RealSpotClient] Spot har hævet sin højde.")

        return "Spot har hævet sin højde."
    
    def set_body_height(self, height: float) -> str:
        """Sæt absolut krop-højde (mellem min_height og max_height)."""
        print(f"[RealSpotClient] Sætter body height til {height:.2f} m")

        self.robot.power_on(timeout_sec=10)
        assert self.robot.is_powered_on(), "Spot kunne ikke starte"

        # clamp højden så Spot ikke prøver noget farligt
        clamped = max(self.min_height, min(self.max_height, height))
        cmd = RobotCommandBuilder.synchro_stand_command(body_height=clamped)
        self.command_client.robot_command(cmd)

        self.current_height = clamped
        return f"Body height sat til {clamped:.2f} m."

    def increase_height(self) -> str:
        """Hæv robotten lidt (incrementel)."""
        new_height = self.current_height + self.height_step
        return self.set_body_height(new_height)

    def decrease_height(self) -> str:
        """Sænk robotten lidt (decrementel)."""
        new_height = self.current_height - self.height_step
        return self.set_body_height(new_height)
    
    def bodyroll(self) -> str:
        """Få Spot til at lave en lille 'body roll' (tilt fra side til side)."""
        print("[RealSpotClient] Starter body roll...")

        self.robot.power_on(timeout_sec=10)
        assert self.robot.is_powered_on(), "Spot kunne ikke starte"

        blocking_stand(self.command_client, timeout_sec=10)

        roll_angle = 0.3  # ca. 17 grader
        stand_right = RobotCommandBuilder.synchro_stand_command(body_roll=roll_angle)
        stand_left  = RobotCommandBuilder.synchro_stand_command(body_roll=-roll_angle)
        stand_neutral = RobotCommandBuilder.synchro_stand_command(body_roll=0.0)

        self.command_client.robot_command(stand_right)
        time.sleep(2)
        self.command_client.robot_command(stand_left)
        time.sleep(2)
        self.command_client.robot_command(stand_neutral)
        time.sleep(2)

        print("[RealSpotClient] Body roll færdig.")
        return "Spot har lavet en body roll."
    
    def snakehead(self) -> str:
        """Få Spot til at lave en 'snake head' bevægelse (drej hoved/krop fra side til side)."""
        print("[RealSpotClient] Starter snake head bevægelse...")

        self.robot.power_on(timeout_sec=10)
        assert self.robot.is_powered_on(), "Spot kunne ikke starte"

        # Sørg for at Spot står op
        from bosdyn.client.robot_command import blocking_stand
        blocking_stand(self.command_client, timeout_sec=10)

        # Vælg en yaw-vinkel (radianer). 0.3 rad ≈ 17 grader.
        yaw_angle = 0.3
        stand_left  = RobotCommandBuilder.synchro_stand_command(body_yaw=-yaw_angle)
        stand_right = RobotCommandBuilder.synchro_stand_command(body_yaw=+yaw_angle)
        stand_center = RobotCommandBuilder.synchro_stand_command(body_yaw=0.0)

        # Lav en lille “snake” bevægelse ved at skifte frem og tilbage
        for _ in range(2):
            self.command_client.robot_command(stand_left)
            time.sleep(1.5)
            self.command_client.robot_command(stand_right)
            time.sleep(1.5)

        # Tilbage til center
        self.command_client.robot_command(stand_center)
        time.sleep(2)

        print("[RealSpotClient] Snake head bevægelse færdig.")
        return "Spot har lavet en snake head bevægelse."
    
    def stop(self) -> str:
        """Stop alle bevægelser med det samme."""
        print("[RealSpotClient] Sender STOP kommando...")

        # Sørg for at robotten er tændt
        self.robot.power_on(timeout_sec=5)
        assert self.robot.is_powered_on(), "Spot kunne ikke starte"

        stop_cmd = RobotCommandBuilder.stop_command()
        self.command_client.robot_command(stop_cmd)
        print("[RealSpotClient] Spot er stoppet.")

        return "Spot er stoppet."
    


    def wiggle(self, cycles: int = 3, amplitude: float = 0.2, duration: float = 1.0) -> str:
        """Få Spot til at 'wiggle' ved at dreje kroppen side-til-side (yaw).
        cycles: antal gange den skal wiggle (frem+tilbage = 1 cycle).
        amplitude: hvor meget yaw i radianer (fx 0.2 ≈ 11 grader).
        duration: hvor længe hver bevægelse varer (sekunder).
        """
        print(f"[RealSpotClient] Starter wiggle (cycles={cycles}, amplitude={amplitude}, duration={duration})")

        # Sørg for at Spot er tændt og står op
        self.robot.power_on(timeout_sec=10)
        assert self.robot.is_powered_on(), "Spot kunne ikke starte"
        blocking_stand(self.command_client, timeout_sec=10)

        # Brug EulerZXY til yaw-rotation
        left_yaw  = RobotCommandBuilder.synchro_stand_command(
            footprint_R_body=RobotCommandBuilder.euler_zxy(yaw=-amplitude, roll=0.0, pitch=0.0),
            body_height=0.0
        )
        right_yaw = RobotCommandBuilder.synchro_stand_command(
            footprint_R_body=RobotCommandBuilder.euler_zxy(yaw=+amplitude, roll=0.0, pitch=0.0),
            body_height=0.0
        )
        center_yaw = RobotCommandBuilder.synchro_stand_command(
            footprint_R_body=RobotCommandBuilder.euler_zxy(yaw=0.0, roll=0.0, pitch=0.0),
            body_height=0.0
        )

        for i in range(cycles):
            print(f"[RealSpotClient] Wiggle cycle {i+1}/{cycles}: left")
            self.command_client.robot_command(left_yaw, end_time_secs=time.time() + duration)
            time.sleep(duration)

            print(f"[RealSpotClient] Wiggle cycle {i+1}/{cycles}: right")
            self.command_client.robot_command(right_yaw, end_time_secs=time.time() + duration)
            time.sleep(duration)

        # Tilbage til center
        self.command_client.robot_command(center_yaw, end_time_secs=time.time() + duration)
        time.sleep(duration)

        print("[RealSpotClient] Wiggle færdig.")
        return f"Spot har wigglet {cycles} gange."

    def selfright(self) -> str:
        print("[RealSpotClient] Commanding Spot to self-right...")

        self.robot.power_on(timeout_sec=10)
        assert self.robot.is_powered_on(), "Spot could not power on"

        cmd = RobotCommandBuilder.selfright_command()
        self.command_client.robot_command(cmd)

        return "Self-right command sent."
        
    
    def look_up(self, pitch: float = 0.3) -> str:
        """
        Få Spot til at kigge op ved at hæve kroppen (positiv pitch).
        Benytter footprint_R_body – ingen Joint Control-licens nødvendig.
        """
        try:
            cmd_client: RobotCommandClient = self.robot.ensure_client(RobotCommandClient.default_service_name)
            blocking_stand(cmd_client, timeout_sec=10)

            # Lav en EulerZXY rotation med pitch
            footprint_R_body = EulerZXY(yaw=0.0, roll=0.0, pitch=pitch)

            command = RobotCommandBuilder.synchro_stand_command(
                body_height=0.0,
                footprint_R_body=footprint_R_body
            )

            cmd_client.robot_command(command, end_time_secs=time.time() + 2.0)
            return f"Spot tilted body with pitch={pitch:.2f} rad (leaning up)."
        except Exception as e:
            return f"Failed to make Spot look up: {e}"

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
