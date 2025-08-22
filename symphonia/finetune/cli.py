"""CLI entry points for finetuning utilities.

This module provides a Typer app exposing subcommands under the
``symphonia.finetune`` namespace. Currently only a minimal
``datagen-seed`` command is implemented which generates seed examples
for a given task plugin and writes them to a JSONL file.

Example
-------
Run the seed generator for the built-in ``notes_kg`` task and save the
examples to ``seeds.jsonl``::

    python -m symphonia.finetune.cli datagen-seed \
        --task notes_kg --out seeds.jsonl

This scaffolding will be extended in future PRs.
"""
from __future__ import annotations

import json
from pathlib import Path

import typer

from .common.identity import stable_id
from .common.validation import validate_record
from .data.plugins.base import get_plugin

app = typer.Typer(help="Finetuning utilities")


@app.command("datagen-seed")
def datagen_seed(task: str, out: Path) -> None:
    """Generate seed examples for *task* and write to *out* as JSONL.

    The command loads the task plugin, obtains its seed examples and writes
    each example as a line of JSON to the provided ``out`` path.
    It is intentionally lightweight to keep the initial scaffold simple;
    later iterations will add Parquet output and additional options.

    Example
    -------
    ``python -m symphonia.finetune.cli datagen-seed --task notes_kg \``
    ``--out seeds.jsonl``
    """

    plugin = get_plugin(task)
    examples = plugin.seed_examples()

    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for row in examples:
            ok, err = validate_record(row, plugin, require_json=plugin.schema() is not None)
            if not ok:
                raise typer.BadParameter(f"invalid record: {err}")
            row["id"] = stable_id(row)
            json.dump(row, f)
            f.write("\n")


if __name__ == "__main__":  # pragma: no cover - manual invocation
    app()
