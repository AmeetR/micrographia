import json
import os
from pathlib import Path

from micrographonia.core import run
from micrographonia.core import exit_codes
from micrographonia.core import constants


def write_plan(path: Path, nodes):
    plan = {"nodes": nodes}
    path.write_text(json.dumps(plan))
    return path


def write_registry(path: Path, content=None):
    data = content if content is not None else {}
    path.write_text(json.dumps(data))
    return path


class chdir:
    def __init__(self, path):
        self.path = path
        self.old = None

    def __enter__(self):
        self.old = os.getcwd()
        os.chdir(self.path)

    def __exit__(self, exc_type, exc, tb):
        os.chdir(self.old)


def test_success_exit_code(tmp_path):
    plan = write_plan(tmp_path / "plan.json", [{"name": "n1"}])
    registry = write_registry(tmp_path / "reg.json")
    with chdir(tmp_path):
        code = run(plan, registry, run_id="run-success")
        assert code == exit_codes.SUCCESS
        metrics = json.loads((tmp_path / constants.RUNS_DIR / "run-success" / constants.METRICS_FILE).read_text())
        assert metrics["stop_reason"] == constants.COMPLETED


def test_preflight_failure_exit_code(tmp_path):
    plan = write_plan(tmp_path / "plan.json", [{"name": "n1"}])
    registry = write_registry(tmp_path / "reg.json", {"bad": True})
    with chdir(tmp_path):
        code = run(plan, registry, run_id="run-preflight")
        assert code == exit_codes.PREFLIGHT_FAILURE
        metrics = json.loads((tmp_path / constants.RUNS_DIR / "run-preflight" / constants.METRICS_FILE).read_text())
        assert metrics["stop_reason"] == constants.PREFLIGHT_FAILED


def test_runtime_failure_exit_code(tmp_path):
    plan = write_plan(tmp_path / "plan.json", [{"name": "ok"}, {"name": "bad", "behavior": "fail"}])
    registry = write_registry(tmp_path / "reg.json")
    with chdir(tmp_path):
        code = run(plan, registry, run_id="run-runtime")
        assert code == exit_codes.RUNTIME_FAILURE
        metrics = json.loads((tmp_path / constants.RUNS_DIR / "run-runtime" / constants.METRICS_FILE).read_text())
        assert metrics["stop_reason"] == constants.RUNTIME_ERROR


def test_invalid_plan_exit_code(tmp_path):
    plan = tmp_path / "plan.json"
    plan.write_text("not json")
    registry = write_registry(tmp_path / "reg.json")
    with chdir(tmp_path):
        code = run(plan, registry, run_id="run-invalid")
        assert code == exit_codes.INVALID_PLAN
        metrics = json.loads((tmp_path / constants.RUNS_DIR / "run-invalid" / constants.METRICS_FILE).read_text())
        assert metrics["stop_reason"] == constants.INVALID_PLAN
