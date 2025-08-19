from __future__ import annotations

from typing import Callable, Protocol

import httpx
from jsonschema import Draft7Validator, ValidationError

from ..registry.manifest import ToolManifest
from .errors import SchemaError, ToolCallError


class Tool(Protocol):
    """Tool protocol."""

    manifest: ToolManifest

    def invoke(self, payload: dict, timeout_s: float | None = None) -> dict: ...


class HttpTool:
    """Invoke tools exposed over HTTP."""

    def __init__(self, manifest: ToolManifest):
        self.manifest = manifest
        self._in_validator = Draft7Validator(manifest.input_schema)
        self._out_validator = Draft7Validator(manifest.output_schema)

    def invoke(self, payload: dict, timeout_s: float | None = None) -> dict:
        try:
            self._in_validator.validate(payload)
        except ValidationError as exc:
            raise SchemaError(f"input schema error: {exc.message}") from exc

        try:
            resp = httpx.post(self.manifest.endpoint, json=payload, timeout=timeout_s)
        except httpx.HTTPError as exc:
            raise ToolCallError(status=None, message=str(exc)) from exc
        if resp.status_code >= 400:
            raise ToolCallError(status=resp.status_code, body=resp.text)

        data = resp.json()
        try:
            self._out_validator.validate(data)
        except ValidationError as exc:
            raise SchemaError(f"output schema error: {exc.message}") from exc
        return data


class InprocTool:
    """Wrap a Python callable as a tool."""

    def __init__(self, manifest: ToolManifest, func: Callable[[dict], dict]):
        self.manifest = manifest
        self.func = func
        self._in_validator = Draft7Validator(manifest.input_schema)
        self._out_validator = Draft7Validator(manifest.output_schema)

    def invoke(self, payload: dict, timeout_s: float | None = None) -> dict:  # pragma: no cover - timeout unused
        try:
            self._in_validator.validate(payload)
        except ValidationError as exc:
            raise SchemaError(f"input schema error: {exc.message}") from exc
        data = self.func(payload)
        try:
            self._out_validator.validate(data)
        except ValidationError as exc:
            raise SchemaError(f"output schema error: {exc.message}") from exc
        return data
