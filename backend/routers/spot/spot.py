# backend/routers/spot/spot.py
from __future__ import annotations
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from fastapi.concurrency import run_in_threadpool   # Importeret så vi kan køre blokkerende kode i en tråd

from ...services.spot_singleton import spot_client  # fælles client, Singleton :))

router = APIRouter()


@router.post("/demo/hello")
async def hello_demo():
    """Endpoint til 'Hello Spot' demo."""
    try:
        # kør hello_spot i baggrundstråd så det ikke blokerer video-streamen
        msg = await run_in_threadpool(spot_client.hello_spot)
        return {"status": "ok", "message": msg}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@router.post("/demo/lay")
async def lay_demo():
    """Endpoint til at lægge Spot ned (sit)."""
    try:
        msg = await run_in_threadpool(spot_client.lay_down)
        return {"status": "ok", "message": msg}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@router.post("/demo/poweroff")
async def poweroff_demo():
    """Endpoint til at slukke Spot (power off)."""
    try:
        msg = await run_in_threadpool(spot_client.power_off)
        return {"status": "ok", "message": msg}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@router.post("/demo/poweron")
async def poweron_demo():
    """Endpoint til at tænde Spot (power on)."""
    try:
        msg = await run_in_threadpool(spot_client.power_on)
        return {"status": "ok", "message": msg}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
