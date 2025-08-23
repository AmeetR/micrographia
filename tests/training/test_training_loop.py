import json
import sys
import subprocess
from pathlib import Path


def _write_dataset(path: Path) -> None:
    lines = []
    for i in range(20):
        split = "train" if i < 15 else "val"
        inp = f"sample {i}"
        target = inp.upper()
        lines.append(json.dumps({"input": inp, "target": target, "split": split}))
    path.write_text("\n".join(lines))


def test_training_loop(tmp_path: Path) -> None:
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
    assert (out_dir / "adapter.bin").exists()
    assert (out_dir / "eval.json").exists()
