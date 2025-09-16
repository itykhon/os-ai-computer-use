from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class BackendConfig:
    host: str = "127.0.0.1"
    port: int = 8765
    token: str | None = None
    allow_origins: tuple[str, ...] = ("http://localhost", "http://127.0.0.1")


def load_config() -> BackendConfig:
    host = os.getenv("OS_AI_BACKEND_HOST", "127.0.0.1")
    port_str = os.getenv("OS_AI_BACKEND_PORT", "8765")
    token = os.getenv("OS_AI_BACKEND_TOKEN")
    origins = os.getenv("OS_AI_BACKEND_CORS_ORIGINS", "http://localhost,http://127.0.0.1")
    try:
        port = int(port_str)
    except Exception:
        port = 8765
    allow_origins = tuple([o.strip() for o in origins.split(",") if o.strip()])
    return BackendConfig(host=host, port=port, token=token, allow_origins=allow_origins)


