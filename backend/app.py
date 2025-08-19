# backend/app.py
from __future__ import annotations
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from .routers import robots as robots_router
from .routers.spot import spot as spot_router

app = FastAPI(title="Robot Hub")

# Frontend sti
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/static", StaticFiles(directory=os.path.join(frontend_dir, "static")), name="static")

@app.get("/")
def root():
    return FileResponse(os.path.join(frontend_dir, "index.html"))

@app.get("/robot")
def robot_page():
    # generisk robotside (frontend/robot.html) – ?id=spot-001
    return FileResponse(os.path.join(frontend_dir, "robot.html"))

# API routers
app.include_router(robots_router.router)
app.include_router(spot_router.router)
