from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import Dict


class ConcurrencyManager:
    """Manage global and per-tool concurrency limits."""

    def __init__(self, max_parallel: int):
        self.global_sem = asyncio.Semaphore(max_parallel)
        self._tool_limits: Dict[str, int] = {}
        self._tool_sems: Dict[str, asyncio.Semaphore] = {}

    def _get_tool_sem(self, tool: str, limit: int | None) -> asyncio.Semaphore:
        if tool not in self._tool_sems:
            if limit is None:
                limit = 1_000_000  # effectively unbounded
            self._tool_limits[tool] = limit
            self._tool_sems[tool] = asyncio.Semaphore(limit)
        return self._tool_sems[tool]

    @asynccontextmanager
    async def slot(self, tool: str, limit: int | None = None):
        tool_sem = self._get_tool_sem(tool, limit)
        async with self.global_sem, tool_sem:
            yield
