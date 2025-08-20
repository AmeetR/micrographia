import json
from pathlib import Path

import json
import pytest

from micrographonia.runtime.preflight import preflight_build_tool_pool
from micrographonia.runtime.model_loader import ModelLoader
from micrographonia.registry.registry import Registry
from micrographonia.runtime.errors import EngineError, RegistryError
from micrographonia.sdk.plan_ir import Plan, Node


def _write_manifest(tmp_path: Path, data: dict) -> None:
    path = tmp_path / f"{data['name']}.{data['version']}.json"
    path.write_text(json.dumps(data))


BASE_MANIFEST = {
    "name": "t",
    "version": "v1",
    "kind": "inproc",
    "entrypoint": "not.a.module.factory",
    "input_schema": {"type": "object"},
    "output_schema": {"type": "object"},
    "model": {
        "base_id": "stub",
        "adapter_uri": "",  # filled in test
        "loader": "peft-lora",
    },
}


def test_bad_entrypoint(tmp_path: Path, monkeypatch):
    adapter_dir = tmp_path / "adapter"
    adapter_dir.mkdir()
    manifest = json.loads(json.dumps(BASE_MANIFEST))
    manifest["model"]["adapter_uri"] = f"file://{adapter_dir.as_posix()}"
    _write_manifest(tmp_path, manifest)
    reg = Registry(tmp_path)
    plan = Plan(version="0.1", graph=[Node(id="n", tool="t.v1", inputs={})])
    with pytest.raises(EngineError):
        preflight_build_tool_pool(plan, reg, loader=ModelLoader(), warmup=False)


def test_missing_model(tmp_path: Path):
    bad = dict(BASE_MANIFEST)
    bad["model"] = None
    _write_manifest(tmp_path, bad)
    with pytest.raises(RegistryError):
        Registry(tmp_path)
