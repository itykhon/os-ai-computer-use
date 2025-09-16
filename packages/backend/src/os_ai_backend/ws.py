from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any, Dict, Optional

from fastapi import WebSocket

try:
    import orjson as json  # type: ignore
except Exception:  # pragma: no cover - fallback if orjson not available
    import json  # type: ignore

from os_ai_llm.types import ToolDescriptor
from os_ai_core.orchestrator import Orchestrator, CancelToken
from os_ai_core.di import create_container

from os_ai_llm.interfaces import LLMClient
from os_ai_core.tools.registry import ToolRegistry

import pyautogui

from os_ai_llm_anthropic.config import COMPUTER_TOOL_TYPE
from .jobs import jobs, Job
from .metrics import metrics


LOGGER_NAME = "os_ai.backend"


class WebSocketRPCHandler:
    """Minimal JSON-RPC 2.0 handler over WebSocket.

    Supported methods (phase 1):
      - session.create
      - agent.run
      - agent.cancel (MVP: no-op acknowledgement)
    """

    def __init__(self) -> None:
        self._logger = logging.getLogger(LOGGER_NAME)

    async def handle(self, websocket: WebSocket) -> None:
        metrics.inc("ws_connections", 1)
        while True:
            raw = await websocket.receive_text()
            try:
                req = json.loads(raw)
            except Exception:
                await self._send_error(websocket, None, -32700, "Parse error")
                continue

            if not isinstance(req, dict):
                await self._send_error(websocket, None, -32600, "Invalid Request")
                continue

            req_id = req.get("id")
            method = req.get("method")
            params = req.get("params") or {}

            if method == "session.create":
                provider = params.get("provider")
                session_id, client, tools = self._create_session(provider)
                await self._send_result(websocket, req_id, {
                    "sessionId": session_id,
                    "capabilities": {"ws": True, "jsonrpc": True}
                })
            elif method == "agent.run":
                task_text = params.get("task") or ""
                if not task_text:
                    await self._send_error(websocket, req_id, -32602, "Missing 'task'")
                    continue
                provider = params.get("provider")
                max_iterations = int(params.get("maxIterations", 30))

                # Build session and run orchestration in background
                session_id, client, tools = self._create_session(provider)
                job_id = str(uuid.uuid4())
                await self._send_result(websocket, req_id, {"jobId": job_id, "sessionId": session_id})

                # Register cancel token before starting the job
                early_cancel = CancelToken()
                jobs.register(Job(id=job_id, cancel=early_cancel))

                task = asyncio.create_task(self._run_job_and_notify(
                    websocket=websocket,
                    job_id=job_id,
                    client=client,
                    tools=tools,
                    task_text=task_text,
                    max_iterations=max_iterations,
                    cancel=early_cancel,
                ))
                # store cancel handle
                # CancelToken constructed in _run_job_and_notify; register a placeholder now, and update within
                # For simplicity, we will register on first event; alternatively refactor to pass out token
            elif method == "agent.cancel":
                # idempotent cancel: treat unknown job as already finished/cancelled
                job_id = params.get("jobId")
                if job_id:
                    try:
                        jobs.cancel(str(job_id))
                        ok = True
                    except Exception:
                        ok = True
                else:
                    ok = False
                await self._send_result(websocket, req_id, {"ok": ok, "jobId": job_id})
            else:
                await self._send_error(websocket, req_id, -32601, "Method not found")

    async def _run_job_and_notify(
        self,
        websocket: WebSocket,
        job_id: str,
        client: LLMClient,
        tools: ToolRegistry,
        task_text: str,
        max_iterations: int,
        cancel: CancelToken,
    ) -> None:
        screen_w, screen_h = pyautogui.size()
        tool_descs = [
            ToolDescriptor(
                name="computer",
                kind="computer_use",
                params={
                    "type": COMPUTER_TOOL_TYPE,
                    "display_width_px": screen_w,
                    "display_height_px": screen_h,
                },
            )
        ]
        system_prompt = (
            "You are an expert desktop operator. Use the computer tool to complete the user's task. "
            "ONLY take a screenshot when needed. Prefer keyboard shortcuts. "
            "NEVER send empty key combos; always include a valid key or hotkey like 'cmd+space'. "
            "When using key/hold_key, provide 'key' or 'keys' as a non-empty string (e.g., 'cmd+space', 'ctrl+c'). "
            "For any action with coordinates, set coordinate_space='auto' in tool input."
        )

        orch = Orchestrator(client, tools)
        loop = asyncio.get_running_loop()

        def on_event(kind: str, payload: Dict[str, Any]) -> None:
            try:
                # Map orchestrator events to WS notifications
                if kind == "assistant_text":
                    # as log for now
                    asyncio.run_coroutine_threadsafe(self._send_event(websocket, "event.log", {"level": "info", "message": payload.get("text", ""), "jobId": job_id}), loop)
                elif kind == "tool_call":
                    asyncio.run_coroutine_threadsafe(self._send_event(websocket, "event.action", {"name": payload.get("name"), "status": "start", "meta": payload.get("args", {}), "jobId": job_id}), loop)
                elif kind == "tool_result_text":
                    asyncio.run_coroutine_threadsafe(self._send_event(websocket, "event.action", {"name": "tool_result", "status": "ok", "meta": payload, "jobId": job_id}), loop)
                elif kind == "tool_result_image":
                    asyncio.run_coroutine_threadsafe(self._send_event(websocket, "event.screenshot", {"mime": payload.get("media_type", "image/jpeg"), "data": payload.get("data", ""), "ts": None, "jobId": job_id}), loop)
                elif kind == "progress":
                    asyncio.run_coroutine_threadsafe(self._send_event(websocket, "event.progress", {**payload, "jobId": job_id}), loop)
            except Exception:
                pass

        def _blocking_run() -> Dict[str, Any]:
            messages = orch.run(task_text, tool_descs, system_prompt, max_iterations=max_iterations, cancel_token=cancel, on_event=on_event)
            final_texts: list[str] = []
            for m in messages:
                if getattr(m, "role", None) == "assistant":
                    for p in (getattr(m, "content", []) or []):
                        try:
                            if getattr(p, "type", None) == "text":
                                txt = str(getattr(p, "text", ""))
                                if txt:
                                    final_texts.append(txt)
                        except Exception:
                            pass
            return {
                "text": "\n".join(final_texts).strip(),
                "usage": {
                    "input_tokens": int(getattr(orch, "total_input_tokens", 0) or 0),
                    "output_tokens": int(getattr(orch, "total_output_tokens", 0) or 0),
                },
                "status": "ok",
            }

        try:
            result = await loop.run_in_executor(None, _blocking_run)
        except Exception as exc:
            logging.getLogger(LOGGER_NAME).exception("Job failed: %s", exc)
            await self._send_event(websocket, "event.final", {"jobId": job_id, "status": "fail", "error": str(exc)})
            return

        await self._send_event(websocket, "event.final", {"jobId": job_id, **result})
        jobs.remove(job_id)

    def _create_session(self, provider: Optional[str]) -> tuple[str, LLMClient, ToolRegistry]:
        inj = create_container(provider)
        client = inj.get(LLMClient)
        tools = inj.get(ToolRegistry)
        session_id = str(uuid.uuid4())
        return session_id, client, tools

    async def _send_result(self, websocket: WebSocket, req_id: Any, result: Dict[str, Any]) -> None:
        payload = {"jsonrpc": "2.0", "id": req_id, "result": result}
        await websocket.send_text(self._dumps(payload))

    async def _send_error(self, websocket: WebSocket, req_id: Any, code: int, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        err = {"code": code, "message": message}
        if data is not None:
            err["data"] = data
        payload = {"jsonrpc": "2.0", "id": req_id, "error": err}
        await websocket.send_text(self._dumps(payload))

    async def _send_event(self, websocket: WebSocket, method: str, params: Dict[str, Any]) -> None:
        payload = {"jsonrpc": "2.0", "method": method, "params": params}
        await websocket.send_text(self._dumps(payload))

    def _dumps(self, obj: Any) -> str:
        try:
            return json.dumps(obj).decode()  # type: ignore[attr-defined]
        except Exception:
            return json.dumps(obj)  # type: ignore[no-any-return]


