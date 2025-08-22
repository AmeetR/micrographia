"""Record validation helpers."""
from __future__ import annotations

from pathlib import Path
from typing import Tuple

import json
from jsonschema import Draft202012Validator, ValidationError

from ..data.plugins.base import TaskPlugin

# Load and cache the base interaction schema
_SCHEMA_PATH = Path(__file__).resolve().parents[1] / "data" / "schemas" / "interaction_v1.json"
with _SCHEMA_PATH.open("r", encoding="utf-8") as _f:
    _INTERACTION_SCHEMA = json.load(_f)
_INTERACTION_VALIDATOR = Draft202012Validator(_INTERACTION_SCHEMA)


def validate_record(rec: dict, plugin: TaskPlugin, require_json: bool) -> Tuple[bool, str | None]:
    """Validate a dataset *rec* against base and plugin schemas.

    Returns ``(True, None)`` if valid, otherwise ``(False, reason)`` describing
    the failure. ``require_json`` enforces presence of ``target.json`` when the
    plugin declares a schema.
    """

    try:
        _INTERACTION_VALIDATOR.validate(rec)
    except ValidationError as exc:  # pragma: no cover - jsonschema detail
        return False, str(exc)

    if "prompt" not in rec.get("input", {}):
        return False, "missing input.prompt"

    target = rec.get("target", {})
    if "text" not in target and "json" not in target:
        return False, "target must include text or json"

    schema = plugin.schema()
    if schema and (require_json or "json" in target):
        if "json" not in target:
            return False, "target.json required"
        try:
            Draft202012Validator(schema).validate(target["json"])
        except ValidationError as exc:  # pragma: no cover - detail
            return False, f"target.json invalid: {exc.message}"

    return True, None
