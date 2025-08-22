from symphonia.finetune.common.identity import stable_id, split_for_id


def test_splits_deterministic() -> None:
    rec = {"input": {"prompt": "hello"}, "target": {"text": "world"}}
    rec_id1 = stable_id(rec)
    rec_id2 = stable_id(rec)
    assert rec_id1 == rec_id2
    assert split_for_id(rec_id1) == split_for_id(rec_id2)
