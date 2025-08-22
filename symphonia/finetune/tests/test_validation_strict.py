from symphonia.finetune.common.validation import validate_record
from symphonia.finetune.data.plugins.notes_kg import plugin


def base_record() -> dict:
    """Return a minimal valid record for ``notes_kg``."""

    return {
        "id": "x",
        "source": "seed",
        "input": {"prompt": "hi"},
        "target": {"text": "x"},
        "meta": {"task": "notes_kg"},
    }


def test_missing_prompt_rejected() -> None:
    rec = base_record()
    rec["input"] = {}
    ok, err = validate_record(rec, plugin, require_json=False)
    assert not ok
    assert "prompt" in (err or "")


def test_missing_json_rejected_when_schema() -> None:
    rec = base_record()
    ok, err = validate_record(rec, plugin, require_json=True)
    assert not ok
    assert "target.json required" in (err or "")


def test_invalid_json_schema_rejected() -> None:
    rec = base_record()
    rec["target"] = {"json": {"foo": "bar"}}
    ok, err = validate_record(rec, plugin, require_json=True)
    assert not ok
    assert "target.json invalid" in (err or "")
