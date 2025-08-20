"""Pre-flight resolution of tools and model loading."""

from __future__ import annotations

import importlib
from typing import Dict

from .tools import HttpTool, Tool
from .model_loader import ModelLoader
from ..registry.registry import Registry
from ..sdk.plan_ir import Plan
from .errors import EngineError, ModelLoadError, RegistryError


def _import_entrypoint(path: str):
    """Import ``path`` and return the referenced factory callable."""

    module, func = path.rsplit(".", 1)
    mod = importlib.import_module(module)
    return getattr(mod, func)


def preflight_build_tool_pool(
    plan: Plan,
    registry: Registry,
    *,
    loader: ModelLoader,
    warmup: bool = True,
) -> Dict[str, Tool]:
    """Resolve all tools referenced by *plan* and return a tool pool."""

    tools = {node.tool for node in plan.graph}
    pool: Dict[str, Tool] = {}
    for namever in tools:
        manifest = registry.resolve(namever)
        if manifest.kind == "http":
            pool[namever] = HttpTool(manifest)
            continue
        if not manifest.model:
            raise RegistryError("manifest.model missing")
        try:
            tok, model = loader.load(**manifest.model)
        except ModelLoadError:
            raise
        factory = None
        try:
            factory = _import_entrypoint(manifest.entrypoint)
        except Exception as exc:
            raise EngineError(f"Cannot import {manifest.entrypoint}") from exc
        try:
            tool = factory(manifest, loader, preloaded=(tok, model))
        except Exception as exc:
            raise EngineError(f"Error instantiating tool {namever}") from exc
        pool[namever] = tool
        if warmup and hasattr(tool, "warmup"):
            try:
                tool.warmup()  # pragma: no cover - optional
            except Exception:
                pass
    return pool
