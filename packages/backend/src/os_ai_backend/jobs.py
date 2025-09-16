from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Dict

from os_ai_core.orchestrator import CancelToken


@dataclass
class Job:
    id: str
    cancel: CancelToken


class JobManager:
    def __init__(self) -> None:
        self._jobs: Dict[str, Job] = {}

    def register(self, job: Job) -> None:
        self._jobs[job.id] = job

    def cancel(self, job_id: str) -> bool:
        j = self._jobs.get(job_id)
        if not j:
            return False
        j.cancel.cancel()
        return True

    def remove(self, job_id: str) -> None:
        self._jobs.pop(job_id, None)


# singleton
jobs = JobManager()


