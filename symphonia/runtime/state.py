"""Helpers for managing runtime state and resolving references."""

from __future__ import annotations

import re
from typing import Any, Dict

from .errors import SchemaError

REF_RE = re.compile(r"\$\{([^}]+)\}")


class State(Dict[str, Any]):
    """Runtime state used for interpolation."""

    def __init__(self, context: Dict[str, Any], vars: Dict[str, Any]):
        super().__init__()
        self["context"] = context
        self["vars"] = vars
        self["nodes"] = {}


def _resolve_expr(expr: str, state: State) -> Any:
    """Resolve a dotted ``expr`` against the current ``state``."""

    parts = expr.split(".")
    if parts[0] == "context":
        target = state["context"]
        parts = parts[1:]
    elif parts[0] == "vars":
        target = state["vars"]
        parts = parts[1:]
    else:
        if parts[0] not in state["nodes"]:
            available = sorted(state["nodes"].keys())
            raise SchemaError(f"missing reference {expr}; available: {available}")
        target = state["nodes"][parts[0]]
        parts = parts[1:]
    for part in parts:
        if isinstance(target, dict) and part in target:
            target = target[part]
        else:
            available = sorted(target.keys()) if isinstance(target, dict) else []
            raise SchemaError(f"missing reference {expr}; available: {available}")
    return target


def interpolate(value: Any, state: State) -> Any:
    """Recursively replace ${} references in *value* using *state*."""

    if isinstance(value, dict):
        return {k: interpolate(v, state) for k, v in value.items()}
    if isinstance(value, list):
        return [interpolate(v, state) for v in value]
    if isinstance(value, str):
        match = REF_RE.fullmatch(value)
        if match:
            return _resolve_expr(match.group(1), state)
        return REF_RE.sub(lambda m: str(_resolve_expr(m.group(1), state)), value)
    return value


def extract_jsonpath(data: Dict[str, Any], path: str) -> Any:
    """Very small subset of JSONPath used in plan ``out`` mappings."""

    if not path.startswith("$."):
        raise KeyError(path)
    cur: Any = data
    parts = path[2:].split(".")
    for part in parts:
        if "[" in part and part.endswith("]"):
            name, idx = part[:-1].split("[")
            if name:
                cur = cur[name]
            cur = cur[int(idx)]
        else:
            cur = cur[part]
    return cur
