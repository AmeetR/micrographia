import json
from pathlib import Path

from jsonschema import validate

from ..data.plugins.notes_kg import plugin


def load_schema(name: str) -> dict:
    path = Path(__file__).resolve().parents[1] / "data" / "schemas" / name
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def test_seed_examples_validate_against_schema() -> None:
    interaction_schema = load_schema("interaction_v1.json")
    structured_schema = plugin.schema()

    seeds = plugin.seed_examples()
    assert seeds, "plugin should return at least one seed example"

    for row in seeds:
        validate(row, interaction_schema)
        target_json = row.get("target", {}).get("json")
        if target_json is not None:
            validate(target_json, structured_schema)
