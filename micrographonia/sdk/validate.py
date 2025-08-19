from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Set

import yaml
from jsonschema import Draft7Validator

from .plan_ir import Plan, Node, Budget
from ..registry.registry import Registry
from ..runtime.errors import PlanSchemaError

SCHEMA_PATH = Path(__file__).parent / "schemas" / "plan_ir.schema.json"
SCHEMA = json.loads(SCHEMA_PATH.read_text())
VALIDATOR = Draft7Validator(SCHEMA)


def load_plan(path: str | Path) -> Plan:
    """Load a plan from YAML or JSON and return a :class:`Plan`."""

    path = Path(path)
    data = json.loads(path.read_text()) if path.suffix == ".json" else yaml.safe_load(path.read_text())
    VALIDATOR.validate(data)
    return _from_dict(data)


def _from_dict(data: Dict) -> Plan:
    budget = data.get("budget")
    budget_obj = Budget(**budget) if budget else None
    nodes = [Node(**n) for n in data["graph"]]
    return Plan(version=data["version"], vars=data.get("vars", {}), budget=budget_obj, graph=nodes)


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

    # needs references exist and DAG acyclic
    edges = {node.id: node.needs or [] for node in plan.graph}
    _check_acyclic(edges)


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
