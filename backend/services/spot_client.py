# backend/services/spot_client.py
from __future__ import annotations
from typing import AsyncIterator, Dict
import asyncio, io, os, time
import numpy as np
from PIL import Image
from .base import RobotClient

class FakeSpotClient(RobotClient):
    name = "spot-001"
    kind = "spot"
    display_name = "Spot (Demo)"

    def __init__(self, placeholder_path: str, w: int = 960, h: int = 540):
        self._w, self._h = w, h
        self._placeholder = placeholder_path

    async def mjpeg_frames(self) -> AsyncIterator[bytes]:
        # minimal: sort billede (du kan bruge din mp4->frames løsning i stedet)
        while True:
            arr = np.zeros((self._h, self._w, 3), dtype=np.uint8)
            img = Image.fromarray(arr, mode="RGB")
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=75)
            yield buf.getvalue()
            await asyncio.sleep(1/15)

    async def perception_stream(self) -> AsyncIterator[Dict]:
        t0 = time.time()
        while True:
            t = time.time() - t0
            x = int(100 + 200 * (0.5 + 0.5*np.sin(t)))
            yield {
                "ts": time.time(),
                "image_size": [self._w, self._h],
                "boxes": [{"id":"b1","label":"object","score":0.9,"xywh":[x,120,120,80]}],
            }
            await asyncio.sleep(0.06)
