# spot-demo

python3 -m uvicorn backend.app:app --reload --host 0.0.0.0 --port 8080

# 🐾 Spot Demo Webapp

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
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
If you have a `requirements.txt` file:
```bash
pip install -r requirements.txt
```

```

---

## ⚙️ Running the Server

Start the FastAPI server with:
```bash
python3 -m uvicorn backend.app:app --reload --host 0.0.0.0 --port 8080

Then open your browser at:
```
http://localhost:8080
```



---

##  Dependencies

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
| *(optional)* `spot-sdk` | If you use additional Spot SDK utilities |

---



