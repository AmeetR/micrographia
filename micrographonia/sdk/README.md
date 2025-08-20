# SDK

User-facing helpers and the command line interface for loading, validating and executing Micrographia plans. The SDK is the main entry point for developing and testing pipelines.

## CLI examples
Validate a plan:

```bash
python -m micrographonia.sdk.cli plan.validate \
  --plan examples/manual_plans/notes.yml \
  --registry registry/manifests
```

Execute a plan:

```bash
python -m micrographonia.sdk.cli plan.run \
  --plan examples/manual_plans/notes.yml \
  --context examples/datasets/note.json \
  --registry registry/manifests
```

The SDK also exposes Python helpers for loading plans, validating schemas and invoking the runtime programmatically.
