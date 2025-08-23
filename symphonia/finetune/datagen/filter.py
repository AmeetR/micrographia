
from pathlib import Path
import json
from ..common.identity import stable_id, split_for_id
from ..common.io import read_any, write_parquet
from ..common.validate import validate_record


def run(raw_path: Path, outdir: Path, task: str, min_json_valid: float = 0.95, drop_near_dupes: bool = False):
    rows = read_any(raw_path)
    out = []
    bad = 0
    good = 0
    seen = set()
    for r in rows:
        r["id"] = r.get("id") or stable_id(r)
        if r["id"] in seen:
            continue
        ok, err = validate_record(r, plugin_name=task, require_json=True)
        if not ok:
            bad += 1
            continue
        r["split"] = r.get("split") or split_for_id(r["id"])
        out.append(r)
        seen.add(r["id"])
        good += 1
    train = [x for x in out if x["split"] == "train"]
    val = [x for x in out if x["split"] == "val"]
    test = [x for x in out if x["split"] == "test"]
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    write_parquet(outdir / "train.parquet", train)
    write_parquet(outdir / "val.parquet", val)
    write_parquet(outdir / "test.parquet", test)
    report = {
        "rows_raw": len(rows),
        "rows_after_filter": len(out),
        "json_valid_rate": good / max(1, len(rows)),
        "split_sizes": {"train": len(train), "val": len(val), "test": len(test)},
    }
    (outdir / "data_report.json").write_text(json.dumps(report, indent=2))
    if report["json_valid_rate"] < min_json_valid:
        raise SystemExit(2)
    return report
