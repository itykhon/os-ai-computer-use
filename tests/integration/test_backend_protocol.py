import json
import pytest
from fastapi.testclient import TestClient

from os_ai_backend.app import create_app


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setenv("OS_AI_BACKEND_TOKEN", "secret")
    app = create_app()
    return TestClient(app)


def test_parse_error(client):
    with client.websocket_connect("/ws?token=secret") as ws:
        ws.send_text("{not a json}")
        msg = json.loads(ws.receive_text())
        assert msg["error"]["code"] == -32700


def test_invalid_request(client):
    with client.websocket_connect("/ws?token=secret") as ws:
        ws.send_text(json.dumps([1,2,3]))
        msg = json.loads(ws.receive_text())
        assert msg["error"]["code"] == -32600


def test_unknown_method(client):
    with client.websocket_connect("/ws?token=secret") as ws:
        ws.send_text(json.dumps({"jsonrpc": "2.0", "id": "x", "method": "no.such", "params": {}}))
        msg = json.loads(ws.receive_text())
        assert msg["error"]["code"] == -32601


def test_missing_params(client):
    with client.websocket_connect("/ws?token=secret") as ws:
        ws.send_text(json.dumps({"jsonrpc": "2.0", "id": "x", "method": "agent.run", "params": {}}))
        msg = json.loads(ws.receive_text())
        assert msg["error"]["code"] == -32602
