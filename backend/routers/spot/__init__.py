from fastapi import APIRouter
from . import spot, status, stream, perception, spot_battery, visualizer_runner

# Saml alle Spot-relaterede endpoints under ét prefix
router = APIRouter(prefix="/api/robots/spot-001", tags=["spot"])

router.include_router(spot.router)        # /demo/hello
router.include_router(status.router)      # /status
router.include_router(stream.router)      # /stream/...
router.include_router(perception.router)  # /perception/...
router.include_router(spot_battery.router)  # /battery
router.include_router(visualizer_runner.router)  # /launch-visualizer