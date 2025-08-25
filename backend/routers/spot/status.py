# backend/routers/spot/status.py
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from ...config import USE_FAKE_SPOT, SPOT_CONFIG
from ...services.spot_singleton import spot_client

router = APIRouter()

@router.get("/status")
async def get_status():
    try:
        if USE_FAKE_SPOT:
            # Fake client: altid online
            return {"online": True, "ip": "fake"}
        else:
            # RealSpotClient: check via robot objektet
            ip = SPOT_CONFIG["hostname"]
            online = spot_client.robot.is_estopped() is not None  # simpel sanity-check
            return {"online": True, "ip": ip}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
