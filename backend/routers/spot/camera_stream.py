# backend/routers/spot/camera_stream.py
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import asyncio
import cv2
import numpy as np
from bosdyn.client.image import ImageClient
from bosdyn.api import image_pb2
from ...services.spot_singleton import spot_client

router = APIRouter()

def _decode_image(image_response):
    """Decode Spot ImageResponse into an OpenCV BGR image (handles JPEG or raw)."""
    img_data = np.frombuffer(image_response.shot.image.data, dtype=np.uint8)
    fmt = image_response.shot.image.format

    if fmt == 1 or fmt == image_pb2.Image.PIXEL_FORMAT_JPEG:
        # Decode JPEG bytes directly
        img = cv2.imdecode(img_data, cv2.IMREAD_COLOR)

    elif fmt == image_pb2.Image.PIXEL_FORMAT_RGB_U8:
        img = img_data.reshape((image_response.shot.image.rows,
                                image_response.shot.image.cols, 3))
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    elif fmt == image_pb2.Image.PIXEL_FORMAT_GREYSCALE_U8:
        img = img_data.reshape((image_response.shot.image.rows,
                                image_response.shot.image.cols))

    else:
        raise ValueError(f"Unsupported image format: {fmt}")

    return img





def _stitch_images(img_left, img_right):
    """Try to stitch two images into a panorama, fallback to side-by-side concat."""
    stitcher = cv2.Stitcher_create(cv2.Stitcher_PANORAMA)
    status, stitched = stitcher.stitch([img_left, img_right])
    if status == cv2.Stitcher_OK:
        return stitched
    else:
        print(f"[Stitcher] Failed with status {status}, fallback to concat")
        # fallback to simple horizontal concat (resize if needed)
        h = min(img_left.shape[0], img_right.shape[0])
        left_resized = cv2.resize(img_left, (int(img_left.shape[1] * h / img_left.shape[0]), h))
        right_resized = cv2.resize(img_right, (int(img_right.shape[1] * h / img_right.shape[0]), h))
        return cv2.hconcat([left_resized, right_resized])

def _encode_frame(frame):
    ok, buf = cv2.imencode(".jpg", frame)
    if not ok:
        return None
    return buf.tobytes()

async def _mjpeg_generator(image_client: ImageClient):
    while True:
        try:
            responses = image_client.get_image_from_sources(
                ["frontleft_fisheye_image", "frontright_fisheye_image"]
            )

            # Debug: log hvilke kilder og formater vi får
            print("Got sources:", [r.source.name for r in responses])
            print("Formats:", [r.shot.image.format for r in responses])
            print("Sizes:", [(r.shot.image.rows, r.shot.image.cols, len(r.shot.image.data)) for r in responses])

            if len(responses) != 2:
                print(f"[Stream] Expected 2 responses, got {len(responses)}")
                await asyncio.sleep(0.1)
                continue

            left_resp, right_resp = responses
            img_left = _decode_image(left_resp)
            img_right = _decode_image(right_resp)

            # Sørg for at begge er i landscape (bredde > højde)
            if img_left.shape[0] > img_left.shape[1]:
                img_left = cv2.rotate(img_left, cv2.ROTATE_90_CLOCKWISE)

            if img_right.shape[0] > img_right.shape[1]:
                img_right = cv2.rotate(img_right, cv2.ROTATE_90_CLOCKWISE)

            # Forsøg at sy sammen, fallback til side-by-side
            stitched = _stitch_images(img_left, img_right)

            cv2.imwrite("/tmp/stitched_debug.jpg", stitched)

            frame_bytes = _encode_frame(stitched)
            if frame_bytes is None:
                continue

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
            )

            await asyncio.sleep(0.05)  # ~20 FPS

        except Exception as e:
            print(f"[Stream error] {e}")
            await asyncio.sleep(0.5)



@router.get("/camera/front/stitched/stream")
async def stream_stitched_cameras():
    """Stream stitched front left + front right fisheye cameras as MJPEG."""
    image_client = spot_client.image_client   # brug den direkte
    return StreamingResponse(
        _mjpeg_generator(image_client),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )

