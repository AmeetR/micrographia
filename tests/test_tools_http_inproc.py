from __future__ import annotations

import httpx
import pytest

from symphonia.registry.manifest import ToolManifest
from symphonia.runtime.errors import SchemaError, ToolCallError
from symphonia.runtime.tools import HttpTool, InprocTool


def test_inproc_tool_validation() -> None:
    manifest = ToolManifest(
        name="adder",
        version="v1",
        kind="inproc",
        input_schema={
            "type": "object",
            "required": ["a"],
            "properties": {"a": {"type": "integer"}},
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "required": ["b"],
            "properties": {"b": {"type": "integer"}},
            "additionalProperties": False,
        },
    )

    tool = InprocTool(manifest, lambda p: {"b": p["a"] + 1})
    assert tool.invoke({"a": 1}) == {"b": 2}
    with pytest.raises(SchemaError):
        tool.invoke({"a": "x"})
    bad_tool = InprocTool(manifest, lambda p: {})
    with pytest.raises(SchemaError):
        bad_tool.invoke({"a": 1})


def test_http_tool(monkeypatch: pytest.MonkeyPatch) -> None:
    manifest = ToolManifest(
        name="remote",
        version="v1",
        kind="http",
        endpoint="http://test/tool",
        input_schema={"type": "object", "properties": {}, "additionalProperties": True},
        output_schema={
            "type": "object",
            "required": ["x"],
            "properties": {"x": {"type": "integer"}},
            "additionalProperties": False,
        },
    )
    tool = HttpTool(manifest)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"x": 5})

    transport = httpx.MockTransport(handler)

    def fake_post(url: str, json: dict, timeout: float | None = None) -> httpx.Response:
        client = httpx.Client(transport=transport)
        return client.post(url, json=json)

    monkeypatch.setattr(httpx, "post", fake_post)
    assert tool.invoke({}) == {"x": 5}

    def bad_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={})

    transport_bad = httpx.MockTransport(bad_handler)

    def bad_post(url: str, json: dict, timeout: float | None = None) -> httpx.Response:
        client = httpx.Client(transport=transport_bad)
        return client.post(url, json=json)

    monkeypatch.setattr(httpx, "post", bad_post)
    with pytest.raises(SchemaError):
        tool.invoke({})

    def err_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={})

    transport_err = httpx.MockTransport(err_handler)

    def err_post(url: str, json: dict, timeout: float | None = None) -> httpx.Response:
        client = httpx.Client(transport=transport_err)
        return client.post(url, json=json)

    monkeypatch.setattr(httpx, "post", err_post)
    with pytest.raises(ToolCallError):
        tool.invoke({})
