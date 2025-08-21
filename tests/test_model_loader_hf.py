import types

import pytest

from symphonia.runtime.model_loader import ModelLoader
from symphonia.runtime.constants import LoaderType, AdapterScheme


class DummyModel:
    def eval(self):
        pass


def test_hf_cache(monkeypatch, tmp_path):
    """Ensure Hugging Face adapters are cached and not re-downloaded."""

    calls = {"download": 0}

    def fake_snapshot_download(repo_id, revision=None, local_dir=None):
        calls["download"] += 1
        d = tmp_path / "repo"
        (d / "adapter").mkdir(parents=True, exist_ok=True)
        (d / "adapter" / "a.txt").write_text("x")
        return str(d)

    monkeypatch.setattr(
        "symphonia.runtime.model_loader.snapshot_download", fake_snapshot_download
    )
    monkeypatch.setattr(
        "symphonia.runtime.model_loader.AutoTokenizer",
        types.SimpleNamespace(from_pretrained=lambda *_a, **_k: "tok"),
    )
    monkeypatch.setattr(
        "symphonia.runtime.model_loader.AutoModelForCausalLM",
        types.SimpleNamespace(from_pretrained=lambda *_a, **_k: DummyModel()),
    )
    monkeypatch.setattr(
        "symphonia.runtime.model_loader.PeftModel",
        types.SimpleNamespace(from_pretrained=lambda base, dir: DummyModel()),
    )

    loader = ModelLoader(cache_dir=tmp_path / "cache")
    cfg = {
        "base_id": "b",
        "adapter_uri": f"{AdapterScheme.HF.value}org/repo@rev/adapter/",
        "revision": "rev",
        "loader": LoaderType.PEFT_LORA.value,
    }
    loader.load(**cfg)
    assert calls["download"] == 1
    loader.load(**cfg)
    assert calls["download"] == 1


def test_quant_fallback(monkeypatch, tmp_path):
    """Quantisation gracefully falls back when bitsandbytes is missing."""

    def fake_from_pretrained(base_id, device_map=None, load_in_4bit=False, load_in_8bit=False):
        calls.append((load_in_4bit, load_in_8bit))
        if load_in_4bit or load_in_8bit:
            raise RuntimeError("bitsandbytes is not installed")
        return DummyModel()

    calls = []
    def fake_snapshot_download(repo_id, revision=None, local_dir=None):
        (tmp_path / "adapter").mkdir(parents=True, exist_ok=True)
        (tmp_path / "adapter" / "a.txt").write_text("x")
        return str(tmp_path)

    monkeypatch.setattr(
        "symphonia.runtime.model_loader.snapshot_download",
        fake_snapshot_download,
    )
    monkeypatch.setattr(
        "symphonia.runtime.model_loader.AutoTokenizer",
        types.SimpleNamespace(from_pretrained=lambda *_a, **_k: "tok"),
    )
    monkeypatch.setattr(
        "symphonia.runtime.model_loader.AutoModelForCausalLM",
        types.SimpleNamespace(from_pretrained=fake_from_pretrained),
    )
    monkeypatch.setattr(
        "symphonia.runtime.model_loader.PeftModel",
        types.SimpleNamespace(from_pretrained=lambda base, dir: DummyModel()),
    )

    loader = ModelLoader(cache_dir=tmp_path / "c")
    cfg = {
        "base_id": "b",
        "adapter_uri": f"{AdapterScheme.HF.value}org/repo@rev/adapter/",
        "revision": "rev",
        "loader": LoaderType.PEFT_LORA.value,
        "quant": "4bit",
    }
    with pytest.warns(RuntimeWarning):
        loader.load(**cfg)
    # first attempt with quantisation, second without
    assert calls == [(True, False), (False, False)]
