# backend/routers/spot/stream.py
from __future__ import annotations
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from ...services.spot_client import FakeSpotClient, RealSpotClient
from ...config import USE_FAKE_SPOT, SPOT_CONFIG

router = APIRouter()

# Vælg klient (FakeSpotClient vs RealSpotClient)
if USE_FAKE_SPOT:
    client = FakeSpotClient()
else:
    client = RealSpotClient(
        hostname=SPOT_CONFIG["hostname"],
        username=SPOT_CONFIG["username"],
        password=SPOT_CONFIG["password"],
    )

BOUNDARY = "frame"

@router.get("/stream/mjpeg")
async def stream_mjpeg():
    """Streamer MJPEG fra Spot eller FakeSpotClient."""
    async def gen():
        async for jpg in client.mjpeg_frames():
            yield (
                f"--{BOUNDARY}\r\n"
                "Content-Type: image/jpeg\r\n"
                f"Content-Length: {len(jpg)}\r\n\r\n"
            ).encode() + jpg + b"\r\n"

    headers = {"Cache-Control": "no-cache, no-store"}
    return StreamingResponse(
        gen(),
        media_type=f"multipart/x-mixed-replace; boundary={BOUNDARY}",
        headers=headers,
    )
