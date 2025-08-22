"""Dataset loading utilities.

This module provides helpers for reading small JSONL datasets used by the
tests.  It intentionally keeps the implementation minimal so that the unit
tests run quickly without requiring external dependencies.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, List


def load_dataset(path: str | Path, splits: Iterable[str]) -> Dict[str, List[dict]]:
    """Load a JSONL dataset and partition by split field.

    Each line of the dataset must contain a JSON object with a ``split`` field
    designating which split (e.g. ``train``, ``val`` or ``test``) the example
    belongs to.  Only examples whose split is present in ``splits`` are returned.
    """

    path = Path(path)
    result: Dict[str, List[dict]] = {s: [] for s in splits}
    with path.open() as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            sp = obj.get("split")
            if sp in result:
                result[sp].append(obj)
    return result
