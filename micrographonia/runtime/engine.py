from __future__ import annotations

import time
from pathlib import Path
from typing import Callable, Dict

from ..sdk.plan_ir import Plan
from ..registry.registry import Registry
from .artifacts import RunArtifacts
from .errors import BudgetError, EngineError, SchemaError, ToolCallError
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
    ok = True
    last_id = None

    for node in plan.graph:
        last_id = node.id
        if plan.budget and plan.budget.max_tool_calls is not None:
            if metrics["tool_calls"] >= plan.budget.max_tool_calls:
                artifacts.write_node_error(node.id, "budget exceeded")
                raise BudgetError("max tool calls exceeded")

        inputs = interpolate(node.inputs, state)
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
