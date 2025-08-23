from pathlib import Path
import json, pandas as pd


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in Path(path).read_text().splitlines() if l.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with Path(path).open("w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def write_parquet(path: Path, rows: list[dict]) -> None:
    df = pd.json_normalize(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, compression="snappy", index=False)


def read_any(path: Path) -> list[dict]:
    p = Path(path)
    if p.suffix == ".jsonl":
        return read_jsonl(p)
    if p.suffix == ".parquet":
        return pd.read_parquet(p).to_dict("records")
    raise ValueError("unsupported input format")
