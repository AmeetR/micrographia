from pathlib import Path
from collections import Counter
import json
from ..common.identity import stable_id, split_for_id
from ..common.io import read_any, write_parquet


def run(in_path: Path, out_path: Path, plugin: str = "notes_kg") -> Path:
    rows = read_any(in_path)
    out = []
    for r in rows:
        r["id"] = r.get("id") or stable_id(r)
        r["split"] = r.get("split") or split_for_id(r["id"])
        out.append(r)
    write_parquet(out_path, out)
    report = {"count": len(out), "splits": Counter([r["split"] for r in out])}
    Path(out_path).with_suffix(".report.json").write_text(json.dumps(report, indent=2))
    return out_path
