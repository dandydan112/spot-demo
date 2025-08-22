# backend/routers/spot/pointcloud.py
from fastapi import APIRouter, WebSocket
import asyncio, json, numpy as np
from bosdyn.client.image import ImageClient
from bosdyn.api import image_pb2

from ...services.spot_client import RealSpotClient, FakeSpotClient
from ...config import USE_FAKE_SPOT, SPOT_CONFIG

router = APIRouter()

# Init klient
if USE_FAKE_SPOT:
    spot_client = FakeSpotClient()
else:
    spot_client = RealSpotClient(
        hostname=SPOT_CONFIG["hostname"],
        username=SPOT_CONFIG["username"],
        password=SPOT_CONFIG["password"],
    )
    # 👉 Tilføj ImageClient til Spot
    spot_client.image_client = spot_client.robot.ensure_client(ImageClient.default_service_name)


@router.websocket("/api/robots/spot-001/pointcloud")
async def ws_pointcloud(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            if USE_FAKE_SPOT:
                # Fake data: lille sky i en kube
                points = np.random.rand(200, 3).tolist()
                await ws.send_text(json.dumps({"points": points}))
                await asyncio.sleep(0.5)
                continue

            # Request et depth image (fx fra Spot's front-left depth camera)
            img_responses = spot_client.image_client.get_image_from_sources(["frontleft_depth_in_visual_frame"])
            if not img_responses:
                await asyncio.sleep(0.2)
                continue

            img = img_responses[0]
            if img.shot.image.pixel_format != image_pb2.Image.PIXEL_FORMAT_DEPTH_U16:
                await asyncio.sleep(0.2)
                continue

            # Konverter depth image → numpy array
            w = img.shot.image.cols
            h = img.shot.image.rows
            depth_data = np.frombuffer(img.shot.image.data, dtype=np.uint16).reshape(h, w)

            # Lav punktsky (x,y,depth) – her bare simple koordinater
            ys, xs = np.meshgrid(np.arange(h), np.arange(w), indexing="ij")
            zs = depth_data.astype(np.float32) / 1000.0  # mm → meter

            # Stack til Nx3 punkter
            arr = np.stack((xs.flatten(), ys.flatten(), zs.flatten()), axis=-1)

            # Tag sample for performance
            sample = arr[::200]
            points = sample.tolist()

            await ws.send_text(json.dumps({"points": points}))
            await asyncio.sleep(0.3)  # ca. 3 Hz

    except Exception as e:
        print("PointCloud stream error:", e)
        await ws.close()
