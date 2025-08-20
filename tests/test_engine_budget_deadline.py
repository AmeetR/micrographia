from __future__ import annotations

import time
from pathlib import Path

import pytest

from micrographonia.registry.registry import Registry
from micrographonia.sdk.plan_ir import Plan, Node, Budget
from micrographonia.runtime.engine import run_plan
from micrographonia.runtime.errors import BudgetError

REG_DIR = Path("registry/manifests")


def slow_extract(payload: dict) -> dict:
    time.sleep(0.2)
    return {"mentions": []}


def test_deadline_budget(tmp_path: Path) -> None:
    reg = Registry(REG_DIR)
    node = Node(id="extract", tool="extractor_A.v1", inputs={"text": "hi"})
    plan = Plan(version="0.1", graph=[node], budget=Budget(deadline_ms=50))
    impls = {"extractor_A.v1": slow_extract}
    record, err = run_plan(plan, {}, reg, impls=impls, runs_dir=tmp_path)
    assert record["ok"] is False
    assert record["stop_reason"] == "deadline"
    assert isinstance(err, BudgetError)
