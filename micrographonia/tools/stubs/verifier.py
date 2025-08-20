"""Stub verifier producing trivial subject-predicate-object triples."""


def run(payload: dict) -> dict:
    """Convert entities into ``is`` triples."""

    triples = [[e["entity"], "is", e["mention"]] for e in payload["entities"]]
    return {"triples": triples}
