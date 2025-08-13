# backend/app.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import uvicorn
import os

app = FastAPI()

# Sti til frontend
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")

# Forside
@app.get("/")
def root():
    return FileResponse(os.path.join(frontend_dir, "index.html"))

# Placeholder-video
@app.get("/placeholder.mp4")
def get_placeholder():
    return FileResponse(os.path.join(frontend_dir, "placeholder.mp4"))

# ---- Demo-stubs (gør intet lige nu) -----------------------------------------
@app.post("/demo/start")
def demo_start():
    # TODO: senere: lease, estop, kør sekvens
    return JSONResponse({"status": "not_implemented", "message": "Demo start stub"}, status_code=202)

@app.post("/demo/stop")
def demo_stop():
    # TODO: senere: safe stop/stand
    return JSONResponse({"status": "not_implemented", "message": "Demo stop stub"}, status_code=202)

# Statiske assets (CSS/JS)
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

if __name__ == "__main__":
    uvicorn.run("backend.app:app", host="0.0.0.0", port=8080, reload=True)
