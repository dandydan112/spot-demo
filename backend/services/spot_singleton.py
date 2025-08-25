# backend/services/spot_singleton.py
from .spot_client import RealSpotClient, FakeSpotClient
from ..config import USE_FAKE_SPOT, SPOT_CONFIG

if USE_FAKE_SPOT:
    spot_client = FakeSpotClient()
else:
    spot_client = RealSpotClient(
        hostname=SPOT_CONFIG["hostname"],
        username=SPOT_CONFIG["username"],
        password=SPOT_CONFIG["password"],
    )
