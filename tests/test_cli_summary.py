from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from micrographonia.sdk.cli import app

REG_DIR = Path("registry/manifests").resolve()


def _write(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data))


def test_cli_emit_summary(tmp_path: Path) -> None:
    plan_path = tmp_path / "plan.json"
    ctx_path = tmp_path / "ctx.json"
    _write(plan_path, {"version": "0.1", "graph": [{"id": "extract", "tool": "extractor_A.v1", "inputs": {"text": "hi"}}]})
    _write(ctx_path, {})
    runner = CliRunner()
    env = {"PYTHONPATH": str(Path(__file__).resolve().parents[1])}
    result = runner.invoke(
        app,
        [
            "plan",
            "run",
            str(plan_path),
            str(ctx_path),
            str(REG_DIR),
            "--runs",
            str(tmp_path / "runs"),
            "--emit-summary",
        ],
        env=env,
    )
    assert result.exit_code == 0
    data = json.loads(result.stdout.strip())
    assert data["ok"] is True
    assert data["stop_reason"] is None


def test_cli_exit_code_deadline(tmp_path: Path) -> None:
    plan_path = tmp_path / "plan.json"
    ctx_path = tmp_path / "ctx.json"
    _write(plan_path, {
        "version": "0.1",
        "budget": {"deadline_ms": 1},
        "graph": [{"id": "extract", "tool": "extractor_A.v1", "inputs": {"text": "hi"}}],
    })
    _write(ctx_path, {})
    runner = CliRunner()
    env = {"PYTHONPATH": str(Path(__file__).resolve().parents[1])}
    result = runner.invoke(
        app,
        [
            "plan",
            "run",
            str(plan_path),
            str(ctx_path),
            str(REG_DIR),
            "--runs",
            str(tmp_path / "runs"),
            "--emit-summary",
        ],
        env=env,
    )
    assert result.exit_code == 14
    data = json.loads(result.stdout.strip())
    assert data["stop_reason"] == "deadline"
