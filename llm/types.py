from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Literal


# Basic content parts
ContentType = Literal["text", "image"]


@dataclass
class TextPart:
    type: Literal["text"] = "text"
    text: str = ""


@dataclass
class ImagePart:
    type: Literal["image"] = "image"
    media_type: str = "image/png"
    data_base64: str = ""  # base64-encoded image data


ContentPart = TextPart | ImagePart


@dataclass
class Message:
    role: Literal["system", "user", "assistant", "tool"]
    content: List[ContentPart]


@dataclass
class ToolDescriptor:
    name: str
    kind: Literal["computer_use", "function"]
    # Free-form provider-agnostic parameters
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolCall:
    id: str
    name: str
    args: Dict[str, Any]


@dataclass
class ToolResult:
    tool_call_id: str
    content: List[ContentPart]
    is_error: bool = False


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    provider_raw: Any = None


@dataclass
class LLMResponse:
    messages: List[Message]  # usually a single assistant message
    tool_calls: List[ToolCall]
    usage: Usage


