import json
import sys
import subprocess
from pathlib import Path

from tests.training.test_training_loop import _write_dataset


def test_registry_update(tmp_path: Path) -> None:
    data_path = tmp_path / "data.jsonl"
    _write_dataset(data_path)
    out_dir = tmp_path / "run"
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text(
        f"""
model:
  base: base-model
  adapter: lora
  output_dir: {out_dir}
data:
  teacher_model: dummy
  dataset: {data_path}
  split: [train, val]
training:
  epochs: 1
  batch_size: 2
logging:
  wandb_project: micrographonia
  save_every: 10
"""
    )
    subprocess.run(
        [sys.executable, "-m", "symphonia.sdk.cli", "train", "--config", str(cfg)],
        check=True,
    )
    registry_path = out_dir.parent / "models_registry.json"
    registry = json.loads(registry_path.read_text())
    assert any(entry["path"] == str(out_dir) for entry in registry)
    assert all("hash" in entry for entry in registry)
