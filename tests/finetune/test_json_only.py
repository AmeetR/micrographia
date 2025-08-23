from symphonia.finetune.datagen.json_only import extract_first_json


def test_extract_first_json_fenced():
    text = "Here\n```json\n{\"a\":1}\n```\nnoise"
    ok, obj, err = extract_first_json(text)
    assert ok and obj == {"a": 1}
