from __future__ import annotations

from typing import Optional

import injector

from config.settings import LLM_PROVIDER
from llm.interfaces import LLMClient
from llm.adapters_anthropic import AnthropicClient
from llm.adapters_openai import OpenAIClient
from tools.registry import ToolRegistry
from tools.computer import computer_tool_handler


class LLMModule(injector.Module):
    def __init__(self, provider: Optional[str] = None) -> None:
        self._provider = (provider or LLM_PROVIDER).lower()

    @injector.provider
    def provide_llm_client(self) -> LLMClient:  # type: ignore[override]
        if self._provider == "openai":
            return OpenAIClient()
        return AnthropicClient()


class ToolsModule(injector.Module):
    @injector.provider
    def provide_tool_registry(self) -> ToolRegistry:  # type: ignore[override]
        reg = ToolRegistry()
        reg.register("computer", computer_tool_handler)
        return reg


def create_container(provider: Optional[str] = None) -> injector.Injector:
    return injector.Injector([LLMModule(provider), ToolsModule()])


