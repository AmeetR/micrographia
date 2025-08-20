import json
import types
import sys
from pathlib import Path

import pytest

from micrographonia.registry.registry import Registry
from micrographonia.runtime.engine import run_plan
from micrographonia.runtime.errors import ModelLoadError
from micrographonia.runtime.model_loader import ModelLoader
from micrographonia.sdk.plan_ir import Plan, Node
from micrographonia.runtime.constants import (
    LoaderType,
    AdapterScheme,
    STOP_REASON_PREFLIGHT,
)


class DummyTool:
    def __init__(self, manifest):
        self.manifest = manifest

    def invoke(self, payload, timeout_s=None):
        return {}


def factory(manifest, loader, preloaded=None):
    return DummyTool(manifest)

sys.modules["preflight_tool"] = types.ModuleType("preflight_tool")
sys.modules["preflight_tool"].factory = factory


def _write_manifest(tmp_path: Path):
    adapter_dir = tmp_path / "adapter"
    adapter_uri = f"{AdapterScheme.FILE.value}{adapter_dir.as_posix()}"
    data = {
        "name": "t",
        "version": "v1",
        "kind": "inproc",
        "entrypoint": "preflight_tool.factory",
        "input_schema": {"type": "object"},
        "output_schema": {"type": "object"},
        "model": {
            "base_id": "b",
            "adapter_uri": adapter_uri,
            "loader": LoaderType.PEFT_LORA.value,
            "sha256": "deadbeef",
        },
    }
    path = tmp_path / "t.v1.json"
    path.write_text(json.dumps(data))
    return adapter_dir


def test_preflight_error(tmp_path, monkeypatch):
    reg_dir = tmp_path / "reg"
    reg_dir.mkdir()
    adapter_dir = _write_manifest(reg_dir)
    adapter_dir.mkdir()
    reg = Registry(reg_dir)

    plan = Plan(version="0.1", graph=[Node(id="a", tool="t.v1", inputs={})])
    monkeypatch.setattr(
        "micrographonia.runtime.model_loader.AutoTokenizer",
        types.SimpleNamespace(from_pretrained=lambda *_a, **_k: "tok"),
    )
    monkeypatch.setattr(
        "micrographonia.runtime.model_loader.AutoModelForCausalLM",
        types.SimpleNamespace(from_pretrained=lambda *_a, **_k: object()),
    )
    monkeypatch.setattr(
        "micrographonia.runtime.model_loader.PeftModel",
        types.SimpleNamespace(from_pretrained=lambda base, dir: object()),
    )
    record, err = run_plan(plan, {}, reg, loader=ModelLoader(), warmup=False)
    assert isinstance(err, ModelLoadError)
    assert record["stop_reason"] == STOP_REASON_PREFLIGHT
    err_path = Path(record["artifacts"]["nodes"]["__preflight__"]["error"])
    assert err_path.exists()
    data = json.loads(err_path.read_text())
    assert data["class"] == "ModelLoadError"
