from __future__ import annotations

from typing import List, Optional, Callable, Dict, Any
import logging, json, sys
import httpx
import anthropic

from os_ai_llm.interfaces import LLMClient
from os_ai_llm.types import Message, ToolDescriptor, TextPart, ToolCall, ToolResult, ImagePart
from os_ai_core.utils.costs import estimate_cost
from os_ai_core.config import USAGE_LOG_EACH_ITERATION, LOGGER_NAME
from os_ai_llm_anthropic.config import MODEL_NAME
from os_ai_core.tools.registry import ToolRegistry


class CancelToken:
    def __init__(self) -> None:
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    @property
    def is_cancelled(self) -> bool:
        return self._cancelled


class Orchestrator:
    def __init__(self, client: LLMClient, tool_registry: ToolRegistry) -> None:
        self._client = client
        self._tools = tool_registry
        # Cumulative usage per run; reset at run() start
        self.total_input_tokens: int = 0
        self.total_output_tokens: int = 0

    def run(
        self,
        task: str,
        tool_descriptors: List[ToolDescriptor],
        system: Optional[str],
        max_iterations: int = 30,
        *,
        cancel_token: Optional[CancelToken] = None,
        on_event: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    ) -> List[Message]:
        messages: List[Message] = [Message(role="user", content=[TextPart(text=task)])]
        logger = logging.getLogger(LOGGER_NAME)
        # reset cumulative usage at start
        try:
            self.total_input_tokens = 0
            self.total_output_tokens = 0
        except Exception:
            pass
        for iter_idx in range(max_iterations):
            if cancel_token is not None and cancel_token.is_cancelled:
                if on_event is not None:
                    try:
                        on_event("progress", {"stage": "cancelled", "iteration": iter_idx})
                    except Exception:
                        pass
                break
            if on_event is not None:
                try:
                    on_event("progress", {"stage": "iteration_start", "iteration": iter_idx})
                except Exception:
                    pass
            try:
                resp = self._client.generate(messages=messages, tools=tool_descriptors, system=system)
            except anthropic.RateLimitError as e:  # type: ignore
                try:
                    body = getattr(e, "response", None)
                    if body is not None:
                        try:
                            payload = e.response.json()
                        except Exception:
                            payload = e.response.text
                        logger.error(f"HTTP 429 Rate Limit from Anthropic: {payload}")
                    else:
                        logger.error(f"HTTP 429 Rate Limit from Anthropic: {e}")
                except Exception:
                    logger.error("HTTP 429 Rate Limit from Anthropic")
                break
            except httpx.HTTPStatusError as e:
                try:
                    status = getattr(e.response, "status_code", None)
                    try:
                        payload = e.response.json()
                    except Exception:
                        payload = e.response.text
                    logger.error(f"HTTP {status} from provider: {payload}")
                except Exception:
                    logger.error("HTTP error from provider")
                break
            except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.WriteTimeout) as e:
                logger.error(f"HTTP timeout from provider: {e}")
                break
            except Exception as e:
                logger.error(f"Provider error: {e}")
                break

            # Print assistant texts immediately (stream-like)
            try:
                for m in resp.messages or []:
                    if getattr(m, "role", None) == "assistant":
                        for p in (getattr(m, "content", []) or []):
                            try:
                                if getattr(p, "type", None) == "text":
                                    txt = str(getattr(p, "text", "")).strip()
                                    if txt:
                                        logger.info('🧠 %s', txt)
                                        if on_event is not None:
                                            try:
                                                on_event("assistant_text", {"text": txt})
                                            except Exception:
                                                pass
                            except Exception:
                                pass
            except Exception:
                pass
            # Optional usage/cost logging similar to legacy
            try:
                inp = int(getattr(resp.usage, "input_tokens", 0) or 0)
                out = int(getattr(resp.usage, "output_tokens", 0) or 0)
                try:
                    self.total_input_tokens += inp
                    self.total_output_tokens += out
                except Exception:
                    pass
                if USAGE_LOG_EACH_ITERATION:
                    _in_cost, _out_cost, _total, _tier = estimate_cost(MODEL_NAME, inp, out)
                    logger.info("📈 Usage iter in=%s out=%s cost=$%.6f (input=$%.6f, output=$%.6f)", inp, out, (_in_cost + _out_cost), _in_cost, _out_cost)
            except Exception:
                pass

            # Append assistant message
            if resp.messages:
                messages.extend(resp.messages)

            if not resp.tool_calls:
                break

            # Execute tool calls sequentially (parallel later if needed)
            for call in resp.tool_calls:
                if cancel_token is not None and cancel_token.is_cancelled:
                    break
                # Notify start of tool call
                if on_event is not None:
                    try:
                        on_event("tool_call", {"name": call.name, "args": call.args})
                    except Exception:
                        pass
                result = self._tools.execute(call)
                # Emit result events
                if on_event is not None:
                    try:
                        # Summarize result
                        has_image = any(isinstance(p, ImagePart) for p in result.content)
                        if has_image:
                            for p in result.content:
                                if isinstance(p, ImagePart):
                                    on_event("tool_result_image", {"media_type": p.media_type, "data": p.data_base64})
                        else:
                            # send first text if present
                            for p in result.content:
                                if getattr(p, "type", None) == "text" or type(p).__name__ == "TextPart":
                                    on_event("tool_result_text", {"text": getattr(p, "text", "")})
                                    break
                    except Exception:
                        pass
                # Append tool_result immediately after the assistant tool_use per Anthropic rules
                messages.append(self._client.format_tool_result(result))

        return messages


