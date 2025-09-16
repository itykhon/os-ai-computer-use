import os
import time
from fastapi.testclient import TestClient
import pytest

from os_ai_backend.app import create_app
import os_ai_backend.files as fmod


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setenv("OS_AI_BACKEND_TOKEN", "secret")
    app = create_app()
    return TestClient(app)


def test_gc_enforces_total_size(client):
    # Set a small total-size limit
    fmod.store.max_total_bytes = 2000  # ~2KB
    fmod.store.max_file_bytes = 1024 * 10  # ensure single file doesn't trigger 413
    # Upload three ~1KB files; after GC total should be <= limit
    for i in range(3):
        data = (b"a" * 1024)
        r = client.post("/v1/files", headers={"Authorization": "Bearer secret"}, files={"file": (f"f{i}.bin", data, "application/octet-stream")})
        assert r.status_code == 200
    # Trigger a GC pass by calling get (opportunistic)
    # pick any known id by scanning store's index
    ids = list(fmod.store._index.keys())
    if ids:
        try:
            fmod.store.get(ids[0])
        except Exception:
            pass
    # Compute current total size
    total = 0
    for sf in list(fmod.store._index.values()):
        try:
            total += sf.path.stat().st_size
        except Exception:
            pass
    assert total <= fmod.store.max_total_bytes
