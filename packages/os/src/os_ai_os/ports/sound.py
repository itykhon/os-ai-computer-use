from __future__ import annotations

from typing import Protocol


class Sound(Protocol):
    def play_click(self) -> None: ...
    def play_done(self) -> None: ...


