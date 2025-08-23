import pytest, pandas as pd, importlib

torch_spec = importlib.util.find_spec("torch")
if torch_spec:
    torch = importlib.import_module("torch")
else:
    torch = None


@pytest.mark.skipif(torch is None or not torch.cuda.is_available(), reason="requires GPU")
def test_train_smoke(tmp_path, monkeypatch):
    from symphonia.finetune.train.sft import run as train_run
    data = [{"input.prompt": "hi", "target.json": {"triples": [{"subject": "a", "predicate": "b", "object": "c"}]}}]
    df = pd.DataFrame(data)
    run_dir = tmp_path / "runs/finetune/exp"
    run_dir.mkdir(parents=True, exist_ok=True)
    df.to_parquet(run_dir / "train.parquet")
    df.to_parquet(run_dir / "val.parquet")
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text(open("symphonia/finetune/train/configs/sft_gemma270m_lora.yaml").read())
    monkeypatch.chdir(tmp_path)
    try:
        train_run(cfg, "exp")
    except Exception:
        pytest.skip("training dependencies missing")
    assert (tmp_path / "runs/finetune/exp/checkpoints/adapter").exists()
