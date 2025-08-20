"""Dataclasses describing tools available in the registry."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class ToolManifest:
    """Description of a tool available in the registry."""

    name: str
    version: str
    kind: str  # "http" or "inproc"
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    endpoint: Optional[str] = None
    tags: list[str] | None = None

    @property
    def fqdn(self) -> str:
        """Return name.version string."""

        return f"{self.name}.{self.version}"
