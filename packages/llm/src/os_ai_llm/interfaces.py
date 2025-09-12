from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from .types import Message, ToolDescriptor, LLMResponse, ToolResult


class LLMClient(ABC):
    """Provider-agnostic LLM client interface."""

    @abstractmethod
    def generate(
        self,
        messages: List[Message],
        tools: List[ToolDescriptor],
        system: Optional[str] = None,
        tool_choice: str = "auto",
        max_tokens: int = 1024,
        allow_parallel_tools: bool = True,
    ) -> LLMResponse:
        """Produce an assistant response and optional tool calls."""

    @abstractmethod
    def format_tool_result(self, result: ToolResult) -> Message:
        """Format a provider-specific tool-result message to append to history."""


