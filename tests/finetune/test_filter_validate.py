from symphonia.finetune.datagen import filter
import json, pandas as pd


def test_filter_drops_invalid(tmp_path):
    raw = tmp_path / "raw.jsonl"
    valid = '{"source":"seed","input":{"prompt":"ok"},"target":{"json":{"triples":[{"subject":"a","predicate":"b","object":"c"}]}},"meta":{"task":"notes_kg"}}'
    invalid = '{"source":"seed","input":{"prompt":"bad"},"target":{"json":{"foo":1}},"meta":{"task":"notes_kg"}}'
    raw.write_text(valid + "\n" + invalid)
    outdir = tmp_path / "out"
    report = filter.run(raw, outdir, task="notes_kg", min_json_valid=0.0)
    assert report["rows_raw"] == 2
    assert report["rows_after_filter"] == 1
    data_report = json.loads((outdir / "data_report.json").read_text())
    assert data_report["rows_after_filter"] == 1
    total = sum(pd.read_parquet(outdir / f"{s}.parquet").shape[0] for s in ["train", "val", "test"])
    assert total == 1
