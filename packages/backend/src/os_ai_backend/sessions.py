from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Dict

from os_ai_llm.interfaces import LLMClient
from os_ai_core.tools.registry import ToolRegistry
from os_ai_core.di import create_container


@dataclass
class Session:
    id: str
    client: LLMClient
    tools: ToolRegistry


class SessionManager:
    def __init__(self) -> None:
        self._sessions: Dict[str, Session] = {}

    def create(self, provider: str | None) -> Session:
        inj = create_container(provider)
        client = inj.get(LLMClient)
        tools = inj.get(ToolRegistry)
        sid = str(uuid.uuid4())
        sess = Session(id=sid, client=client, tools=tools)
        self._sessions[sid] = sess
        return sess

    def get(self, session_id: str) -> Session:
        return self._sessions[session_id]

    def close(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)


