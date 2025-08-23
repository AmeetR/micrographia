from symphonia.finetune.datagen import assemble
import json, pandas as pd


def test_assemble_adds_id_split(tmp_path):
    inp = tmp_path / "in.jsonl"
    inp.write_text('{"input": {"prompt": "hi"}, "target": {"json": {}}}\n')
    out = tmp_path / "out.parquet"
    assemble.run(inp, out)
    assert out.exists()
    report = json.loads(out.with_suffix('.report.json').read_text())
    assert report["count"] == 1
    df = pd.read_parquet(out)
    assert "id" in df.columns and "split" in df.columns
