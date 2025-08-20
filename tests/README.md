# Tests

Unit tests covering the runtime engine, registry, SDK helpers and tool integrations.

## Running
Execute the full suite:

```bash
pytest
```

For a quicker signal during development run a subset:

```bash
pytest tests/test_runtime.py::test_simple_plan
```

The tests double as executable specification and can be extended as new tools or runtime features are added.
