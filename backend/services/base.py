# backend/services/base.py
from __future__ import annotations
from typing import AsyncIterator, Dict, Optional

class RobotClient:
    """Fælles interface for alle robottyper (Spot, MiR, UR, osv.)."""
    name: str
    kind: str  # fx "spot", "mir", "ur"
    display_name: str

    async def mjpeg_frames(self) -> AsyncIterator[bytes]:
        raise NotImplementedError

    async def perception_stream(self) -> AsyncIterator[Dict]:
        raise NotImplementedError
