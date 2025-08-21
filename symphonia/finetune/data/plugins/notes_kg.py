"""Example task plugin for a simple notes → knowledge graph task.

The plugin provides a small number of seed examples and a JSON schema
for the structured ``target.json`` field consisting of subject/predicate/object
triples. Metrics are intentionally left empty for the scaffold stage.

Example
-------
Retrieve the plugin and inspect a seed example::

    from symphonia.finetune.data.plugins.base import get_plugin
    plugin = get_plugin("notes_kg")
    first = plugin.seed_examples()[0]
    first["target"]["json"]["triples"]
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Dict

from .base import register


@dataclass
class NotesKGPlugin:
    name: str = "notes_kg"

    def __post_init__(self) -> None:
        schema_path = Path(__file__).resolve().parents[1] / "schemas" / "structured_v1.json"
        with schema_path.open("r", encoding="utf-8") as f:
            self._schema = json.load(f)

    def schema(self) -> dict | None:  # pragma: no cover - simple getter
        return self._schema

    def seed_examples(self, n: int | None = None) -> List[Dict]:
        examples = [
            {
                "id": "seed-1",
                "source": "seed",
                "input": {
                    "prompt": "Aspirin reduces headaches.",
                    "context": {},
                },
                "target": {
                    "text": None,
                    "json": {
                        "triples": [
                            {
                                "subject": "Aspirin",
                                "predicate": "reduces",
                                "object": "headaches",
                            }
                        ]
                    },
                },
                "meta": {
                    "task": "notes_kg",
                    "lang": "en",
                    "difficulty": "easy",
                    "tags": ["triples"],
                    "teacher_model": None,
                    "added_at": datetime.now().isoformat(),
                },
            }
        ]
        if n is not None:
            return examples[:n]
        return examples

    def metrics(self, preds: list, refs: list) -> Dict:  # pragma: no cover - stub
        return {}


# Register plugin instance
plugin = NotesKGPlugin()
register(plugin)
