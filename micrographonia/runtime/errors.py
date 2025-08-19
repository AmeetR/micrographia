"""Error taxonomy used across the runtime."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class MicrographiaError(Exception):
    """Base class for all custom exceptions."""


class PlanSchemaError(MicrographiaError):
    """Raised when a plan fails validation."""


class RegistryError(MicrographiaError):
    """Raised for registry loading or lookup failures."""


class SchemaError(MicrographiaError):
    """Input or output payload failed JSON-schema validation."""

    def __init__(
        self, message: str, errors: Any | None = None, stage: str | None = None
    ) -> None:
        super().__init__(message)
        self.errors = errors
        # stage is optional; when provided it typically indicates PRE/POST.
        self.stage = stage


@dataclass
class ToolCallError(MicrographiaError):
    """Error during tool invocation."""

    status: int | None
    body: Any | None = None
    message: str | None = None

    def __str__(self) -> str:  # pragma: no cover - trivial
        base = self.message or "tool call failed"
        if self.status is not None:
            base += f" (status={self.status})"
        return base


class BudgetError(MicrographiaError):
    """Raised when the execution budget is exceeded."""


class EngineError(MicrographiaError):
    """Raised for unexpected errors within the engine."""
