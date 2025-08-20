"""Example in-process extractor tool.

This module demonstrates the required factory signature for in-process tools.
The implementation is intentionally trivial and merely echoes an empty list of
triples; real tools would apply a tokenizer and model to produce structured
output.
"""

from __future__ import annotations

from micrographonia.runtime.tools import Tool


class ExtractorTool(Tool):
    """Minimal example tool returning no triples."""

    def __init__(self, manifest):
        self.manifest = manifest

    def invoke(self, payload: dict, timeout_s: float | None = None) -> dict:  # pragma: no cover - example
        """Return an empty result regardless of *payload*.

        The ``# pragma: no cover`` markers keep coverage noise low as these
        examples serve purely as documentation.
        """

        return {"triples": []}


def factory(manifest, loader, preloaded=None):
    """Factory producing :class:`ExtractorTool` instances."""

    return ExtractorTool(manifest)
