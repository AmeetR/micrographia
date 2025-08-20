# Tools

Reference implementations and stub tools used by the runtime and tests. Real deployments would swap these stubs for calls to specialised models or services.

## Included stubs
- `extractor_A` – extracts candidate triples from text.
- `entity_linker` – maps mentions to canonical entities.
- `kg_writer` – writes triples to a JSON file.
- `verifier` – performs simple consistency checks.

Each stub runs as a small FastAPI server. You can try one directly:

```bash
python -m micrographonia.tools.stubs.extractor_A
# visit http://localhost:8001/docs
```

These services demonstrate the contract each tool must implement, acting as placeholders for future Gemma-based specialists.
