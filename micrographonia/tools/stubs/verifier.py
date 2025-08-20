"""Stub verifier producing trivial subject-predicate-object triples."""

from micrographonia.runtime.tools import InprocTool


def run(payload: dict) -> dict:
    """Convert entities into ``is`` triples."""

    triples = [[e["entity"], "is", e["mention"]] for e in payload["entities"]]
    return {"triples": triples}


def factory(manifest, loader, preloaded=None):  # pragma: no cover - simple stub
    return InprocTool(manifest, run)
