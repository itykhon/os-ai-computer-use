from __future__ import annotations

from llm.adapters_anthropic import AnthropicClient
from llm.types import Message, TextPart, ToolDescriptor
import os
import pytest


class DummyAnthropic:
    class Beta:
        class Messages:
            def create(self, **kwargs):
                # Validate messages shape: first message must have non-empty content
                msgs = kwargs.get("messages", [])
                assert isinstance(msgs, list) and msgs, "messages should not be empty"
                first = msgs[0]
                assert first.get("role") == "user"
                assert first.get("content"), "first message content must be non-empty"

                class Resp:
                    def __init__(self):
                        self.content = []
                        class Usage:
                            input_tokens = 1
                            output_tokens = 1
                        self.usage = Usage()
                return Resp()
        def __init__(self):
            self.messages = DummyAnthropic.Beta.Messages()
    def __init__(self, **kwargs):
        self.beta = DummyAnthropic.Beta()


def test_anthropic_adapter_builds_valid_messages(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    # Monkeypatch anthropic class to our dummy
    import llm.adapters_anthropic as aa
    aa.anthropic.Anthropic = DummyAnthropic  # type: ignore

    client = AnthropicClient()
    resp = client.generate(
        messages=[Message(role="user", content=[TextPart(text="hi")])],
        tools=[ToolDescriptor(name="computer", kind="computer_use", params={"display_width_px": 10, "display_height_px": 10})],
        system=None,
        max_tokens=50,
    )
    assert resp.usage.input_tokens == 1

