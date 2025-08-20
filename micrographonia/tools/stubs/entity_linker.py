"""Stub entity linker mapping mentions to lowercase identifiers."""


def run(payload: dict) -> dict:
    """Link each mention to a lower-case entity identifier."""

    entities = [{"mention": m, "entity": m.lower()} for m in payload["mentions"]]
    return {"entities": entities}
