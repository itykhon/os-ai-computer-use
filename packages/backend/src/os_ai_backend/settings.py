from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import logging


@dataclass
class RuntimeSettings:
    screenshot_enabled: bool = True
    screenshot_binary_mode: bool = False
    screenshot_quality: int = 50
    log_level: str = "INFO"


class SettingsManager:
    def __init__(self) -> None:
        self._s = RuntimeSettings()

    def update(self, **kwargs) -> RuntimeSettings:
        for k, v in kwargs.items():
            if hasattr(self._s, k):
                setattr(self._s, k, v)
        # apply log level
        try:
            logging.getLogger().setLevel(getattr(logging, self._s.log_level.upper(), logging.INFO))
        except Exception:
            pass
        return self._s

    def get(self) -> RuntimeSettings:
        return self._s


settings = SettingsManager()


