import json
from pathlib import Path

import pytest

from micrographonia.registry.registry import Registry
from micrographonia.runtime.errors import RegistryError

BASE = {
    "name": "tool",
    "version": "v1",
    "kind": "inproc",
    "entrypoint": "examples.tools.extractor.factory",
    "input_schema": {"type": "object"},
    "output_schema": {"type": "object"},
    "model": {
        "base_id": "b",
        "adapter_uri": "hf://repo/adapter/",
        "loader": "peft-lora",
    },
}


def _write_manifest(tmp_path: Path, data: dict) -> Path:
    path = tmp_path / "tool.v1.json"
    path.write_text(json.dumps(data))
    return path


def test_missing_base_id(tmp_path: Path):
    data = json.loads(json.dumps(BASE))
    del data["model"]["base_id"]
    _write_manifest(tmp_path, data)
    with pytest.raises(RegistryError):
        Registry(tmp_path)


def test_unknown_loader(tmp_path: Path):
    data = json.loads(json.dumps(BASE))
    data["model"]["loader"] = "bad-loader"
    _write_manifest(tmp_path, data)
    with pytest.raises(RegistryError):
        Registry(tmp_path)


def test_bad_scheme(tmp_path: Path):
    data = json.loads(json.dumps(BASE))
    data["model"]["adapter_uri"] = "ftp://server/path"
    _write_manifest(tmp_path, data)
    with pytest.raises(RegistryError):
        Registry(tmp_path)
