# backend/routers/spot/status.py

from fastapi import APIRouter
from fastapi.responses import JSONResponse
import subprocess
from ...config import SPOT_CONFIG

router = APIRouter()

@router.get("/status")
async def get_status():
    ip = SPOT_CONFIG["hostname"]
    try:
        result = subprocess.run(
            ["ping", "-c", "1", "-W", "1", ip],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        online = result.returncode == 0
        return {"online": online, "ip": ip}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
