from __future__ import annotations

"""Async execution engine for Micrographia.

This module provides :func:`run_plan` which executes a plan described by the
:class:`~micrographonia.sdk.plan_ir.Plan` dataclass.  The implementation is a
light-weight orchestrator supporting parallel execution, retries with
exponential backoff, a tiny on-disk cache and the ability to resume interrupted
runs.  The goal of the implementation is not to be feature complete but to
provide the behaviour required by the tests in this kata.
"""

import asyncio
import hashlib
import json
import time
import datetime as _dt
from dataclasses import asdict
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

from ..sdk.plan_ir import Node, Plan, RetryPolicy
from ..registry.registry import Registry
from .artifacts import RunArtifacts
from .cache import SimpleCache, cache_key, _stable_dumps
from .concurrency import ConcurrencyManager
from .errors import (
    BudgetError,
    EngineError,
    ModelLoadError,
    MicrographiaError,
    PlanSchemaError,
    RegistryError,
    SchemaError,
    ToolCallError,
)
from .retry import RetryMatcher, backoff_delays
from .state import State, extract_jsonpath, interpolate
from .tools import Tool, InprocTool
from .model_loader import ModelLoader
from .preflight import preflight_build_tool_pool


# ---------------------------------------------------------------------------
def _hash_blob(data: Any) -> str:
    return hashlib.sha256(_stable_dumps(data).encode()).hexdigest()


# ---------------------------------------------------------------------------
async def _invoke_tool(tool: Tool, payload: Dict[str, Any], timeout_ms: int | None) -> Dict:
    timeout_s = timeout_ms / 1000.0 if timeout_ms else None
    return await asyncio.to_thread(tool.invoke, payload, timeout_s)


# ---------------------------------------------------------------------------
async def run_plan_async(
    plan: Plan,
    context: Dict,
    registry: Registry,
    impls: Dict[str, Callable[[dict], dict]] | None = None,
    runs_dir: str | Path = "runs",
    run_id: str | None = None,
    resume: bool = True,
    max_parallel: int | None = None,
    cache_read: bool = True,
    cache_write: bool = True,
    loader: ModelLoader | None = None,
    warmup: bool = True,
) -> Tuple[Dict, MicrographiaError | None]:
    """Execute *plan* asynchronously.

    Returns a tuple ``(summary, error)`` where ``summary`` contains basic
    run information and ``error`` is ``None`` on success or the terminal
    :class:`MicrographiaError` if the run failed.  The summary and metrics are
    written to disk regardless of success or failure.
    """

    # ------------------------------------------------------------------
    artifacts = RunArtifacts(runs_dir, run_id=run_id)
    state = State(context, plan.vars)
    state["context"]["run_output"] = str(artifacts.output_dir)

    # Hashes used for idempotency / resume checks
    inputs_hash = _hash_blob({"plan": asdict(plan), "context": state["context"]})
    registry_hash = registry.content_hash()

    existing = artifacts.read_run_info()
    if existing:
        if not resume:
            raise EngineError("run id exists; resume disabled")
        if existing.get("inputs_hash") != inputs_hash or existing.get("registry_hash") != registry_hash:
            raise EngineError("cannot resume: plan/context or registry changed")
    else:
        artifacts.write_plan(plan)
        artifacts.write_context(state["context"])
        artifacts.write_run_info(
            {
                "inputs_hash": inputs_hash,
                "registry_hash": registry_hash,
                "created_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
            }
        )

    # Load previous node results when resuming
    metrics: Dict[str, Any] = {
        "tool_calls": 0,
        "cache_hits": 0,
        "per_node": {},
        "retries": 0,
    }
    timeline: Dict[str, Any] = {}

    start = time.perf_counter()
    loader = loader or ModelLoader()
    try:
        tool_pool = preflight_build_tool_pool(plan, registry, loader=loader, warmup=warmup)
    except MicrographiaError as exc:
        metrics["stop_reason"] = "error:Preflight"
        artifacts.write_preflight_error(str(exc), exc.__class__.__name__)
        total_ms = int((time.perf_counter() - start) * 1000)
        metrics["total_ms"] = total_ms
        artifacts.write_metrics(metrics)
        artifacts.write_timeline(timeline)
        summary = {
            "run_id": artifacts.run_id,
            "ok": False,
            "stop_reason": metrics["stop_reason"],
            "totals": {
                "nodes": len(plan.graph),
                "tool_calls": 0,
                "cache_hits": 0,
                "retries": 0,
                "total_ms": total_ms,
            },
            "artifacts": artifacts.paths,
        }
        artifacts.write_summary(summary)
        return summary, exc

    for node in plan.graph:
        data = artifacts.read_node_response(node.id)
        if data:
            response = data.get("data", {})
            expose = {}
            if node.out:
                for k, path in node.out.items():
                    expose[k] = extract_jsonpath(response, path)
            else:
                expose = response
            state["nodes"][node.id] = expose
            manifest = tool_pool[node.tool].manifest
            cache_val: Any = (
                "bypassed:side_effect" if "side_effecting" in (manifest.tags or []) else False
            )
            metrics["per_node"][node.id] = {
                "ms": data.get("ms", 0),
                "ok": True,
                "cache": cache_val,
                "retries": 0,
            }
            timeline[node.id] = {"start_ms": 0, "end_ms": data.get("ms", 0)}

    if impls:
        for key, func in impls.items():
            if key in tool_pool:
                tool_pool[key] = InprocTool(tool_pool[key].manifest, func)

    # ------------------------------------------------------------------
    max_parallel = (
        max_parallel
        or (plan.execution.max_parallel if plan.execution and plan.execution.max_parallel else 1)
    )
    mgr = ConcurrencyManager(max_parallel=max_parallel)

    cache_dir = Path(runs_dir) / "cache"
    cache = SimpleCache(cache_dir)
    cache_default = (
        plan.execution.cache_default if plan.execution and plan.execution.cache_default is not None else False
    )
    retry_default = plan.execution.retry_default if plan.execution else None
    deadline_at = (
        start + plan.budget.deadline_ms / 1000.0
        if plan.budget and plan.budget.deadline_ms
        else None
    )

    # ------------------------------------------------------------------
    async def run_node(node: Node) -> None:
        nonlocal metrics

        if node.id in state["nodes"]:
            return  # already completed via resume

        node_start = time.perf_counter()
        start_ms = int((node_start - start) * 1000)
        timeline[node.id] = {"start_ms": start_ms, "attempts": [start_ms]}

        try:
            inputs = interpolate(node.inputs, state)
        except SchemaError as exc:
            metrics["per_node"][node.id] = {"ms": 0, "ok": False, "retries": 0}
            artifacts.write_node_error(node.id, str(exc))
            raise

        manifest = tool_pool[node.tool].manifest
        side_effect = "side_effecting" in (manifest.tags or [])
        use_cache = cache_read and (
            (node.cache if node.cache is not None else cache_default) and not side_effect
        )
        cache_status: Any = "bypassed:side_effect" if side_effect else False

        manifest_hash = _hash_blob(manifest.__dict__)
        ck = cache_key(manifest.name, manifest.version, inputs, manifest_hash)
        if use_cache:
            cached = cache.read(ck)
            if cached is not None:
                metrics["cache_hits"] += 1
                metrics["per_node"][node.id] = {
                    "ms": 0,
                    "ok": True,
                    "cache": True,
                    "retries": 0,
                }
                timeline[node.id]["end_ms"] = timeline[node.id]["start_ms"]
                expose = {}
                if node.out:
                    for k, path in node.out.items():
                        expose[k] = extract_jsonpath(cached, path)
                else:
                    expose = cached
                state["nodes"][node.id] = expose
                return

        tool: Tool = tool_pool[manifest.fqdn]

        artifacts.write_node_request(node.id, node.tool, inputs)

        policy: RetryPolicy = node.retry or retry_default or RetryPolicy()
        matcher = RetryMatcher(policy.retry_on)
        delays = backoff_delays(policy.retries, policy.backoff_ms, policy.jitter_ms)
        attempt = 0

        while True:
            attempt += 1
            if attempt > 1:
                timeline[node.id]["attempts"].append(
                    int((time.perf_counter() - start) * 1000)
                )
            try:
                # Honour deadline and per-node timeout
                timeout_ms = node.timeout_ms
                if deadline_at is not None:
                    remaining = int((deadline_at - time.perf_counter()) * 1000)
                    timeout_ms = (
                        remaining
                        if timeout_ms is None
                        else min(timeout_ms, remaining)
                    )
                    if timeout_ms <= 0:
                        raise BudgetError("deadline exceeded")

                async with mgr.slot(manifest.fqdn, node.concurrency):
                    response = await _invoke_tool(tool, inputs, timeout_ms)
                if deadline_at is not None and time.perf_counter() > deadline_at:
                    raise BudgetError("deadline exceeded")
                break
            except (ToolCallError, SchemaError) as exc:
                if attempt - 1 >= policy.retries or not matcher.matches(exc):
                    node_ms = int((time.perf_counter() - node_start) * 1000)
                    timeline[node.id]["end_ms"] = int((time.perf_counter() - start) * 1000)
                    metrics["per_node"][node.id] = {
                        "ms": node_ms,
                        "ok": False,
                        "cache": cache_status,
                        "retries": attempt - 1,
                    }
                    artifacts.write_node_error(node.id, str(exc))
                    raise
                metrics["retries"] += 1
                delay_ms = delays[attempt - 2]
                if deadline_at is not None:
                    remaining = (deadline_at - time.perf_counter()) * 1000
                    if remaining <= 0 or delay_ms > remaining:
                        await asyncio.sleep(max(0, remaining) / 1000)
                        raise BudgetError("deadline exceeded")
                await asyncio.sleep(delay_ms / 1000)

        node_ms = int((time.perf_counter() - node_start) * 1000)
        artifacts.write_node_response(node.id, node.tool, response, node_ms)
        metrics["per_node"][node.id] = {
            "ms": node_ms,
            "ok": True,
            "cache": cache_status,
            "retries": attempt - 1,
        }
        metrics["tool_calls"] += 1
        timeline[node.id]["end_ms"] = int((time.perf_counter() - start) * 1000)

        expose: Dict[str, Any] = {}
        if node.out:
            for key, path in node.out.items():
                expose[key] = extract_jsonpath(response, path)
        else:
            expose = response
        state["nodes"][node.id] = expose

        if use_cache and cache_write:
            cache.write(ck, response)

    # ------------------------------------------------------------------
    # Build dependency graph
    pending: Dict[str, Node] = {n.id: n for n in plan.graph}
    deps: Dict[str, List[str]] = {n.id: list(n.needs or []) for n in plan.graph}
    dependents: Dict[str, List[str]] = {n.id: [] for n in plan.graph}
    for node in plan.graph:
        for dep in node.needs or []:
            dependents.setdefault(dep, []).append(node.id)

    # Skip nodes that already have state (resume)
    for done_id in list(state["nodes"].keys()):
        if done_id in deps:
            for dep in dependents.get(done_id, []):
                if dep in deps:
                    deps[dep].remove(done_id)
            deps.pop(done_id, None)
            pending.pop(done_id, None)

    ready = [pending[n_id] for n_id, d in deps.items() if not d]
    tasks: Dict[asyncio.Task[Any], str] = {}
    completed: set[str] = set()
    ok = True
    stop_exc: Exception | None = None

    while ready or tasks:
        while ready:
            node = ready.pop()
            task = asyncio.create_task(run_node(node))
            tasks[task] = node.id

        if not tasks:
            break

        done, _ = await asyncio.wait(tasks.keys(), return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            node_id = tasks.pop(task)
            try:
                await task
                completed.add(node_id)
                for dep in dependents.get(node_id, []):
                    if dep in deps:
                        deps[dep].remove(node_id)
                        if not deps[dep]:
                            ready.append(pending[dep])
            except Exception as exc:  # pragma: no cover - error path
                ok = False
                stop_exc = exc
                for t in tasks:
                    t.cancel()
                await asyncio.gather(*tasks.keys(), return_exceptions=True)
                ready.clear()
                break

    total_ms = int((time.perf_counter() - start) * 1000)
    metrics["total_ms"] = total_ms

    stop_reason = None
    if stop_exc:
        if isinstance(stop_exc, BudgetError):
            stop_reason = "deadline"
        else:
            stop_reason = f"error:{type(stop_exc).__name__}"
    metrics["stop_reason"] = stop_reason

    artifacts.write_metrics(metrics)
    artifacts.write_timeline(timeline)

    summary = {
        "run_id": artifacts.run_id,
        "ok": ok and not stop_exc,
        "stop_reason": stop_reason,
        "totals": {
            "nodes": len(plan.graph),
            "tool_calls": metrics["tool_calls"],
            "cache_hits": metrics["cache_hits"],
            "retries": metrics["retries"],
            "total_ms": metrics["total_ms"],
        },
        "artifacts": artifacts.paths,
    }
    artifacts.write_summary(summary)
    return summary, stop_exc


# ---------------------------------------------------------------------------
def run_plan(
    plan: Plan,
    context: Dict,
    registry: Registry,
    impls: Dict[str, Callable[[dict], dict]] | None = None,
    runs_dir: str | Path = "runs",
    run_id: str | None = None,
    resume: bool = True,
    max_parallel: int | None = None,
    cache_read: bool = True,
    cache_write: bool = True,
    loader: ModelLoader | None = None,
    warmup: bool = True,
) -> Tuple[Dict, MicrographiaError | None]:
    """Synchronous wrapper around :func:`run_plan_async`."""

    return asyncio.run(
        run_plan_async(
            plan,
            context,
            registry,
            impls=impls,
            runs_dir=runs_dir,
            run_id=run_id,
            resume=resume,
            max_parallel=max_parallel,
            cache_read=cache_read,
            cache_write=cache_write,
            loader=loader,
            warmup=warmup,
        )
    )

