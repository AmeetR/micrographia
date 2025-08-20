import types

from micrographonia.runtime.model_loader import ModelLoader


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
        "micrographonia.runtime.model_loader.snapshot_download", fake_snapshot_download
    )
    monkeypatch.setattr(
        "micrographonia.runtime.model_loader.AutoTokenizer",
        types.SimpleNamespace(from_pretrained=lambda *_a, **_k: "tok"),
    )
    monkeypatch.setattr(
        "micrographonia.runtime.model_loader.AutoModelForCausalLM",
        types.SimpleNamespace(from_pretrained=lambda *_a, **_k: DummyModel()),
    )
    monkeypatch.setattr(
        "micrographonia.runtime.model_loader.PeftModel",
        types.SimpleNamespace(from_pretrained=lambda base, dir: DummyModel()),
    )

    loader = ModelLoader(cache_dir=tmp_path / "cache")
    cfg = {
        "base_id": "b",
        "adapter_uri": "hf://org/repo@rev/adapter/",
        "revision": "rev",
        "loader": "peft-lora",
    }
    loader.load(**cfg)
    assert calls["download"] == 1
    loader.load(**cfg)
    assert calls["download"] == 1
