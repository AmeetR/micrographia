from __future__ import annotations

import json
from pathlib import Path

from symphonia.registry.registry import Registry
from symphonia.sdk.validate import load_plan, validate_plan
from symphonia.runtime.engine import run_plan
from symphonia.tools.stubs import extractor_A, entity_linker, kg_writer, verifier

REG_DIR = Path("registry/manifests")
PLAN_PATH = Path("examples/manual_plans/notes.yml")
CTX_PATH = Path("examples/datasets/note.json")

IMPLS = {
    "extractor_A.v1": extractor_A,
    "entity_linker.v1": entity_linker,
    "verifier.v1": verifier,
    "kg_writer.v1": kg_writer,
}


def test_engine_run(tmp_path: Path) -> None:
    reg = Registry(REG_DIR)
    plan = load_plan(PLAN_PATH)
    validate_plan(plan, reg)
    ctx = json.loads(CTX_PATH.read_text())
    record, err = run_plan(plan, ctx, reg, impls=IMPLS, runs_dir=tmp_path)
    assert err is None
    assert record["ok"] is True
    assert record["totals"]["tool_calls"] == 4
    node_resp = Path(record["artifacts"]["nodes"]["write"]["response"])
    out_path = Path(json.loads(node_resp.read_text())["data"]["path"])
    assert out_path.exists()


def test_engine_failure(tmp_path: Path) -> None:
    reg = Registry(REG_DIR)
    plan = load_plan(PLAN_PATH)
    validate_plan(plan, reg)
    ctx = json.loads(CTX_PATH.read_text())
    bad_impls = dict(IMPLS)
    bad_impls["entity_linker.v1"] = lambda p: {}
    record, err = run_plan(plan, ctx, reg, impls=bad_impls, runs_dir=tmp_path)
    assert record["ok"] is False
    assert err is not None
    node_err = record["artifacts"]["nodes"]["link"]["error"]
    assert Path(node_err).exists()
