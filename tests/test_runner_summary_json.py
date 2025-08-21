import json
import os
from pathlib import Path

from micrographonia.core import run
from micrographonia.core import constants, exit_codes


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
        self.old = Path.cwd()
        os.chdir(self.path)

    def __exit__(self, exc_type, exc, tb):
        os.chdir(self.old)


def test_emit_summary_json(tmp_path, capsys):
    plan = write_plan(tmp_path / "plan.json", [{"name": "n1"}])
    registry = write_registry(tmp_path / "reg.json")
    with chdir(tmp_path):
        code = run(plan, registry, run_id="run-summary", emit_summary_json=True)
        assert code == exit_codes.SUCCESS
        metrics = json.loads((tmp_path / constants.RUNS_DIR / "run-summary" / constants.METRICS_FILE).read_text())
        out = capsys.readouterr().out.strip()
        summary = json.loads(out)
        assert summary["run_id"] == "run-summary"
        assert summary["exit_code"] == metrics["exit_code"]
        assert summary["stop_reason"] == metrics["stop_reason"]
