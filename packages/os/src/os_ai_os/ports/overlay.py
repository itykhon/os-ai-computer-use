from __future__ import annotations

from typing import Protocol, Optional


class Overlay(Protocol):
    def highlight(self, x: int, y: int, *, radius: Optional[int] = None, duration: Optional[float] = None) -> None: ...
    def process_events(self) -> None: ...


