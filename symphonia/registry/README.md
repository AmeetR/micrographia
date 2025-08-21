# Registry

Utilities for loading tool manifests from disk and resolving them during plan execution. The registry keeps tool definitions decoupled from code so pipelines can swap implementations easily.

## Manifest format
A manifest is a JSON document describing a tool endpoint and its schema:

```json
{
  "id": "extractor_A.v1",
  "url": "http://localhost:8000/extract",
  "inputs": { "text": "string" },
  "outputs": { "triples": "list" }
}
```

## Usage
```python
from symphonia.registry import Registry
registry = Registry("registry/manifests")
extract_manifest = registry.resolve("extractor_A.v1")
```
