from __future__ import annotations

from pathlib import Path

from micrographonia.registry.registry import Registry
from micrographonia.sdk.plan_ir import Plan, Node, Execution
from micrographonia.runtime.engine import run_plan
from micrographonia.tools.stubs import extractor_A, kg_writer

REG_DIR = Path("registry/manifests")


def test_side_effect_bypass(tmp_path: Path) -> None:
    reg = Registry(REG_DIR)
    plan = Plan(
        version="0.1",
        execution=Execution(cache_default=True),
        graph=[
            Node(id="extract", tool="extractor_A.v1", inputs={"text": "hi"}),
            Node(
                id="write",
                tool="kg_writer.v1",
                needs=["extract"],
                inputs={"triples": [], "path": "${context.run_output}/out.json"},
            ),
        ],
    )
    calls = {"write": 0}

    def writer(p):
        calls["write"] += 1
        return kg_writer.run(p)

    impls = {"extractor_A.v1": extractor_A, "kg_writer.v1": writer}
    run_plan(plan, {}, reg, impls=impls, runs_dir=tmp_path)
    record2, _ = run_plan(plan, {}, reg, impls=impls, runs_dir=tmp_path)
    assert calls["write"] == 2
    assert record2["totals"]["cache_hits"] == 1
