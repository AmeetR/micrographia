# Examples

Sample datasets, plans, and scripts demonstrating how to use **Symphonia**.

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
python -m symphonia.sdk.cli plan.run \
  --plan examples/manual_plans/notes.yml \
  --context examples/datasets/note.json \
  --registry registry/manifests
```

Modify the YAML plan or dataset to adapt this flow to your own domain.

### In‑process tool example

The ``manual_plans/notes_inproc.yml`` plan demonstrates using an in‑process
tool with a pre‑loaded model.  Validate the model availability before running:

```bash
python -m symphonia.sdk.cli plan.check-models \
  --plan examples/manual_plans/notes_inproc.yml \
  --registry examples/registry/manifests \
  [--no-warmup]
```

Running ``plan.run`` on the same plan will implicitly perform the pre‑flight
check and reuse the cached model on subsequent runs.
