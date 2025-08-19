# backend/routers/spot.py
from __future__ import annotations
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse, JSONResponse
import subprocess

from ...services.spot_client import FakeSpotClient
from ...config import SPOT_CONFIG   # 👈 Hent konfig

router = APIRouter(prefix="/api/robots/spot-001", tags=["spot"])
client = FakeSpotClient(placeholder_path="frontend/placeholder.mp4")

BOUNDARY = "frame"


# @router.get("/status")
# async def get_status():
#     try:
#         ip = SPOT_CONFIG["hostname"]

#         # -c 1 = send 1 ping, -W 1 = timeout 1 sekund
#         result = subprocess.run(
#             ["ping", "-c", "1", "-W", "1", ip],
#             stdout=subprocess.DEVNULL,
#             stderr=subprocess.DEVNULL,
#         )
#         online = result.returncode == 0
#         return {"online": online, "ip": ip}
#     except Exception as e:
#         return JSONResponse(content={"error": str(e)}, status_code=500)


# @router.get("/stream/mjpeg")
# async def stream_mjpeg():
#     async def gen():
#         async for jpg in client.mjpeg_frames():
#             yield (
#                 f"--{BOUNDARY}\r\n"
#                 "Content-Type: image/jpeg\r\n"
#                 f"Content-Length: {len(jpg)}\r\n\r\n"
#             ).encode() + jpg + b"\r\n"

#     headers = {"Cache-Control": "no-cache, no-store"}
#     return StreamingResponse(
#         gen(),
#         media_type=f"multipart/x-mixed-replace; boundary={BOUNDARY}",
#         headers=headers,
#     )


# @router.websocket("/perception")
# async def perception_ws(ws: WebSocket):
#     await ws.accept()
#     try:
#         async for msg in client.perception_stream():
#             await ws.send_json(msg)
#     except WebSocketDisconnect:
#         pass
