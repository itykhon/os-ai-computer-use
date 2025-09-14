from __future__ import annotations

from typing import Optional
from .platform.drivers import PlatformDrivers
from .platform.factory import build_platform

_drivers: Optional[PlatformDrivers] = None


def get_drivers() -> PlatformDrivers:
    global _drivers
    if _drivers is None:
        _drivers = build_platform()
    return _drivers


