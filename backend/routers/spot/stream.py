# backend/routers/spot/stream.py
from __future__ import annotations
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from ...services.spot_singleton import spot_client  # ← brug singleton!

router = APIRouter()

BOUNDARY = "frame"

@router.get("/stream/mjpeg")
async def stream_mjpeg():
    """Streamer MJPEG fra Spot (Real) eller FakeSpotClient."""
    async def gen():
        async for jpg in spot_client.mjpeg_frames():
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
