"""Training command and utilities for distilling tiny models.

The implementation here intentionally avoids heavy dependencies so that the
test suite runs quickly.  It demonstrates the orchestration flow for loading a
configuration, performing a mock training loop, evaluating the result and
storing artifacts.
"""

from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import typer
import yaml

from symphonia.training.datasets import load_dataset
from symphonia.training.distill import distill_loss, load_student, load_teacher
from symphonia.training.eval import evaluate


@dataclass
class Config:
    """Strongly typed view of the training configuration."""

    model: Dict[str, Any]
    data: Dict[str, Any]
    training: Dict[str, Any]
    logging: Dict[str, Any]


class ConfigError(Exception):
    """Raised when a configuration file is invalid."""

    pass


def load_config(path: Path) -> Config:
    """Parse a YAML configuration file into a :class:`Config` object."""

    try:
        data = yaml.safe_load(Path(path).read_text())
    except Exception as exc:  # pragma: no cover - yaml library errors
        raise ConfigError(str(exc)) from exc
    required = ["model", "data", "training", "logging"]
    for key in required:
        if key not in data:
            raise ConfigError(f"missing '{key}' section")
    return Config(**{k: data[k] for k in required})


def _save_artifacts(output_dir: Path, config: Config, metrics: dict) -> str:
    """Persist model artifacts and update a tiny registry.

    Returns the SHA256 hash of the saved adapter to emulate real model
    registries.
    """

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "adapter.bin").write_bytes(b"stub")
    (output_dir / "config.json").write_text(json.dumps(config.__dict__, indent=2))
    (output_dir / "eval.json").write_text(json.dumps(metrics, indent=2))
    (output_dir / "card.md").write_text("Model card\n===========\n")
    sha = hashlib.sha256((output_dir / "adapter.bin").read_bytes()).hexdigest()
    registry_path = output_dir.parent / "models_registry.json"
    registry: list = []
    if registry_path.exists():
        registry = json.loads(registry_path.read_text())
    registry.append({"path": str(output_dir), "hash": sha})
    registry_path.write_text(json.dumps(registry, indent=2))
    return sha


def train(config: Config) -> dict:
    """Run a mock training and evaluation loop using ``config``."""

    teacher = load_teacher(config.data["teacher_model"])
    student = load_student(config.model["base"], config.model.get("adapter", "full_ft"))

    splits = config.data.get("split", ["train", "val"])
    data = load_dataset(config.data["dataset"], splits)
    train_data = data.get("train", [])
    val_data = data.get("val", [])

    for _ in range(config.training.get("epochs", 1)):
        for item in train_data:
            inp = item["input"]
            teacher_out = teacher.predict(inp)
            student_out = student.predict(inp)
            _ = distill_loss(student_out, teacher_out)
            student.learn(inp, teacher_out)

    metrics = evaluate(student, teacher, val_data)
    _save_artifacts(Path(config.model["output_dir"]), config, metrics)
    return metrics


cli = typer.Typer()


@cli.command()
def main(
    config: Path = typer.Option(..., "--config", "-c", help="Path to YAML config"),
    emit_summary: bool = typer.Option(False, "--emit-summary", is_flag=True),
) -> None:
    """Entry point for ``micrographonia train``."""

    try:
        cfg = load_config(config)
        metrics = train(cfg)
    except ConfigError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(2)
    if emit_summary:
        typer.echo(json.dumps(metrics))
    else:
        typer.echo(json.dumps(metrics, indent=2))


if __name__ == "__main__":  # pragma: no cover
    cli()
