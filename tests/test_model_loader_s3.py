import types

import fsspec
import pytest

from micrographonia.runtime.model_loader import ModelLoader
from micrographonia.runtime.errors import ModelLoadError
from micrographonia.runtime.constants import LoaderType, AdapterScheme


def test_s3_sha_mismatch(monkeypatch, tmp_path):
    fs = fsspec.filesystem("memory")
    fs.mkdirs("bucket/adapter")
    fs.open("bucket/adapter/a.txt", "wb").write(b"hello")

    orig_fs = fsspec.filesystem
    monkeypatch.setattr(
        fsspec, "filesystem", lambda protocol, **kw: fs if protocol == "s3" else orig_fs(protocol, **kw)
    )
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

    loader = ModelLoader(cache_dir=tmp_path / "cache")
    cfg = {
        "base_id": "b",
        "adapter_uri": f"{AdapterScheme.S3.value}bucket/adapter",
        "loader": LoaderType.PEFT_LORA.value,
        "sha256": "deadbeef",
    }
    with pytest.raises(ModelLoadError):
        loader.load(**cfg)
