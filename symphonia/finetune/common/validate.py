from jsonschema import Draft202012Validator
import json, importlib


with open("symphonia/finetune/data/schemas/interaction_v1.json") as f:
    BASE_SCHEMA = json.load(f)
BASE_VALIDATOR = Draft202012Validator(BASE_SCHEMA)


def validate_record(rec: dict, plugin_name: str, require_json: bool) -> tuple[bool, str | None]:
    try:
        BASE_VALIDATOR.validate(rec)
    except Exception as e:  # pragma: no cover - jsonschema detail
        return False, f"base:{e}"

    plugin = importlib.import_module(f"symphonia.finetune.data.plugins.{plugin_name}")
    schema = getattr(plugin, "schema", lambda: None)()
    if require_json and not rec.get("target", {}).get("json"):
        return False, "missing target.json"
    if schema and rec.get("target", {}).get("json") is not None:
        try:
            Draft202012Validator(schema).validate(rec["target"]["json"])
        except Exception as e:  # pragma: no cover - jsonschema detail
            return False, f"plugin:{e}"
    return True, None
