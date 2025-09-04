# backend/routers/spot/spot_battery.py
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from bosdyn.client.robot_state import RobotStateClient
import traceback

from ...config import USE_FAKE_SPOT
from ...services.spot_singleton import spot_client

router = APIRouter()

@router.get("/battery")
async def get_battery():
    try:
        if USE_FAKE_SPOT:
            # Fake klient: returnér en dummy værdi
            return {
                "battery_percentage": 100.0,
                "voltage": 55.0,
                "current": 0.0,
                "temperature": 25.0,
            }

        # Hent robot state client
        state_client = spot_client.ensure_client(RobotStateClient.default_service_name)
        state = state_client.get_robot_state()

        if not state.battery_states:
            return JSONResponse(
                content={"error": "No battery state found"},
                status_code=404,
            )

        battery = state.battery_states[0]  # Spot har typisk kun ét batteri

        # Brug .value kun hvis feltet ikke er None
        return {
            "battery_percentage": battery.charge_percentage.value if battery.charge_percentage else None,
            "voltage": battery.voltage.value if battery.voltage else None,
            "current": battery.current.value if battery.current else None,
            "temperature": battery.temperature.value if battery.temperature else None,
        }

    except Exception as e:
        # Udskriv traceback i server-loggen for lettere debugging
        traceback.print_exc()
        return JSONResponse(content={"error": str(e)}, status_code=500)
