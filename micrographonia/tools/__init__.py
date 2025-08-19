"""Collection of stub tool services.

Each tool is intended to be replaced by a small specialized model.
"""

from . import teachers

class BaseTool:
    """Base class for tool stubs."""

    name: str = "base_tool"

    def run(self, *args, **kwargs):  # pragma: no cover - stub
        """Execute the tool with given arguments."""
        # TODO: implement tool behavior
        return {}


__all__ = ["BaseTool", "teachers"]
