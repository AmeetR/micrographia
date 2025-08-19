from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict


def _stable_dumps(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def cache_key(
    tool: str, version: str, inputs: Dict[str, Any], manifest_hash: str
) -> str:
    """Compute a deterministic cache key for a tool invocation."""
    data = {
        "tool": tool,
        "version": version,
        "inputs": inputs,
        "manifest_hash": manifest_hash,
    }
    blob = _stable_dumps(data)
    return hashlib.sha256(blob.encode()).hexdigest()


class SimpleCache:
    """Very small JSON-on-disk cache used for testing."""

    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def read(self, key: str) -> Any | None:
        path = self.root / f"{key}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text())

    def write(self, key: str, data: Any) -> None:
        path = self.root / f"{key}.json"
        path.write_text(_stable_dumps(data))
