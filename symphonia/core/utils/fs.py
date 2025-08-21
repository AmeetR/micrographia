"""Filesystem helpers."""
from __future__ import annotations

from pathlib import Path


def atomic_write(path: Path, text: str) -> None:
    """Write text to ``path`` atomically.

    The content is first written to a temporary ``.tmp`` file which is then
    moved into place to avoid partially written files if the process crashes.
    """
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)
