import json
import sys
import subprocess
from pathlib import Path

from tests.training.test_training_loop import _write_dataset


def test_eval_metrics(tmp_path: Path) -> None:
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
    metrics = json.loads((out_dir / "eval.json").read_text())
    for key in ["accuracy", "f1", "loss", "student_vs_teacher_agreement"]:
        assert key in metrics
        assert 0 <= metrics[key] <= 1
