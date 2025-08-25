# backend/routers/spot/visualizer.py
from fastapi import APIRouter, WebSocket
import asyncio, json, numpy as np
from bosdyn.api import image_pb2

from ...services.spot_singleton import spot_client  # ← BRUG singleton

router = APIRouter()


@router.websocket("/api/robots/spot-001/visualizer")
async def ws_visualizer(ws: WebSocket):
    """Stream en forsimplet 3D point cloud baseret på depth image fra Spot."""
    await ws.accept()
    try:
        while True:
            if spot_client.kind == "spot" and spot_client.display_name == "Spot (Demo)":
                # Fake tilfældige punkter (til test uden robot)
                points = np.random.rand(500, 3).tolist()
                await ws.send_text(json.dumps({"points": points}))
                await asyncio.sleep(0.5)
                continue

            try:
                # Brug et depth-kamera (f.eks. venstre front)
                img_responses = spot_client.image_client.get_image_from_sources(
                    ["frontleft_depth_in_visual_frame"]
                )
                if not img_responses:
                    await asyncio.sleep(0.2)
                    continue

                img = img_responses[0]
                if img.shot.image.pixel_format != image_pb2.Image.PIXEL_FORMAT_DEPTH_U16:
                    await asyncio.sleep(0.2)
                    continue

                w, h = img.shot.image.cols, img.shot.image.rows
                depth = np.frombuffer(img.shot.image.data, dtype=np.uint16).reshape(h, w)

                # Normaliser og nedprøv
                xs, ys = np.meshgrid(np.arange(w), np.arange(h))
                zs = depth.astype(np.float32) / 1000.0  # mm → meter

                arr = np.stack((xs.flatten(), ys.flatten(), zs.flatten()), axis=-1)
                sample = arr[::500]  # reducer datamængde
                points = sample.tolist()

                await ws.send_text(json.dumps({"points": points}))
            except Exception as inner_e:
                print("Depth stream error:", inner_e)

            await asyncio.sleep(0.3)  # ~3 Hz
    except Exception as e:
        print("Visualizer error:", e)
        await ws.close()
