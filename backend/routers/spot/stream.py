from __future__ import annotations
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse, JSONResponse
import subprocess

from ...services.spot_client import FakeSpotClient
from ...config import SPOT_CONFIG   # Hent konfig

router = APIRouter(prefix="/api/robots/spot-001", tags=["spot"])
client = FakeSpotClient(placeholder_path="frontend/placeholder.mp4")

BOUNDARY = "frame"



@router.get("/stream/mjpeg")
async def stream_mjpeg():
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