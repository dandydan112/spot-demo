# backend/routers/spot/stream.py
from __future__ import annotations
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from ...services.spot_singleton import spot_client  # Bruger singleton :)

router = APIRouter()

BOUNDARY = "frame"

def make_stream_response(camera: str):
    async def gen():
        async for jpg in spot_client.mjpeg_frames(camera=camera):
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

@router.get("/stream/frontleft")
async def stream_frontleft():
    return make_stream_response("frontleft_fisheye_image")

@router.get("/stream/frontright")
async def stream_frontright():
    return make_stream_response("frontright_fisheye_image")

@router.get("/stream/left")
async def stream_left():
    return make_stream_response("left_fisheye_image")

@router.get("/stream/right")
async def stream_right():
    return make_stream_response("right_fisheye_image")

@router.get("/stream/back")
async def stream_back():
    return make_stream_response("back_fisheye_image")
