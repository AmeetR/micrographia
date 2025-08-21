"""Registry of tool manifests.

This module will manage tool schemas and endpoints.
"""

class ToolRegistry:
    """Stub registry for tool metadata."""

    def register(self, name: str, manifest: dict) -> None:  # pragma: no cover - stub
        """Register a tool manifest."""
        # TODO: store manifest information
        _ = (name, manifest)

    def get(self, name: str) -> dict | None:  # pragma: no cover - stub
        """Retrieve a manifest by name."""
        # TODO: implement lookup
        return None
