# Examples

Sample datasets, plans, and scripts demonstrating how to use **Micrographia**.

## Why examples?
These snippets act as executable documentation and inspiration for building domain pipelines. Each example shows how tiny specialists combine to produce structured artifacts.

## Quick start
Run the smallest end-to-end example:

```bash
python run_hello.py
# ✅ Wrote 2 triples to examples/kg.json
```

## Running a plan
Use the CLI to execute a plan and context from the repository root:

```bash
python -m micrographonia.sdk.cli plan.run \
  --plan examples/manual_plans/notes.yml \
  --context examples/datasets/note.json \
  --registry registry/manifests
```

Modify the YAML plan or dataset to adapt this flow to your own domain.
