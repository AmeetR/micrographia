# Tool Registry

JSON manifests describing the available tools. These are loaded by the `Registry` class and referenced by the example plans and tests.

## Structure
Each manifest lives in `manifests/` and follows the schema expected by the runtime. Adding a new tool simply involves dropping a new manifest file.

## Example
```json
{
  "id": "kg_writer.v1",
  "url": "http://localhost:8003/write",
  "inputs": { "triples": "list", "namespace": "string" },
  "outputs": { "path": "string" }
}
```

Use these manifests to swap in real implementations or to point to running services.
