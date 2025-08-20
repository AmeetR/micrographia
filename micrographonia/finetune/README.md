# Finetuning utilities

Scaffolding for building small task-specific adapters used by Micrographia.
This package currently contains:

- `cli.py` — Typer-based command line entry points.
- `data/` — task plugins and JSON schemas.
  - `plugins/base.py` defines the `TaskPlugin` protocol and registry.
  - `plugins/notes_kg.py` is an example plugin that produces triple
    extraction seed data.
  - `schemas/interaction_v1.json` and `schemas/structured_v1.json`
    describe the unified data record and a toy triples schema.
- `tests/` — unit tests for the scaffolding.

## Example

Generate seed examples with the built-in `notes_kg` plugin:

```bash
python -m micrographonia.finetune.cli datagen-seed \
    --task notes_kg --out seeds.jsonl
```

The JSONL output contains unified interaction records that can later be
augmented by a teacher model and converted to train/validation/test
splits.

## Writing a plugin

To add a new task, implement `TaskPlugin` and register an instance:

```python
from micrographonia.finetune.data.plugins.base import TaskPlugin, register

class MyPlugin(TaskPlugin):
    name = "my_task"
    def schema(self) -> dict | None:
        return None
    def seed_examples(self, n: int | None = None) -> list[dict]:
        return []
    def metrics(self, preds: list, refs: list) -> dict:
        return {}

register(MyPlugin())
```

CLI commands will be able to reference the plugin by its `name`.
