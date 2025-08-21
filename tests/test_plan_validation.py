from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from micrographonia.registry.registry import Registry
from micrographonia.runtime.errors import PlanSchemaError
from micrographonia.sdk.validate import load_plan, validate_plan

REG_DIR = Path("registry/manifests")
PLAN_PATH = Path("examples/manual_plans/notes.yml")


def test_valid_plan() -> None:
    reg = Registry(REG_DIR)
    plan = load_plan(PLAN_PATH)
    validate_plan(plan, reg)


def _write_plan(tmp_path: Path, data: dict) -> Path:
    path = tmp_path / "plan.yml"
    path.write_text(yaml.safe_dump(data))
    return path


def test_duplicate_id(tmp_path: Path) -> None:
    reg = Registry(REG_DIR)
    data = yaml.safe_load(PLAN_PATH.read_text())
    data["graph"][1]["id"] = "extract"  # duplicate
    path = _write_plan(tmp_path, data)
    plan = load_plan(path)
    with pytest.raises(PlanSchemaError):
        validate_plan(plan, reg)


def test_unknown_tool(tmp_path: Path) -> None:
    reg = Registry(REG_DIR)
    data = yaml.safe_load(PLAN_PATH.read_text())
    data["graph"][0]["tool"] = "missing.v1"
    path = _write_plan(tmp_path, data)
    plan = load_plan(path)
    with pytest.raises(PlanSchemaError):
        validate_plan(plan, reg)


def test_cycle(tmp_path: Path) -> None:
    reg = Registry(REG_DIR)
    data = yaml.safe_load(PLAN_PATH.read_text())
    data["graph"][0]["needs"] = ["write"]
    path = _write_plan(tmp_path, data)
    plan = load_plan(path)
    with pytest.raises(PlanSchemaError):
        validate_plan(plan, reg)


def test_invalid_execution_and_retry(tmp_path: Path) -> None:
    data = yaml.safe_load(PLAN_PATH.read_text())
    data["execution"] = {"max_parallel": 0}
    path = _write_plan(tmp_path, data)
    with pytest.raises(PlanSchemaError):
        load_plan(path)

    data["execution"] = {"max_parallel": 1}
    data["graph"][0]["retry"] = {"retries": -1}
    path = _write_plan(tmp_path, data)
    with pytest.raises(PlanSchemaError):
        load_plan(path)
