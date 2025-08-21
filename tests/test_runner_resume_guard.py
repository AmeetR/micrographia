import json
import os
from pathlib import Path

from symphonia.core import run
from symphonia.core import constants, exit_codes


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


def test_resume_mismatch_writes_resume_json(tmp_path):
    plan1 = write_plan(tmp_path / "plan.json", [{"name": "n1"}])
    registry = write_registry(tmp_path / "reg.json")
    with chdir(tmp_path):
        assert run(plan1, registry, run_id="orig") == exit_codes.SUCCESS
    # modify plan to trigger mismatch
    plan2 = write_plan(tmp_path / "plan.json", [{"name": "n2"}])
    with chdir(tmp_path):
        code = run(plan2, registry, resume_run_id="orig")
        assert code == exit_codes.PLAN_MISMATCH
        resume_data = json.loads((tmp_path / constants.RUNS_DIR / "orig" / "resume.json").read_text())
        assert resume_data["requested_run_id"] == "orig"
        assert "existing_plan_hash" in resume_data
        assert "new_plan_hash" in resume_data
