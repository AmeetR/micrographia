"""Utilities for parsing retry policies and computing backoff delays."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Iterable, List, Sequence

from .errors import EngineError, SchemaError, ToolCallError


@dataclass
class _Rule:
    """Internal representation of a single retry rule."""

    exc_type: type
    code: int | None = None
    family: int | None = None
    stage: str | None = None


class RetryMatcher:
    """Determine whether an exception should trigger a retry."""

    _MAP = {
        "ToolCallError": ToolCallError,
        "SchemaError": SchemaError,
        "EngineError": EngineError,
    }

    def __init__(self, patterns: Sequence[str]):
        self.rules: List[_Rule] = [self._parse(p) for p in patterns]

    def _parse(self, pattern: str) -> _Rule:
        """Convert a retry *pattern* string into a :class:`_Rule`."""

        cls_name, _, spec = pattern.partition(":")
        exc_type = self._MAP.get(cls_name)
        if exc_type is None:
            raise ValueError(f"unknown retry class {cls_name}")
        code = family = None
        stage = None
        if spec:
            if exc_type is ToolCallError:
                if spec.endswith("xx") and len(spec) == 3:
                    family = int(spec[0]) * 100
                else:
                    code = int(spec)
            elif exc_type is SchemaError:
                stage = spec
        return _Rule(exc_type, code=code, family=family, stage=stage)

    def matches(self, exc: Exception) -> bool:
        for rule in self.rules:
            if isinstance(exc, rule.exc_type):
                if rule.exc_type is ToolCallError:
                    status = getattr(exc, "status", None)
                    if rule.code is not None and status != rule.code:
                        continue
                    if rule.family is not None and (
                        status is None or status // 100 * 100 != rule.family
                    ):
                        continue
                elif rule.exc_type is SchemaError and rule.stage is not None:
                    if getattr(exc, "stage", None) != rule.stage:
                        continue
                return True
        return False


def backoff_delays(retries: int, backoff_ms: int, jitter_ms: int = 0) -> List[float]:
    """Compute the sequence of backoff delays in milliseconds."""
    delays: List[float] = []
    for attempt in range(retries):
        base = backoff_ms * (2 ** attempt)
        jitter = random.uniform(0, jitter_ms) if jitter_ms else 0
        delays.append(base + jitter)
    return delays
