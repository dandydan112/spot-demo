# backend/routers/spot/perception.py
from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from ...services.spot_singleton import spot_client  

router = APIRouter(prefix="/api/robots/spot-001", tags=["spot"])


@router.websocket("/perception")
async def perception_ws(ws: WebSocket):
    await ws.accept()
    try:
        async for msg in spot_client.perception_stream():
            await ws.send_json(msg)
    except WebSocketDisconnect:
        pass
