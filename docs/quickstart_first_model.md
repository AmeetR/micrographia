# Quickstart: Train Your First Model

This guide walks through the minimal end-to-end path for training a tiny specialist with Micrographia.
It assumes access to a single GPU (e.g. 2080, A10, or T4) and optional teacher APIs (OpenAI or Gemini).

```bash
pip install -e .[finetune]
```

## 1. Assemble deterministic splits
```bash
python -m micrographonia.finetune.cli datagen-assemble \
  --in examples/finetune/notes_kg/seeds_small.jsonl \
  --out runs/finetune/noteskg/seeds.split.parquet
```

## 2. (Optional) Expand with a teacher
```bash
python -m micrographonia.finetune.cli datagen-generate \
  --task notes_kg \
  --seeds runs/finetune/noteskg/seeds.split.parquet \
  --out runs/finetune/noteskg/raw.jsonl \
  --json-only --max-examples 2000 --qps 2 --budget-usd 2.50 --strict
```

## 3. Filter & assemble final parquet splits
```bash
python -m micrographonia.finetune.cli datagen-filter \
  --raw runs/finetune/noteskg/raw.jsonl \
  --outdir runs/finetune/noteskg \
  --min-json-valid 0.95 --drop-near-duplicates
```

## 4. Train a QLoRA adapter
```bash
python -m micrographonia.finetune.cli train-sft \
  --config symphonia/finetune/train/configs/sft_gemma270m_lora.yaml \
  --exp noteskg
```

## 5. Evaluate the adapter
```bash
python -m micrographonia.finetune.cli eval-run \
  --exp noteskg --config symphonia/finetune/evals/configs/eval_default.yaml
```

## 6. Package the adapter and manifest
```bash
python -m micrographonia.finetune.cli package-export \
  --exp noteskg --dest runs/finetune/noteskg/package
```

## 7. Orchestrate it in a plan
```bash
cp runs/finetune/noteskg/package/manifest.json examples/registry/manifests/extractor_A.local.json

python -m micrographonia.sdk.cli plan.check-models \
  --plan examples/manual_plans/notes_inproc.yml \
  --registry examples/registry/manifests

python -m micrographonia.sdk.cli plan.run \
  --plan examples/manual_plans/notes_inproc.yml \
  --registry examples/registry/manifests --emit-summary
```

Running all steps will yield a working in-process tool backed by your freshly trained adapter.

