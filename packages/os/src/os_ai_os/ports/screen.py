from __future__ import annotations

from typing import Protocol, Optional, Tuple, Any
from .types import Size, Rect


class Screen(Protocol):
    def size(self) -> Size: ...
    def screenshot(self, region: Optional[Tuple[int, int, int, int]] = None) -> Any: ...  # returns PIL.Image or ndarray


