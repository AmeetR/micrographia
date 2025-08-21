import json
import types
import sys

import httpx

from symphonia.registry.registry import Registry
from symphonia.runtime.engine import run_plan
from symphonia.runtime.model_loader import ModelLoader
from symphonia.sdk.plan_ir import Plan, Node
from symphonia.runtime.constants import LoaderType, AdapterScheme, STUB_BASE_ID


class DummyTool:
    def __init__(self, manifest):
        self.manifest = manifest

    def invoke(self, payload, timeout_s=None):
        return {"echo": payload}


def factory(manifest, loader, preloaded=None):
    return DummyTool(manifest)

sys.modules["dummy_tool"] = types.ModuleType("dummy_tool")
sys.modules["dummy_tool"].factory = factory


def _write_manifest(path, data):
    path.write_text(json.dumps(data))


def test_mixed_plan(tmp_path, monkeypatch):
    reg_dir = tmp_path / "reg"
    reg_dir.mkdir()
    adapter_dir = reg_dir / "adapter"
    adapter_dir.mkdir()
    _write_manifest(
        reg_dir / "t.v1.json",
        {
            "name": "t",
            "version": "v1",
            "kind": "inproc",
            "entrypoint": "dummy_tool.factory",
            "input_schema": {"type": "object"},
            "output_schema": {"type": "object"},
            "model": {
                "base_id": STUB_BASE_ID,
                "adapter_uri": f"{AdapterScheme.FILE.value}{adapter_dir.as_posix()}",
                "loader": LoaderType.PEFT_LORA.value,
            },
        },
    )
    _write_manifest(
        reg_dir / "h.v1.json",
        {
            "name": "h",
            "version": "v1",
            "kind": "http",
            "endpoint": "http://server/tool",
            "input_schema": {"type": "object"},
            "output_schema": {"type": "object"},
        },
    )

    reg = Registry(reg_dir)

    def fake_post(url, json=None, timeout=None):
        class Resp:
            status_code = 200

            def json(self):
                return {"echo": json}

        return Resp()

    monkeypatch.setattr(httpx, "post", fake_post)

    plan = Plan(
        version="0.1",
        graph=[
            Node(id="a", tool="t.v1", inputs={}),
            Node(id="b", tool="h.v1", inputs={}),
        ],
    )
    record, err = run_plan(plan, {}, reg, loader=ModelLoader(), warmup=False)
    assert err is None
    assert record["totals"]["tool_calls"] == 2
