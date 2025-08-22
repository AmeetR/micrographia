"""Command line interface for validating and executing plans."""

from __future__ import annotations

import json
from pathlib import Path
from enum import IntEnum

import typer

from .validate import load_plan, validate_plan
from ..registry.registry import Registry
from ..runtime.engine import run_plan
from ..runtime.preflight import preflight_build_tool_pool
from ..runtime.model_loader import ModelLoader
from ..runtime.errors import (
    BudgetError,
    EngineError,
    SymphoniaError,
    PlanSchemaError,
    SchemaError,
    ToolCallError,
    RegistryError,
    ModelLoadError,
)
from symphonia.training.train import main as train_command

app = typer.Typer()
plan_app = typer.Typer()
registry_app = typer.Typer()
app.add_typer(plan_app, name="plan")
app.add_typer(registry_app, name="registry")
app.command("train")(train_command)


class ExitCode(IntEnum):
    SUCCESS = 0
    SCHEMA_ERROR = 12
    TOOL_CALL_ERROR = 13
    BUDGET_ERROR = 14
    ENGINE_ERROR = 15


EXIT_CODES = {
    SchemaError: ExitCode.SCHEMA_ERROR,
    ToolCallError: ExitCode.TOOL_CALL_ERROR,
    BudgetError: ExitCode.BUDGET_ERROR,
    PlanSchemaError: ExitCode.ENGINE_ERROR,
    EngineError: ExitCode.ENGINE_ERROR,
    RegistryError: ExitCode.ENGINE_ERROR,
    ModelLoadError: ExitCode.ENGINE_ERROR,
}


def _exit_err(exc: SymphoniaError) -> None:
    code = int(EXIT_CODES.get(type(exc), 1))
    typer.echo(str(exc), err=True)
    raise typer.Exit(code)


@plan_app.command("validate")
def plan_validate(plan: Path, registry: Path) -> None:
    try:
        reg = Registry(registry)
        p = load_plan(plan)
        validate_plan(p, reg)
    except SymphoniaError as exc:
        _exit_err(exc)
    typer.echo("ok")


@plan_app.command("run")
def plan_run(
    plan: Path,
    context: Path,
    registry: Path,
    runs: Path = Path("runs"),
    run_id: str | None = typer.Option(None, help="Reuse an existing run id"),
    resume: bool = typer.Option(True, help="Resume if run dir exists"),
    max_parallel: int | None = typer.Option(None, help="Override plan max_parallel"),
    cache_read: bool = typer.Option(True, help="Enable cache reads"),
    cache_write: bool = typer.Option(True, help="Enable cache writes"),
    no_warmup: bool = typer.Option(False, help="Skip model warmup"),
    emit_summary: bool = typer.Option(False, help="Emit one-line summary"),
) -> None:
    try:
        reg = Registry(registry)
        p = load_plan(plan)
        validate_plan(p, reg)
        ctx = json.loads(Path(context).read_text())
        record, err = run_plan(
            p,
            ctx,
            reg,
            runs_dir=runs,
            run_id=run_id,
            resume=resume,
            max_parallel=max_parallel,
            cache_read=cache_read,
            cache_write=cache_write,
            loader=ModelLoader(),
            warmup=not no_warmup,
        )
    except SymphoniaError as exc:
        _exit_err(exc)
        return
    if emit_summary:
        typer.echo(json.dumps(record))
    else:
        typer.echo(json.dumps(record, indent=2))
    if err:
        _exit_err(err)


@plan_app.command("check-models")
def plan_check_models(
    plan: Path,
    registry: Path,
    no_warmup: bool = typer.Option(False, help="Skip model warmup"),
) -> None:
    try:
        reg = Registry(registry)
        p = load_plan(plan)
        validate_plan(p, reg)
        preflight_build_tool_pool(p, reg, loader=ModelLoader(), warmup=not no_warmup)
    except SymphoniaError as exc:
        _exit_err(exc)
    typer.echo("ok")


@registry_app.command("health")
def registry_health(registry: Path, base_url: str | None = None) -> None:
    reg = Registry(registry)
    result = reg.health(base_url)
    typer.echo(json.dumps(result, indent=2))


if __name__ == "__main__":  # pragma: no cover
    app()
