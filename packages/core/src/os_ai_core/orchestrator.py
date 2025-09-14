from __future__ import annotations

from typing import List, Optional
import logging, json, sys
import httpx
import anthropic

from os_ai_llm.interfaces import LLMClient
from os_ai_llm.types import Message, ToolDescriptor, TextPart
from os_ai_core.utils.costs import estimate_cost
from os_ai_core.config import USAGE_LOG_EACH_ITERATION, LOGGER_NAME
from os_ai_llm_anthropic.config import MODEL_NAME
from os_ai_core.tools.registry import ToolRegistry


class Orchestrator:
    def __init__(self, client: LLMClient, tool_registry: ToolRegistry) -> None:
        self._client = client
        self._tools = tool_registry

    def run(self, task: str, tool_descriptors: List[ToolDescriptor], system: Optional[str], max_iterations: int = 30) -> List[Message]:
        messages: List[Message] = [Message(role="user", content=[TextPart(text=task)])]
        logger = logging.getLogger(LOGGER_NAME)
        for _ in range(max_iterations):
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
                            except Exception:
                                pass
            except Exception:
                pass
            # Optional usage/cost logging similar to legacy
            try:
                if USAGE_LOG_EACH_ITERATION:
                    inp = int(getattr(resp.usage, "input_tokens", 0) or 0)
                    out = int(getattr(resp.usage, "output_tokens", 0) or 0)
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
                result = self._tools.execute(call)
                # Append tool_result immediately after the assistant tool_use per Anthropic rules
                messages.append(self._client.format_tool_result(result))

        return messages


