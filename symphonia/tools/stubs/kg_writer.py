"""Stub knowledge-graph writer that persists triples to disk."""

import json
from pathlib import Path

from symphonia.runtime.tools import InprocTool


def run(payload: dict) -> dict:
    """Write triples to a JSON file and return its path."""

    path = Path(payload.get("path", "kg.json"))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump({"triples": payload["triples"]}, fh, indent=2)
    return {"path": str(path)}


def factory(manifest, loader, preloaded=None):  # pragma: no cover - simple stub
    return InprocTool(manifest, run)
