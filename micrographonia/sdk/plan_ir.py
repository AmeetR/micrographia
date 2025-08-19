from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Budget:
    """Budget constraints for a plan."""

    max_tool_calls: Optional[int] = None
    deadline_ms: Optional[int] = None
    max_parallel: Optional[int] = None


@dataclass
class Node:
    """A single node in the execution graph."""

    id: str
    tool: str
    inputs: Dict[str, Any]
    needs: List[str] | None = None
    out: Dict[str, str] | None = None


@dataclass
class Plan:
    """Plan intermediate representation."""

    version: str
    graph: List[Node]
    vars: Dict[str, Any] = field(default_factory=dict)
    budget: Optional[Budget] = None
