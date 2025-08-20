from __future__ import annotations
import asyncio
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ...config import USE_FAKE_SPOT, SPOT_CONFIG
from ...services.spot_client import FakeSpotClient, RealSpotClient

router = APIRouter()

# Vælg hvilken klient vi bruger
if USE_FAKE_SPOT:
    spot_client = FakeSpotClient()
else:
    spot_client = RealSpotClient(
        hostname=SPOT_CONFIG["hostname"],
        username=SPOT_CONFIG["username"],
        password=SPOT_CONFIG["password"],
    )

@router.post("/demo/hello")
async def hello_demo():
    """
    Endpoint til 'Hello Spot' demo.
    """
    try:
        if USE_FAKE_SPOT:
            await asyncio.sleep(1)
            return {"status": "ok", "message": "Hello Spot demo (fake)"}
        else:
            msg = spot_client.hello_spot()
            return {"status": "ok", "message": msg}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
