from __future__ import annotations

import json
from pathlib import Path

import pytest

from symphonia.registry.registry import Registry
from symphonia.runtime.errors import RegistryError

REG_DIR = Path("registry/manifests")


def test_registry_summary() -> None:
    reg = Registry(REG_DIR)
    summary = reg.summary()
    assert "extractor_A.v1" in summary
    assert summary["kg_writer.v1"]["kind"] == "inproc"


def test_bad_manifest(tmp_path: Path) -> None:
    bad = {
        "name": "bad",
        "version": "v1",
        "kind": "http",
        "input_schema": {},
        "output_schema": {},
    }
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(bad))
    with pytest.raises(RegistryError):
        Registry(tmp_path)
