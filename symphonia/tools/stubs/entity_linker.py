"""Stub entity linker mapping mentions to lowercase identifiers."""

from symphonia.runtime.tools import InprocTool


def run(payload: dict) -> dict:
    """Link each mention to a lower-case entity identifier."""

    entities = [{"mention": m, "entity": m.lower()} for m in payload["mentions"]]
    return {"entities": entities}


def factory(manifest, loader, preloaded=None):  # pragma: no cover - simple stub
    return InprocTool(manifest, run)
