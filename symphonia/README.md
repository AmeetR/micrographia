# Symphonia Package

Core library code for **Symphonia**. It provides the building blocks that coordinate small model specialists.

## Modules
- `runtime/` – asynchronous engine that schedules tool calls with retries and caching.
- `registry/` – manifest loader that resolves tool contracts.
- `sdk/` – user-facing helpers and CLI entry points.
- `tools/` – stub implementations and interfaces for external services.

## Example
Load a plan and execute it with the runtime:

```python
from symphonia.registry import Registry
from symphonia.runtime.engine import run_plan
from symphonia.sdk.plan_ir import load_plan

plan = load_plan("examples/manual_plans/notes.yml")
registry = Registry("registry/manifests")
summary, err = run_plan(plan, {"namespace": "demo"}, registry)
```

This package is intended as a reference implementation; swap the stubs for real services or fine‑tuned models as your pipeline grows.
