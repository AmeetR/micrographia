"""Task plugin interface and registry.

Plugins supply task-specific utilities such as seed example generation,
structured output schemas and evaluation metrics. They are registered in
an in-memory registry for lookup by name.

Example
-------
Create and register a minimal plugin::

    from symphonia.finetune.data.plugins import base

    class EchoPlugin:
        name = "echo"
        def schema(self):
            return None
        def seed_examples(self, n=None):
            return [{"id": "1", ...}]
        def metrics(self, preds, refs):
            return {}

    base.register(EchoPlugin())
    plugin = base.get_plugin("echo")
    plugin.seed_examples()
"""
from __future__ import annotations
from typing import Protocol, runtime_checkable, Dict


@runtime_checkable
class TaskPlugin(Protocol):
    """Protocol that all task plugins must implement."""

    name: str

    def schema(self) -> dict | None:
        """Return JSON schema for ``target.json`` or ``None`` if unstructured."""

    def seed_examples(self, n: int | None = None) -> list[dict]:
        """Return a list of seed examples.

        ``n`` may limit the number of examples returned. Implementations may
        ignore the limit if they only have a fixed small set of examples.
        """

    def metrics(self, preds: list, refs: list) -> dict:
        """Compute task specific metrics given predictions and references."""


_PLUGINS: Dict[str, TaskPlugin] = {}


def register(plugin: TaskPlugin) -> None:
    """Register ``plugin`` in the global registry."""

    _PLUGINS[plugin.name] = plugin


def get_plugin(name: str) -> TaskPlugin:
    """Retrieve a plugin by ``name``.

    Raises ``KeyError`` if no plugin with that name is registered.
    """

    return _PLUGINS[name]
