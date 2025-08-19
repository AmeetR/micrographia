from __future__ import annotations

import json
from pathlib import Path

import typer

from .validate import load_plan, validate_plan
from ..registry.registry import Registry
from ..runtime.engine import run_plan

app = typer.Typer()
plan_app = typer.Typer()
registry_app = typer.Typer()
app.add_typer(plan_app, name="plan")
app.add_typer(registry_app, name="registry")


def _load_impls():
    try:  # pragma: no cover - optional
        from ..tools.stubs import extractor_A, entity_linker, verifier, kg_writer

        return {
            "extractor_A.v1": extractor_A.run,
            "entity_linker.v1": entity_linker.run,
            "verifier.v1": verifier.run,
            "kg_writer.v1": kg_writer.run,
        }
    except Exception:  # pragma: no cover
        return {}


@plan_app.command("validate")
def plan_validate(plan: Path, registry: Path) -> None:
    reg = Registry(registry)
    p = load_plan(plan)
    validate_plan(p, reg)
    typer.echo("ok")


@plan_app.command("run")
def plan_run(
    plan: Path,
    context: Path,
    registry: Path,
    runs: Path = Path("runs"),
    deadline_ms: int | None = None,
) -> None:
    reg = Registry(registry)
    p = load_plan(plan)
    validate_plan(p, reg)
    ctx = json.loads(Path(context).read_text())
    record = run_plan(p, ctx, reg, impls=_load_impls(), runs_dir=runs)
    typer.echo(json.dumps(record, indent=2))


@registry_app.command("health")
def registry_health(registry: Path, base_url: str | None = None) -> None:
    reg = Registry(registry)
    result = reg.health(base_url)
    typer.echo(json.dumps(result, indent=2))


if __name__ == "__main__":  # pragma: no cover
    app()
