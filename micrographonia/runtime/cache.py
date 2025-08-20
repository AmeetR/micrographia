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
    """Very small JSON-on-disk cache used for testing.

    The implementation is intentionally tiny but includes a couple of
    characteristics that are important for the runtime:

    * Writes are atomic – data is written to a ``.tmp`` file and then
      atomically renamed over the target path to avoid torn writes.
    * A size cap (``max_bytes``) can be supplied; when the cache grows
      beyond the limit the oldest entries are evicted in a basic LRU
      manner.

    The cache stores each entry as ``<key>.json`` containing a JSON
    document.  Keys are assumed to already be content addressed.
    """

    def __init__(self, root: Path, max_bytes: int | None = None):
        self.root = root
        self.max_bytes = max_bytes
        self.root.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    def _path(self, key: str) -> Path:
        return self.root / f"{key}.json"

    # ------------------------------------------------------------------
    def read(self, key: str) -> Any | None:
        path = self._path(key)
        if not path.exists():
            return None
        return json.loads(path.read_text())

    # ------------------------------------------------------------------
    def write(self, key: str, data: Any) -> None:
        path = self._path(key)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(_stable_dumps(data))
        tmp.replace(path)
        if self.max_bytes is not None:
            self._enforce_size()

    # ------------------------------------------------------------------
    def _enforce_size(self) -> None:
        """Delete oldest files until the cache fits ``max_bytes``."""

        files = sorted(
            [p for p in self.root.glob("*.json") if p.is_file()],
            key=lambda p: p.stat().st_mtime,
        )
        total = sum(p.stat().st_size for p in files)
        while total > (self.max_bytes or 0) and files:
            victim = files.pop(0)
            total -= victim.stat().st_size
            try:
                victim.unlink()
            except FileNotFoundError:  # pragma: no cover - race safe
                pass
