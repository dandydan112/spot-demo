# backend/routers/robots.py
from __future__ import annotations
from fastapi import APIRouter
from typing import Dict, Any

router = APIRouter(prefix="/api/robots", tags=["robots"])

# “registry” TILFØJE ANDRE ROBOTTER SENERE
ROBOT_REGISTRY: Dict[str, Dict[str, Any]] = {
    "spot-001": {
        "id": "spot-001",
        "kind": "spot",
        "name": "Spot",
        "endpoints": {
            "mjpeg": "/api/robots/spot-001/stream/mjpeg",
            "perception": "/api/robots/spot-001/perception",
        },
        "status": "online",
        "thumbnail": "/static/img/thumbs/spotimg.png",
    }
}

@router.get("")
def list_robots():
    return {"robots": list(ROBOT_REGISTRY.values())}

@router.get("/{robot_id}")
def get_robot(robot_id: str):
    r = ROBOT_REGISTRY.get(robot_id)
    return r or {"error": "not_found"}
