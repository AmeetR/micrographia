# Runtime

Asynchronous execution engine orchestrating tool calls, caching, retries and state management for running Symphonia plans. Inspired by workflow schedulers and DAG executors, it focuses on reliability and transparency.

## Usage
```python
from symphonia.runtime.engine import run_plan
from symphonia.registry import Registry
from symphonia.sdk.plan_ir import load_plan

plan = load_plan("examples/manual_plans/notes.yml")
registry = Registry("registry/manifests")
summary, err = run_plan(plan, {"namespace": "demo"}, registry)
```

The runtime handles parallelism, backoff and resumable runs so experiments can start simple and grow into complex pipelines.
