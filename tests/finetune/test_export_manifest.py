from symphonia.finetune.packaging import export
import json
from symphonia.finetune.packaging.export import bundle_sha


def test_export_manifest(tmp_path, monkeypatch):
    src = tmp_path / "runs/finetune/exp/checkpoints/adapter"
    src.mkdir(parents=True)
    (src / "adapter_model.bin").write_text("hi")
    dest = tmp_path / "package"
    monkeypatch.chdir(tmp_path)
    export.run("exp", dest)
    manifest = json.loads((dest / "manifest.json").read_text())
    assert manifest["model"]["adapter_uri"].endswith("/adapter/")
    sha = json.loads((dest / "checksums.json").read_text())["adapter_sha256"]
    (dest / "adapter" / ".DS_Store").write_text("x")
    assert bundle_sha(dest / "adapter") == sha
