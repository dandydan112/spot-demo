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
    

@router.post("/demo/rollover")
async def rollover_demo():
    """Endpoint til at rulle Spot over."""
    try:
        msg = await run_in_threadpool(spot_client.roll_over)
        return {"status": "ok", "message": msg}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@router.post("/demo/stand")
async def stand_demo():
    """Endpoint til at få Spot til at stå op."""
    try:
        msg = await run_in_threadpool(spot_client.stand_up)
        return {"status": "ok", "message": msg}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@router.post("/demo/fiducial")
async def fiducial_demo():
    """Endpoint til at få Spot til at følge et fiducial marker."""
    try:
        msg = await run_in_threadpool(spot_client.fiducial_follow)
        return {"status": "ok", "message": msg}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@router.post("/demo/increase_height")
async def increase_height_demo():
    """Endpoint til at få Spot til at hæve sin højde."""
    try:
        msg = await run_in_threadpool(spot_client.increase_height)
        return {"status": "ok", "message": msg}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@router.post("/demo/decrease_height")
async def decrease_height_demo():
    """Endpoint til at få Spot til at sænke sin højde."""
    try:
        msg = await run_in_threadpool(spot_client.decrease_height)
        return {"status": "ok", "message": msg}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@router.post("/demo/bodyroll")
async def bodyroll_demo():
    """Endpoint til at få Spot til at lave en bodyroll."""
    try:
        msg = await run_in_threadpool(spot_client.bodyroll)
        return {"status": "ok", "message": msg}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@router.post("/demo/snakehead")
async def snakehead_demo():
    """Endpoint til at få Spot til at lave en snakehead bevægelse."""
    try:
        msg = await run_in_threadpool(spot_client.snakehead)
        return {"status": "ok", "message": msg}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@router.post("/demo/stop")
async def stop_demo():
    """Endpoint til at få Spot til at stoppe."""
    try:
        msg = await run_in_threadpool(spot_client.stop)
        return {"status": "ok", "message": msg}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@router.post("/demo/estop")
async def estop_demo():
    """Endpoint til at få Spot til at gå i nødstop."""
    try:
        msg = await run_in_threadpool(spot_client.estop)
        return {"status": "ok", "message": msg}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@router.post("/demo/wiggle")
async def wiggle_demo():
    """Endpoint til at få Spot til at wiggle."""
    try:
        msg = await run_in_threadpool(spot_client.wiggle)
        return {"status": "ok", "message": msg}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
    
@router.post("/demo/selfright")
async def selfright_demo():
    """Endpoint til at få Spot til at self-right."""
    try:
        msg = await run_in_threadpool(spot_client.selfright)
        return {"status": "ok", "message": msg}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
    
@router.post("/demo/lookup")
async def lookup_demo():
    """Endpoint til at få Spot til at kigge op."""
    try:
        msg = await run_in_threadpool(spot_client.look_up)
        return {"status": "ok", "message": msg}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)