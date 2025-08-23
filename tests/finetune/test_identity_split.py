from symphonia.finetune.common.identity import stable_id, split_for_id


def test_identity_split_deterministic():
    rec = {"input": {"prompt": "hello"}, "target": {"json": {"a": 1}}}
    id1 = stable_id(rec)
    id2 = stable_id(rec)
    assert id1 == id2
    assert split_for_id(id1) == split_for_id(id2)
