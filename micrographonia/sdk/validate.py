from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Set

import yaml
from jsonschema import Draft7Validator, ValidationError

from .plan_ir import Plan, Node, Budget, Execution, RetryPolicy
from ..registry.registry import Registry
from ..runtime.errors import PlanSchemaError
from ..runtime.retry import RetryMatcher

SCHEMA_PATH = Path(__file__).parent / "schemas" / "plan_ir.schema.json"
SCHEMA = json.loads(SCHEMA_PATH.read_text())
VALIDATOR = Draft7Validator(SCHEMA)


def load_plan(path: str | Path) -> Plan:
    """Load a plan from YAML or JSON and return a :class:`Plan`."""

    path = Path(path)
    data = json.loads(path.read_text()) if path.suffix == ".json" else yaml.safe_load(path.read_text())
    try:
        VALIDATOR.validate(data)
    except ValidationError as exc:
        raise PlanSchemaError(str(exc)) from exc
    return _from_dict(data)


def _from_dict(data: Dict) -> Plan:
    budget = data.get("budget")
    budget_obj = Budget(**budget) if budget else None

    execution = data.get("execution")
    if execution:
        retry_def = execution.get("retry_default")
        retry_def_obj = RetryPolicy(**retry_def) if retry_def else None
        execution_obj = Execution(
            max_parallel=execution.get("max_parallel"),
            cache_default=execution.get("cache_default"),
            retry_default=retry_def_obj,
        )
    else:
        execution_obj = None

    def _node_from_dict(n: Dict) -> Node:
        retry = n.get("retry")
        retry_obj = RetryPolicy(**retry) if retry else None
        return Node(
            id=n["id"],
            tool=n["tool"],
            inputs=n["inputs"],
            needs=n.get("needs"),
            out=n.get("out"),
            cache=n.get("cache"),
            timeout_ms=n.get("timeout_ms"),
            retry=retry_obj,
            concurrency=n.get("concurrency"),
        )

    nodes = [_node_from_dict(n) for n in data["graph"]]

    return Plan(
        version=data["version"],
        vars=data.get("vars", {}),
        budget=budget_obj,
        graph=nodes,
        execution=execution_obj,
    )


def validate_plan(plan: Plan, registry: Registry) -> None:
    """Validate structural rules for the plan against a registry."""

    node_ids: Set[str] = set()
    for node in plan.graph:
        if node.id in node_ids:
            raise PlanSchemaError(f"duplicate node id {node.id}")
        node_ids.add(node.id)
        try:
            registry.resolve(node.tool)
        except Exception as exc:
            raise PlanSchemaError(f"unknown tool {node.tool}") from exc
        if node.retry and node.retry.retry_on:
            try:
                RetryMatcher(node.retry.retry_on)
            except ValueError as exc:
                raise PlanSchemaError(str(exc)) from exc

    # needs references exist and DAG acyclic
    edges = {node.id: node.needs or [] for node in plan.graph}
    _check_acyclic(edges)

    if plan.execution and plan.execution.retry_default and plan.execution.retry_default.retry_on:
        try:
            RetryMatcher(plan.execution.retry_default.retry_on)
        except ValueError as exc:
            raise PlanSchemaError(str(exc)) from exc


def _check_acyclic(edges: Dict[str, List[str]]) -> None:
    temp: Set[str] = set()
    perm: Set[str] = set()

    def visit(n: str) -> None:
        if n in perm:
            return
        if n in temp:
            raise PlanSchemaError("graph contains a cycle")
        temp.add(n)
        for m in edges.get(n, []):
            if m not in edges:
                raise PlanSchemaError(f"unknown dependency {m}")
            visit(m)
        temp.remove(n)
        perm.add(n)

    for node in edges:
        visit(node)
