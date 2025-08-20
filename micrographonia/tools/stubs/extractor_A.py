"""Stub mention extractor returning capitalised words."""

from micrographonia.runtime.tools import InprocTool


def run(payload: dict) -> dict:
    """Return a list of capitalised tokens from ``payload['text']``."""

    text: str = payload["text"]
    mentions = [w for w in text.split() if w and w[0].isupper()]
    return {"mentions": mentions}


def factory(manifest, loader, preloaded=None):  # pragma: no cover - simple stub
    return InprocTool(manifest, run)
