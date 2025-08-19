from __future__ import annotations
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse, JSONResponse
import subprocess

from ...services.spot_client import FakeSpotClient
from ...config import SPOT_CONFIG   # 👈 Hent konfig

router = APIRouter(prefix="/api/robots/spot-001", tags=["spot"])
client = FakeSpotClient(placeholder_path="frontend/placeholder.mp4")

BOUNDARY = "frame"


@router.websocket("/perception")
async def perception_ws(ws: WebSocket):
    await ws.accept()
    try:
        async for msg in client.perception_stream():
            await ws.send_json(msg)
    except WebSocketDisconnect:
        pass
