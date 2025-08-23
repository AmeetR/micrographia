from pathlib import Path

import pytest

from symphonia.training.train import Config, load_config, ConfigError


def test_config_loader_valid(tmp_path: Path) -> None:
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text(
        """
model:
  base: base-model
  adapter: lora
  output_dir: out
data:
  teacher_model: dummy
  dataset: data.jsonl
  split: [train, val]
training:
  epochs: 1
  batch_size: 2
logging:
  wandb_project: micrographonia
  save_every: 10
"""
    )
    c = load_config(cfg)
    assert isinstance(c, Config)
    assert c.model["base"] == "base-model"


def test_config_loader_invalid(tmp_path: Path) -> None:
    cfg = tmp_path / "bad.yaml"
    cfg.write_text("model: []: bad")
    with pytest.raises(ConfigError):
        load_config(cfg)
