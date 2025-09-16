import os
import json
import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from os_ai_backend.app import create_app
from os_ai_llm.interfaces import LLMClient
from os_ai_llm.types import LLMResponse, Message, TextPart, Usage
from os_ai_core.tools.registry import ToolRegistry


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setenv("OS_AI_BACKEND_TOKEN", "secret")

    class DummyLLM(LLMClient):  # type: ignore[abstract-method]
        def generate(self, *, messages, tools, system):  # type: ignore[override]
            return LLMResponse(messages=[Message(role="assistant", content=[TextPart(text="ok")])], tool_calls=[], usage=Usage())

        def format_tool_result(self, result):  # type: ignore[override]
            return Message(role="user", content=[TextPart(text="tool_result")])

    def fake_container(_provider=None):
        class _Inj:
            def get(self, cls):
                if cls.__name__ == "LLMClient":
                    return DummyLLM()
                if cls.__name__ == "ToolRegistry":
                    return ToolRegistry()
                raise KeyError(cls)
        return _Inj()

    # Patch DI to avoid real provider calls
    import os_ai_core.di as core_di
    import os_ai_backend.ws as backend_ws
    monkeypatch.setattr(core_di, "create_container", fake_container)
    monkeypatch.setattr(backend_ws, "create_container", fake_container)

    app = create_app()
    return TestClient(app)


def _recv_json(ws):
    raw = ws.receive_text()
    return json.loads(raw)


def test_ws_auth_required(client):
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws"):
            pass


def test_ws_flow_session_and_run(client):
    with client.websocket_connect("/ws?token=secret") as ws:
        ws.send_text(json.dumps({"jsonrpc": "2.0", "id": "1", "method": "session.create", "params": {"provider": "anthropic"}}))
        resp = _recv_json(ws)
        assert resp["id"] == "1"
        assert resp["result"]["sessionId"]

        ws.send_text(json.dumps({"jsonrpc": "2.0", "id": "2", "method": "agent.run", "params": {"task": "echo", "maxIterations": 1}}))
        r2 = _recv_json(ws)
        assert r2["id"] == "2"
        assert r2["result"]["jobId"]

        # We expect some event notifications, eventually final
        final = None
        for _ in range(50):
            ev = _recv_json(ws)
            if ev.get("method") == "event.final":
                final = ev
                break
        assert final is not None
        assert final["params"]["status"] in ("ok", "fail")


def test_rest_auth_and_files(client):
    # missing token
    r = client.post("/v1/files", files={"file": ("a.txt", b"hello", "text/plain")})
    assert r.status_code == 401

    r = client.post("/v1/files", headers={"Authorization": "Bearer secret"}, files={"file": ("a.txt", b"hello", "text/plain")})
    assert r.status_code == 200
    file_id = r.json()["fileId"]

    r2 = client.get(f"/v1/files/{file_id}", headers={"Authorization": "Bearer secret"})
    assert r2.status_code == 200
    assert r2.content == b"hello"
