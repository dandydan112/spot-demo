# backend/routers/spot/spot_battery.py
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from ...services.spot_singleton import spot_client

router = APIRouter()

@router.get("/battery")
async def get_battery():
    try:
        battery = spot_client.get_battery_state()
        if battery is None:
            return JSONResponse(
                content={"error": "No battery state found"},
                status_code=404,
            )
        return battery
    except Exception as e:
        return JSONResponse(
            content={"error": f"Battery fetch failed: {e}"},
            status_code=500,
        )
