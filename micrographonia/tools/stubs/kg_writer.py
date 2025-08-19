import json
from pathlib import Path

def run(payload: dict) -> dict:
    path = Path(payload.get("path", "kg.json"))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump({"triples": payload["triples"]}, fh, indent=2)
    return {"path": str(path)}
