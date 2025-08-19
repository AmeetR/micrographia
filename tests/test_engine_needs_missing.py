from __future__ import annotations

from pathlib import Path

from micrographonia.registry.registry import Registry
from micrographonia.sdk.plan_ir import Plan, Node
from micrographonia.runtime.engine import run_plan
from micrographonia.tools.stubs import extractor_A, entity_linker

REG_DIR = Path("registry/manifests")
IMPLS = {
    "extractor_A.v1": extractor_A,
    "entity_linker.v1": entity_linker,
}


def test_missing_reference(tmp_path: Path) -> None:
    reg = Registry(REG_DIR)
    n1 = Node(id="extract", tool="extractor_A.v1", inputs={"text": "Hi"})
    n2 = Node(
        id="link",
        tool="entity_linker.v1",
        needs=["extract"],
        inputs={"mentions": "${extract.missing}"},
    )
    plan = Plan(version="0.1", graph=[n1, n2])
    record = run_plan(plan, {}, reg, impls=IMPLS, runs_dir=tmp_path)
    assert record["ok"] is False
    err_path = Path(record["paths"]["nodes"]["link"]["error"])
    assert err_path.exists()
