from __future__ import annotations

from typing import Callable, Dict, List, Any

from llm.types import ToolCall, ToolResult, TextPart, ImagePart


class ToolRegistry:
    def __init__(self) -> None:
        self._handlers: Dict[str, Callable[[Dict[str, Any]], List[Dict[str, Any]]]] = {}

    def register(self, name: str, handler: Callable[[Dict[str, Any]], List[Dict[str, Any]]]) -> None:
        self._handlers[name] = handler

    def execute(self, call: ToolCall) -> ToolResult:
        handler = self._handlers.get(call.name)
        if not handler:
            return ToolResult(
                tool_call_id=call.id,
                content=[TextPart(text=f"error: unknown tool '{call.name}'")],
                is_error=True,
            )

        # Our legacy handler returns Anthropic-style content blocks (dicts). Normalize to ContentPart.
        raw_blocks = handler(call.args)
        parts = []
        for b in raw_blocks or []:
            btype = b.get("type") if isinstance(b, dict) else None
            if btype == "text":
                parts.append(TextPart(text=str(b.get("text", ""))))
            elif btype == "image":
                src = (b.get("source") or {}) if isinstance(b.get("source"), dict) else {}
                media = str(src.get("media_type", "image/png"))
                data = str(src.get("data", ""))
                parts.append(ImagePart(media_type=media, data_base64=data))
            else:
                parts.append(TextPart(text=str(b)))

        return ToolResult(tool_call_id=call.id, content=parts, is_error=False)


