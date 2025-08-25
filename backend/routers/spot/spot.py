# backend/routers/spot/spot.py
from __future__ import annotations
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ...services.spot_singleton import spot_client  # ← fælles client

router = APIRouter()


@router.post("/demo/hello")
async def hello_demo():
    """Endpoint til 'Hello Spot' demo."""
    try:
        msg = spot_client.hello_spot()
        return {"status": "ok", "message": msg}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@router.post("/demo/lay")
async def lay_demo():
    """Endpoint til at lægge Spot ned (sit)."""
    try:
        msg = spot_client.lay_down()
        return {"status": "ok", "message": msg}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@router.post("/demo/poweroff")
async def poweroff_demo():
    """Endpoint til at slukke Spot (power off)."""
    try:
        msg = spot_client.power_off()
        return {"status": "ok", "message": msg}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
