from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any, Dict, Iterable
from uuid import uuid4

from ..sdk.plan_ir import Plan


class RunArtifacts:
    """Helper for reading/writing run artifacts.

    The helper owns the on-disk directory structure for a run.  When a
    ``run_id`` is supplied the corresponding directory will be reused
    (allowing resumption); otherwise a new run identifier is generated.
    """

    def __init__(self, root: str | Path = "runs", run_id: str | None = None) -> None:
        self.root_base = Path(root)
        if run_id is None:
            run_id = uuid4().hex[:8]
        # Runs are grouped by date for easier browsing.  When resuming we
        # search for an existing directory with the supplied run_id.
        candidates: Iterable[Path] = self.root_base.glob(f"*/{run_id}")
        try:
            self.root = next(iter(candidates))
        except StopIteration:
            date_dir = _dt.date.today().isoformat()
            self.root = self.root_base / date_dir / run_id
        self.run_id = run_id

        self.nodes_dir = self.root / "nodes"
        self.output_dir = self.root / "outputs"
        self.root.mkdir(parents=True, exist_ok=True)
        self.nodes_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.paths: Dict[str, Any] = {"root": str(self.root), "nodes": {}}

    # ------------------------------------------------------------------
    def _write(self, path: Path, data: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)

    # ------------------------------------------------------------------
    def write_plan(self, plan: Plan) -> None:
        from dataclasses import asdict

        path = self.root / "plan.json"
        self._write(path, asdict(plan))
        self.paths["plan"] = str(path)

    def write_context(self, context: Dict[str, Any]) -> None:
        path = self.root / "context.json"
        self._write(path, context)
        self.paths["context"] = str(path)

    def write_node_request(self, node_id: str, tool: str, payload: Dict[str, Any]) -> None:
        path = self.nodes_dir / f"{node_id}.request.json"
        self._write(path, {"tool": tool, "payload": payload})
        self.paths["nodes"].setdefault(node_id, {})["request"] = str(path)

    def write_node_response(self, node_id: str, tool: str, data: Dict[str, Any], ms: int) -> None:
        path = self.nodes_dir / f"{node_id}.response.json"
        self._write(path, {"tool": tool, "data": data, "ms": ms})
        self.paths["nodes"].setdefault(node_id, {})["response"] = str(path)

    def write_node_error(self, node_id: str, message: str) -> None:
        path = self.nodes_dir / f"{node_id}.error.json"
        self._write(path, {"error": message})
        self.paths["nodes"].setdefault(node_id, {})["error"] = str(path)

    def write_metrics(self, metrics: Dict[str, Any]) -> None:
        path = self.root / "metrics.json"
        self._write(path, metrics)
        self.paths["metrics"] = str(path)

    # ------------------------------------------------------------------
    def write_timeline(self, timeline: Dict[str, Any]) -> None:
        path = self.root / "metrics.timeline.json"
        self._write(path, timeline)
        self.paths["timeline"] = str(path)

    # ------------------------------------------------------------------
    def write_run_info(self, info: Dict[str, Any]) -> None:
        path = self.root / "run.json"
        self._write(path, info)

    # ------------------------------------------------------------------
    def read_run_info(self) -> Dict[str, Any] | None:
        path = self.root / "run.json"
        if not path.exists():
            return None
        return json.loads(path.read_text())

    # ------------------------------------------------------------------
    def read_node_response(self, node_id: str) -> Dict[str, Any] | None:
        path = self.nodes_dir / f"{node_id}.response.json"
        if not path.exists():
            return None
        return json.loads(path.read_text())

    # ------------------------------------------------------------------
    def write_summary(self, summary: Dict[str, Any]) -> None:
        path = self.root / "summary.json"
        self._write(path, summary)
