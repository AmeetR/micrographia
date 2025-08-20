from __future__ import annotations

from pathlib import Path
import pytest

from micrographonia.registry.registry import Registry
from micrographonia.sdk.plan_ir import Plan, Node, Execution
from micrographonia.runtime.engine import run_plan
from micrographonia.runtime.errors import EngineError, ToolCallError
from micrographonia.tools.stubs import extractor_A, entity_linker, kg_writer

REG_DIR = Path("registry/manifests")


def test_resume_happy(tmp_path: Path) -> None:
    reg = Registry(REG_DIR)
    plan = Plan(
        version="0.1",
        graph=[
            Node(id="extract", tool="extractor_A.v1", inputs={"text": "hi"}),
            Node(
                id="link",
                tool="entity_linker.v1",
                needs=["extract"],
                inputs={"mentions": "${extract.mentions}"},
            ),
            Node(
                id="write",
                tool="kg_writer.v1",
                needs=["link"],
                inputs={"triples": [], "path": "${context.run_output}/out.json"},
            ),
        ],
        execution=Execution(cache_default=True),
    )
    counts = {"extract": 0, "link": 0, "write": 0}

    def extract(p):
        counts["extract"] += 1
        return extractor_A(p)

    fail = {"flag": True}

    def link_fail(p):
        counts["link"] += 1
        if fail["flag"]:
            fail["flag"] = False
            raise ToolCallError("boom", code=500)
        return entity_linker(p)

    def link_ok(p):
        counts["link"] += 1
        return entity_linker(p)

    def write(p):
        counts["write"] += 1
        return kg_writer(p)

    impls1 = {
        "extractor_A.v1": extract,
        "entity_linker.v1": link_fail,
        "kg_writer.v1": write,
    }
    record1, err1 = run_plan(plan, {}, reg, impls=impls1, runs_dir=tmp_path, run_id="r1")
    assert err1 is not None

    impls2 = {
        "extractor_A.v1": extract,
        "entity_linker.v1": link_ok,
        "kg_writer.v1": write,
    }
    record2, err2 = run_plan(plan, {}, reg, impls=impls2, runs_dir=tmp_path, run_id="r1")
    assert err2 is None
    assert record2["ok"] is True
    assert counts["extract"] == 1
    assert record2["totals"]["tool_calls"] == 2


def test_resume_mismatch(tmp_path: Path) -> None:
    reg = Registry(REG_DIR)
    n1 = Node(id="extract", tool="extractor_A.v1", inputs={"text": "hi"})
    plan1 = Plan(version="0.1", graph=[n1])
    impls = {"extractor_A.v1": extractor_A}
    run_plan(plan1, {}, reg, impls=impls, runs_dir=tmp_path, run_id="r2")

    n2 = Node(id="extra", tool="extractor_A.v1", inputs={"text": "hi"})
    plan2 = Plan(version="0.1", graph=[n1, n2])
    with pytest.raises(EngineError):
        run_plan(plan2, {}, reg, impls=impls, runs_dir=tmp_path, run_id="r2")
