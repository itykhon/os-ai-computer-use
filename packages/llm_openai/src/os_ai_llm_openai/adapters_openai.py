from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

# We avoid importing openai SDK now to not add dependency; this is a skeleton.

from config.settings import OPENAI_MODEL_NAME
from llm.interfaces import LLMClient
from llm.types import Message, ToolDescriptor, LLMResponse, ToolResult, Usage, TextPart, ImagePart, ToolCall


class OpenAIClient(LLMClient):
    """Skeleton adapter for OpenAI Computer Use API.

    Note: Implement actual SDK integration later.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None) -> None:
        key = api_key or os.environ.get("OPENAI_API_KEY")
        if not key:
            # Keep lazy; do not crash if not used
            self._api_key = None
        else:
            self._api_key = key
        self._model = model_name or OPENAI_MODEL_NAME

    def generate(
        self,
        messages: List[Message],
        tools: List[ToolDescriptor],
        system: Optional[str] = None,
        tool_choice: str = "auto",
        max_tokens: int = 1024,
        allow_parallel_tools: bool = True,
    ) -> LLMResponse:
        # Minimal stub to keep orchestration code working even without OpenAI SDK
        assistant = Message(role="assistant", content=[TextPart(text="OpenAI adapter not implemented yet.")])
        return LLMResponse(messages=[assistant], tool_calls=[], usage=Usage())

    def format_tool_result(self, result: ToolResult) -> Message:
        # For OpenAI, tool results are role="tool" with tool_call_id and content parts.
        # We encode them as text for now; real impl should map to SDK message format.
        txts = []
        for p in result.content:
            if isinstance(p, TextPart):
                txts.append(p.text)
            elif isinstance(p, ImagePart):
                txts.append(f"[image {p.media_type} {len(p.data_base64)}b]")
        return Message(role="tool", content=[TextPart(text=f"TOOL({result.tool_call_id}):\n" + "\n".join(txts))])


