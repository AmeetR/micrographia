
from pathlib import Path
import json, time
from ..common.identity import stable_id
from ..common.io import read_any, write_jsonl
from .teacher_api import ask_teacher
from .json_only import extract_first_json


def run(
    task: str,
    seeds_path: Path,
    out_path: Path,
    provider: str,
    model: str,
    json_only: bool = True,
    max_examples: int | None = None,
    qps: float | None = 2.0,
    strict: bool = False,
) -> dict:
    seeds = read_any(seeds_path)
    rows = []
    valid = 0
    t0 = time.time()
    for i, rec in enumerate(seeds):
        if max_examples and i >= max_examples:
            break
        prompt = rec["input"]["prompt"]
        text = ask_teacher(provider, prompt, model, json_only)
        out = {"id": rec.get("id") or stable_id(rec), "input": rec["input"], "meta": rec.get("meta", {})}
        if json_only:
            ok, obj, _ = extract_first_json(text)
            out["target"] = {"json": obj} if ok else {"text": text}
            valid += int(ok)
        else:
            out["target"] = {"text": text}
        rows.append(out)
    write_jsonl(out_path, rows)
    report = {
        "count": len(rows),
        "json_valid": valid,
        "json_valid_rate": valid / max(1, len(rows)),
        "elapsed_s": round(time.time() - t0, 3),
    }
    Path(out_path).with_suffix(".report.json").write_text(json.dumps(report, indent=2))
    if strict and report["json_valid_rate"] < 0.9:
        raise SystemExit(2)
    return report
