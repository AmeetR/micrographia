from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Callable, Dict, List

from ..sdk.plan_ir import Plan
from ..registry.registry import Registry
from .artifacts import RunArtifacts
from .errors import BudgetError, EngineError, SchemaError, ToolCallError, PlanSchemaError
from .state import State, interpolate, extract_jsonpath
from .tools import HttpTool, InprocTool, Tool


def run_plan(
    plan: Plan,
    context: Dict,
    registry: Registry,
    impls: Dict[str, Callable[[dict], dict]] | None = None,
    runs_dir: str | Path = "runs",
) -> Dict:
    """Execute *plan* sequentially."""

    artifacts = RunArtifacts(runs_dir)
    state = State(context, plan.vars)
    state["context"]["run_output"] = str(artifacts.output_dir)
    artifacts.write_plan(plan)
    artifacts.write_context(state["context"])

    metrics: Dict[str, Dict] = {"tool_calls": 0, "per_node": {}}
    start = time.perf_counter()
    deadline_at = (
        start + plan.budget.deadline_ms / 1000.0
        if plan.budget and plan.budget.deadline_ms
        else None
    )

    def _check_deadline(current_id: str) -> None:
        if deadline_at and time.perf_counter() > deadline_at:
            artifacts.write_node_error(current_id, "deadline exceeded")
            raise BudgetError("deadline_ms exceeded")

    ok = True
    last_id = None

    index: Dict[str, Any] = {n.id: n for n in plan.graph}
    seen: set[str] = set()
    ordered: List = []
    while len(ordered) < len(plan.graph):
        progress = False
        for n in plan.graph:
            if n.id in seen:
                continue
            needs = n.needs or []
            if all(req in seen or req not in index for req in needs):
                ordered.append(n)
                seen.add(n.id)
                progress = True
        if not progress:
            raise PlanSchemaError("cycle or unsatisfied 'needs' detected")

    for node in ordered:
        last_id = node.id
        _check_deadline(node.id)

        if plan.budget and plan.budget.max_tool_calls is not None:
            if metrics["tool_calls"] >= plan.budget.max_tool_calls:
                artifacts.write_node_error(node.id, "budget exceeded")
                raise BudgetError("max tool calls exceeded")

        if node.needs:
            missing = [n for n in node.needs if n not in state["nodes"]]
            if missing:
                artifacts.write_node_error(node.id, f"unsatisfied needs: {missing}")
                raise PlanSchemaError(
                    f"unsatisfied needs for node {node.id}: {missing}"
                )

        try:
            inputs = interpolate(node.inputs, state)
        except SchemaError as exc:
            ok = False
            artifacts.write_node_error(node.id, str(exc))
            metrics["per_node"][node.id] = {"ms": 0, "ok": False}
            break

        manifest = registry.resolve(node.tool)
        if manifest.kind == "http":
            tool: Tool = HttpTool(manifest)
        else:
            if not impls or manifest.fqdn not in impls:
                raise EngineError(f"missing implementation for {manifest.fqdn}")
            tool = InprocTool(manifest, impls[manifest.fqdn])

        artifacts.write_node_request(node.id, node.tool, inputs)
        node_start = time.perf_counter()
        try:
            response = tool.invoke(inputs)
        except (ToolCallError, SchemaError) as exc:
            ok = False
            artifacts.write_node_error(node.id, str(exc))
            metrics["per_node"][node.id] = {
                "ms": int((time.perf_counter() - node_start) * 1000),
                "ok": False,
            }
            break

        _check_deadline(node.id)

        node_ms = int((time.perf_counter() - node_start) * 1000)
        artifacts.write_node_response(node.id, node.tool, response, node_ms)
        metrics["per_node"][node.id] = {"ms": node_ms, "ok": True}
        metrics["tool_calls"] += 1

        expose = {}
        if node.out:
            for key, path in node.out.items():
                expose[key] = extract_jsonpath(response, path)
        else:
            expose = response
        state["nodes"][node.id] = expose

    total_ms = int((time.perf_counter() - start) * 1000)
    metrics["total_ms"] = total_ms
    artifacts.write_metrics(metrics)
    return {
        "run_id": artifacts.run_id,
        "ok": ok,
        "metrics": metrics,
        "paths": artifacts.paths,
        "state_tail": state["nodes"].get(last_id, {}),
    }
