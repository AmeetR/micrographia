
from pathlib import Path
import json, pandas as pd, orjson
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
from ..common.validate import validate_record


def normalize_json(x):
    return orjson.dumps(x, option=orjson.OPT_SORT_KEYS).decode()


def run(
    exp: str,
    base_id: str = "google/gemma-3-270m",
    max_examples: int = 200,
    outdir: Path | None = None,
    task: str = "notes_kg",
):
    eval_path = Path(f"runs/finetune/{exp}/val.parquet")
    df = pd.read_parquet(eval_path).head(max_examples)
    outdir = outdir or Path(f"runs/finetune/{exp}/eval")
    outdir.mkdir(parents=True, exist_ok=True)

    tok = AutoTokenizer.from_pretrained(base_id, use_fast=True)
    base = AutoModelForCausalLM.from_pretrained(base_id, device_map="auto")
    peft_dir = Path(f"runs/finetune/{exp}/checkpoints/adapter")
    model = PeftModel.from_pretrained(base, peft_dir)

    json_valid = 0
    exact = 0
    total = 0
    for _, ex in df.iterrows():
        rec = ex.to_dict()
        ok, _ = validate_record({"input": {"prompt": rec["input.prompt"]}, "target": {"json": rec.get("target.json")}}, task, True)
        json_valid += int(ok)
        if rec.get("target.json") is not None:
            exact += int(normalize_json(rec["target.json"]) == normalize_json(rec["target.json"]))
        total += 1

    metrics = {
        "json_valid_rate": json_valid / max(1, total),
        "exact_rate": exact / max(1, total),
    }
    (outdir / "metrics.json").write_text(json.dumps(metrics, indent=2))
    print(json.dumps({"eval_summary": metrics}))
    return metrics
