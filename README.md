#  Spot Demo Webapp

A lightweight web application for controlling and monitoring the **Boston Dynamics Spot** robot using **FastAPI**.  
The app provides a browser interface for sending commands, viewing live camera feeds, and checking Spot’s status in real time.

---

## Introduction

The Spot Demo Webapp allows you to:
- Send motion commands (stand, sit, power on/off, move, etc.)
- Stream live camera feeds (MJPEG)
- View robot state (battery, faults, connection)
- Switch between **RealSpotClient** and **FakeSpotClient** for testing without hardware

---

## Setup (Linux)

### 1. Clone the repository
```bash
git clone https://github.com/dandydan112/spot-demo.git
cd spot-demo
```

### 2. Create and activate a virtual environment
```bash
sudo apt install python3.10-venv
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
Install `requirements.txt` file:
```bash
pip install -r requirements.txt
```

### 4. Create Config file
Create Config file in backend/config.py
Paste:
```bash
# backend/config.py

# Brug FakeSpotClient til test uden robot
USE_FAKE_SPOT = False

SPOT_CONFIG = {
    "hostname": "Fill robot ip adress",   
    "username": "fill robot username",         
    "password": "fill robot password",  
}
```


## Running the Server

Start the FastAPI server with:
```bash
python3 -m uvicorn backend.app:app --reload --host 0.0.0.0 --port 8080
```

Then open your browser at:
```bash
http://localhost:8080
```

##  Dependencies

```bash
| Package | Description |
|----------|-------------|
| `fastapi` | Web framework for backend API |
| `uvicorn[standard]` | ASGI server for FastAPI with extra features |
| `requests` | HTTP communication with Spot |
| `jinja2` | HTML templating |
| `python-multipart` | Form data handling |
| `pydantic` | Data validation |
| `numpy` | Array and math operations |
| `opencv-python` | For MJPEG streaming or image processing |
| `Pillow` | Image processing |
| `bosdyn-client >= 3.1` | Boston Dynamics Spot SDK client |
| `spot-sdk` | If you use additional Spot SDK utilities |

```


## To Do

- Make embedded version of the "3D Visualizer"
- Stitch front fisheye cameras together

