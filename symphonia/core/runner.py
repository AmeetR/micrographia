"""Simple workflow runner with deterministic outputs.

This implementation is intentionally lightweight and only aims to provide the
behaviour required for the unit tests in this kata.  It supports run
identifiers, hashing of the plan and registry files, exit codes and writing
metrics/timeline/log files.
"""
from __future__ import annotations

import json
import logging
import signal
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from . import constants
from . import exit_codes
from .utils import atomic_write, sha256_file


@dataclass
class NodeResult:
    name: str
    start: datetime
    end: datetime
    status: str


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat().replace("+00:00", "Z")


def _setup_logger(log_path: Path, verbose: bool) -> logging.Logger:
    logger = logging.getLogger(f"runner.{id(log_path)}")
    logger.setLevel(logging.INFO)
    logger.handlers = []
    fmt = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
    file_handler = logging.FileHandler(log_path)
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)
    if verbose:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(fmt)
        logger.addHandler(stream_handler)
    return logger


def load_plan(path: Path) -> Dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict) or "nodes" not in data or not isinstance(data["nodes"], list):
        raise ValueError("invalid plan structure")
    return data


def load_registry(path: Path) -> Dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("invalid registry structure")
    return data


def preflight_load(registry: Dict[str, Any]) -> None:
    # extremely small simulation: if registry contains key ``bad`` then fail
    if registry.get("bad"):
        raise RuntimeError("bad registry")


def execute_node(node: Dict[str, Any]) -> None:
    if node.get("behavior") == "fail":
        raise RuntimeError("node failed")
    # any other behaviour is treated as success


def run(
    plan_path: str | Path,
    registry_path: str | Path,
    run_id: str | None = None,
    resume_run_id: str | None = None,
    emit_summary_json: bool = False,
    verbose: bool = False,
) -> int:
    """Execute the plan and return an exit code."""

    plan_path = Path(plan_path)
    registry_path = Path(registry_path)

    if resume_run_id:
        run_id = resume_run_id
        resume = True
    else:
        resume = False
        run_id = run_id or str(uuid.uuid4())

    outdir = Path(constants.RUNS_DIR) / run_id
    outdir.mkdir(parents=True, exist_ok=True)

    plan_hash = sha256_file(plan_path)
    registry_hash = sha256_file(registry_path)

    meta = {
        "run_id": run_id,
        "plan_path": str(plan_path),
        "registry_path": str(registry_path),
        "plan_hash": plan_hash,
        "registry_hash": registry_hash,
        "created_at": _iso(_now()),
        "version": "symphonia@0.0-test",
    }
    meta_path = outdir / constants.META_FILE
    if not resume:
        atomic_write(meta_path, json.dumps(meta, indent=2))

    started_at = _now()
    logger = _setup_logger(outdir / constants.LOG_FILE, verbose)

    original_sigterm = signal.getsignal(signal.SIGTERM)

    def _sigterm_handler(signum, frame):
        raise KeyboardInterrupt()

    signal.signal(signal.SIGTERM, _sigterm_handler)

    timeline: List[NodeResult] = []
    plan_nodes_total = 0
    nodes_ok = 0

    def stop(code: int, reason: str, *, error: str | None = None, extra: Dict[str, Any] | None = None) -> int:
        ended = _now()
        duration_ms = int((ended - started_at).total_seconds() * 1000)
        metrics: Dict[str, Any] = {
            "ok": code == exit_codes.SUCCESS,
            "exit_code": code,
            "stop_reason": reason,
            "started_at": _iso(started_at),
            "ended_at": _iso(ended),
            "duration_ms": duration_ms,
            "plan_hash": plan_hash,
            "registry_hash": registry_hash,
            "totals": {
                "nodes_total": plan_nodes_total,
                "nodes_ok": nodes_ok,
                "nodes_failed": len([t for t in timeline if t.status == constants.STATUS_FAILED]),
                "tool_calls": 0,
                "retries": 0,
                "cache_hits": 0,
            },
        }
        if extra:
            metrics.update(extra)
        metrics_path = outdir / constants.METRICS_FILE
        atomic_write(metrics_path, json.dumps(metrics, indent=2))
        timeline_path = outdir / constants.TIMELINE_FILE
        tl = [
            {
                "node": t.name,
                "start": _iso(t.start),
                "end": _iso(t.end),
                "status": t.status,
            }
            for t in timeline
        ]
        atomic_write(timeline_path, json.dumps(tl, indent=2))
        if emit_summary_json:
            summary = {
                "run_id": run_id,
                "stop_reason": reason,
                "exit_code": code,
                "plan_hash": plan_hash,
                "registry_hash": registry_hash,
            }
            print(json.dumps(summary))
        signal.signal(signal.SIGTERM, original_sigterm)
        return code

    if resume:
        if meta_path.exists():
            try:
                existing = json.loads(meta_path.read_text())
            except Exception:
                existing = {}
            if existing.get("plan_hash") != plan_hash or existing.get("registry_hash") != registry_hash:
                resume_info = {
                    "requested_run_id": run_id,
                    "existing_plan_hash": existing.get("plan_hash"),
                    "existing_registry_hash": existing.get("registry_hash"),
                    "new_plan_hash": plan_hash,
                    "new_registry_hash": registry_hash,
                }
                atomic_write(outdir / "resume.json", json.dumps(resume_info, indent=2))
                return stop(
                    exit_codes.PLAN_MISMATCH,
                    constants.PLAN_MISMATCH,
                    extra={"resume": {
                        "requested_run_id": run_id,
                        "existing_plan_hash": existing.get("plan_hash"),
                        "existing_registry_hash": existing.get("registry_hash"),
                    }},
                )
            return stop(exit_codes.PLAN_MISMATCH, constants.RESUME_NOT_SUPPORTED)
        else:
            return stop(exit_codes.PLAN_MISMATCH, constants.PLAN_MISMATCH)

    try:
        plan = load_plan(plan_path)
        registry = load_registry(registry_path)
        plan_nodes_total = len(plan["nodes"])
    except Exception:
        return stop(exit_codes.INVALID_PLAN, constants.INVALID_PLAN)

    try:
        preflight_load(registry)
    except Exception as exc:
        logger.error("preflight failed: %s", exc)
        return stop(exit_codes.PREFLIGHT_FAILURE, constants.PREFLIGHT_FAILED)

    try:
        for node in plan["nodes"]:
            start = _now()
            try:
                execute_node(node)
                status = constants.STATUS_OK
                nodes_ok += 1
                logger.info("node %s completed", node.get("name"))
            except KeyboardInterrupt:
                status = constants.STATUS_FAILED
                end = _now()
                timeline.append(NodeResult(node.get("name", ""), start, end, status))
                raise
            except Exception as exc:
                status = constants.STATUS_FAILED
                end = _now()
                timeline.append(NodeResult(node.get("name", ""), start, end, status))
                logger.error("node %s failed: %s", node.get("name"), exc)
                raise
            else:
                end = _now()
                timeline.append(NodeResult(node.get("name", ""), start, end, status))
        return stop(exit_codes.SUCCESS, constants.COMPLETED)
    except KeyboardInterrupt:
        return stop(exit_codes.INTERRUPTED, constants.INTERRUPTED)
    except Exception:
        return stop(exit_codes.RUNTIME_FAILURE, constants.RUNTIME_ERROR)
