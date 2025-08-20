"""Filesystem-backed registry for resolving tool manifests."""

from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Any, Dict

from jsonschema import Draft7Validator

from .manifest import ToolManifest
from ..runtime.errors import RegistryError


class Registry:
    """Load and resolve tool manifests."""

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self._manifests: Dict[str, ToolManifest] = {}
        self._load()

    # ------------------------------------------------------------------
    def _load(self) -> None:
        if not self.root.exists():
            raise RegistryError(f"registry dir {self.root} does not exist")

        for path in self.root.glob("*.json"):
            data = json.loads(path.read_text())
            manifest = ToolManifest(**data)
            key = manifest.fqdn
            if key in self._manifests:
                raise RegistryError(f"duplicate manifest for {key}")
            if manifest.kind == "http":
                if not manifest.endpoint or not manifest.endpoint.startswith("http"):
                    raise RegistryError(f"http tool {key} missing valid endpoint")
            elif manifest.kind == "inproc":
                if not manifest.entrypoint:
                    raise RegistryError(f"inproc tool {key} missing entrypoint")
                model = manifest.model or {}
                if not model.get("base_id"):
                    raise RegistryError("manifest.model.base_id missing")
                if not model.get("adapter_uri"):
                    raise RegistryError("manifest.model.adapter_uri missing")
                loader = model.get("loader", "peft-lora")
                if loader not in {"peft-lora"}:
                    raise RegistryError(f"Unsupported loader: {loader}")
                uri = model.get("adapter_uri", "")
                if not any(uri.startswith(p) for p in ("hf://", "s3://", "gs://", "file://")):
                    raise RegistryError("Unsupported scheme for adapter_uri")
            Draft7Validator.check_schema(manifest.input_schema)
            Draft7Validator.check_schema(manifest.output_schema)
            self._manifests[key] = manifest

    # ------------------------------------------------------------------
    def resolve(self, fqdn: str) -> ToolManifest:
        try:
            return self._manifests[fqdn]
        except KeyError as exc:  # pragma: no cover - simple mapping
            raise RegistryError(f"unknown tool {fqdn}") from exc

    # ------------------------------------------------------------------
    def summary(self) -> Dict[str, Dict[str, Any]]:
        return {key: {"kind": m.kind} for key, m in self._manifests.items()}

    # ------------------------------------------------------------------
    def content_hash(self) -> str:
        """Return a deterministic hash of all loaded manifests.

        Used to guarantee that a resumed run is operating against the same
        registry contents as the original run.
        """

        parts = []
        for key in sorted(self._manifests):
            m = self._manifests[key]
            parts.append(
                json.dumps(
                    {
                        "name": m.name,
                        "version": m.version,
                        "kind": m.kind,
                        "input_schema": m.input_schema,
                        "output_schema": m.output_schema,
                        "endpoint": m.endpoint,
                        "entrypoint": m.entrypoint,
                        "model": m.model,
                        "tags": m.tags,
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                )
            )
        blob = "".join(parts)
        return hashlib.sha256(blob.encode()).hexdigest()

    # ------------------------------------------------------------------
    def health(self, base_url: str | None = None) -> Dict[str, bool]:
        import httpx

        results: Dict[str, bool] = {}
        for key, manifest in self._manifests.items():
            if manifest.kind == "http" and manifest.endpoint:
                url = manifest.endpoint
                if base_url:
                    url = url.replace("http://localhost", base_url.rstrip("/"))
                try:
                    resp = httpx.get(f"{url}/health", timeout=2.0)
                    results[key] = resp.status_code == 200
                except Exception:  # pragma: no cover - network issues
                    results[key] = False
            else:
                results[key] = True
        return results
