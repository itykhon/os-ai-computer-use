from __future__ import annotations

from os_ai_core.tools.registry import ToolRegistry


def test_tools_registry_normalizes_text_and_image_blocks():
    reg = ToolRegistry()

    def handler(args):
        return [
            {"type": "text", "text": "hello"},
            {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "abc"}},
        ]

    reg.register("computer", handler)

    call = type("Call", (), {"id": "1", "name": "computer", "args": {}})()  # simple stub
    res = reg.execute(call)

    assert res.tool_call_id == "1"
    assert len(res.content) == 2

