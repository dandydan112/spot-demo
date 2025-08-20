# backend/services/spot_client.py
from __future__ import annotations
from typing import AsyncIterator, Dict
import asyncio, io, time
import numpy as np
from PIL import Image

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
import bosdyn.client
import bosdyn.client.util
from bosdyn.client.robot_command import RobotCommandClient, blocking_stand, RobotCommandBuilder
from bosdyn.client.lease import LeaseClient, LeaseKeepAlive


class RealSpotClient:
    name = "spot-001"
    kind = "spot"
    display_name = "Spot (Real)"

    def __init__(self, hostname: str, username: str, password: str):
        try:
            print(f"[RealSpotClient] Forbinder til Spot @ {hostname} som {username}")

            # Initialiser Spot SDK
            self.sdk = bosdyn.client.create_standard_sdk("spot-demo")
            self.robot = self.sdk.create_robot(hostname)

            # Login + time sync
            self.robot.authenticate(username, password)
            bosdyn.client.util.authenticate(self.robot)  # sikrer time sync m.m.
            print("[RealSpotClient] Auth + Time Sync OK")

            # Clients
            self.command_client = self.robot.ensure_client(RobotCommandClient.default_service_name)
            self.lease_client = self.robot.ensure_client(LeaseClient.default_service_name)

            # 👉 Hent en lease manuelt
            lease = self.lease_client.acquire()
            print("[RealSpotClient] Lease acquired:", lease)

            # Hold lease så længe vi kører
            self.lease_keepalive = LeaseKeepAlive(
                self.lease_client,
                lease=lease,
                return_at_exit=True,
            )
            print("[RealSpotClient] LeaseKeepAlive startet")

        except Exception as e:
            print(f"[RealSpotClient] FEJL under init: {e}")
            raise


    def hello_spot(self) -> str:
        """Få Spot til at stå op og lave et lille 'hej'-nik."""
        print("[RealSpotClient] Starter Hello Spot demo...")

        # Power on robot
        self.robot.power_on(timeout_sec=20)
        assert self.robot.is_powered_on(), "Spot kunne ikke starte"
        print("[RealSpotClient] Power ON OK")

        # Stå op
        blocking_stand(self.command_client, timeout_sec=10)
        print("[RealSpotClient] Spot står op")

        # Løft → vent → sænk
        cmd1 = RobotCommandBuilder.synchro_stand_command(body_height=0.1)
        self.command_client.robot_command(cmd1)
        print("[RealSpotClient] Løfter")
        time.sleep(2)

        cmd2 = RobotCommandBuilder.synchro_stand_command(body_height=-0.1)
        self.command_client.robot_command(cmd2)
        print("[RealSpotClient] Sænker")
        time.sleep(2)

        # Tilbage til normal stand
        cmd3 = RobotCommandBuilder.synchro_stand_command(body_height=0.0)
        self.command_client.robot_command(cmd3)
        print("[RealSpotClient] Tilbage til normal stand")

        return "Hello Spot demo udført!"


# ============================================================
# Eksporter kun de 2 clients
# ============================================================
__all__ = ["FakeSpotClient", "RealSpotClient"]
