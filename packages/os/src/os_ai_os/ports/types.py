from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Point:
    x: int
    y: int


@dataclass(frozen=True)
class Size:
    width: int
    height: int


@dataclass(frozen=True)
class Rect:
    x: int
    y: int
    width: int
    height: int


@dataclass(frozen=True)
class Capabilities:
    supports_synthetic_input: bool = True
    supports_click_through_overlay: bool = True
    supports_smooth_move: bool = True
    dpi_scale: float = 1.0
    screen_recording_available: bool = True


