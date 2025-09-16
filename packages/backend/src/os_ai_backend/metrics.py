from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict
import threading


@dataclass
class MetricsState:
    ws_connections: int = 0
    sessions_created: int = 0
    jobs_started: int = 0
    jobs_completed: int = 0
    jobs_failed: int = 0
    jobs_cancelled: int = 0


class Metrics:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._state = MetricsState()

    def inc(self, field: str, delta: int = 1) -> None:
        with self._lock:
            v = getattr(self._state, field, 0)
            setattr(self._state, field, v + delta)

    def snapshot(self) -> Dict[str, int]:
        with self._lock:
            return asdict(self._state)  # type: ignore[return-value]


metrics = Metrics()


