# backend/routers/spot/visualizer_runner.py
import subprocess
import sys
from fastapi import APIRouter

router = APIRouter()

@router.post("/launch-visualizer")
async def launch_visualizer():
    try:
        python_bin = sys.executable
        print(f"[Visualizer Runner] Launching via {python_bin} -m backend.services.spot_visualizer")

        # Her sender vi output direkte til terminalen
        subprocess.Popen(
            [python_bin, "-m", "backend.services.spot_visualizer"]
        )

        return {"status": "ok", "message": "Visualizer started"}
    except Exception as e:
        print("[Visualizer Runner] ERROR:", e)
        return {"status": "error", "message": str(e)}
