from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Budget:
    """Budget constraints for a plan."""

    max_tool_calls: Optional[int] = None
    deadline_ms: Optional[int] = None


@dataclass
class Node:
    """A single node in the execution graph."""

    id: str
    tool: str
    inputs: Dict[str, Any]
    needs: List[str] | None = None
    out: Dict[str, str] | None = None
    cache: Optional[bool] = None
    timeout_ms: Optional[int] = None
    retry: Optional["RetryPolicy"] = None
    concurrency: Optional[int] = None


@dataclass
class RetryPolicy:
    retries: int = 0
    backoff_ms: int = 0
    jitter_ms: int = 0
    retry_on: List[str] = field(default_factory=list)


@dataclass
class Execution:
    max_parallel: Optional[int] = None
    cache_default: Optional[bool] = None
    retry_default: Optional[RetryPolicy] = None


@dataclass
class Plan:
    """Plan intermediate representation."""

    version: str
    graph: List[Node]
    vars: Dict[str, Any] = field(default_factory=dict)
    budget: Optional[Budget] = None
    execution: Optional[Execution] = None
