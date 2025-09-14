from __future__ import annotations

import importlib
import platform
from typing import Optional

from .drivers import PlatformDrivers


def _load_entry_point(ep_group: str, name: str):
    try:
        import importlib.metadata as md  # Python 3.8+
    except Exception:
        import importlib_metadata as md  # type: ignore
    for ep in md.entry_points(group=ep_group):  # type: ignore
        if ep.name == name:
            return ep.load()
    return None


def build_platform(explicit: Optional[str] = None) -> PlatformDrivers:
    sysname = (explicit or platform.system()).lower()
    if sysname == "darwin":
        factory = _load_entry_point("os_ai_os.drivers", "darwin")
        if factory is None:
            # direct import fallback
            try:
                mod = importlib.import_module("os_ai_os_macos.drivers")
                factory = getattr(mod, "make_drivers", None)
            except Exception:
                factory = None
        if factory is None:
            raise RuntimeError("macOS drivers not installed: install os_ai_os_macos package")
        return factory()
    if sysname == "windows":
        factory = _load_entry_point("os_ai_os.drivers", "windows")
        if factory is None:
            try:
                mod = importlib.import_module("os_ai_os_windows.drivers")
                factory = getattr(mod, "make_drivers", None)
            except Exception:
                factory = None
        if factory is None:
            raise RuntimeError("Windows drivers not installed: install os_ai_os_windows package")
        return factory()
    raise RuntimeError(f"Unsupported platform: {sysname}")


