"""Model loading utilities for in-process tools.

The :class:`ModelLoader` resolves model adapter URIs from a variety of
backends (Hugging Face, S3/GS buckets via ``fsspec`` or local files), verifies
their integrity and attaches them to a base model.  A small content addressed
cache avoids repeated downloads.  For test scenarios the loader understands the
special ``base_id="stub"`` which returns inexpensive dummy objects instead of
touching the real ``transformers`` stack.
"""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path
from typing import Tuple

import fsspec
try:  # pragma: no cover - imported lazily for tests
    from huggingface_hub import snapshot_download
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel
except Exception:  # pragma: no cover - tests may monkeypatch
    snapshot_download = None  # type: ignore
    AutoTokenizer = AutoModelForCausalLM = PeftModel = object  # type: ignore

from .errors import ModelLoadError


class ModelLoader:
    """Resolve model adapter URIs and attach adapters."""

    def __init__(self, cache_dir: Path | None = None) -> None:
        if cache_dir is None:
            cache_dir = Path.home() / ".micrographia" / "model-cache"
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    def _bundle_hash(self, directory: Path) -> str:
        """Return a combined SHA256 hash for all files under *directory*.

        Each file digest is computed separately and concatenated before hashing
        again.  This is stable across platforms and orderings.
        """

        digests = []
        for path in sorted(p for p in directory.rglob("*") if p.is_file()):
            digests.append(hashlib.sha256(path.read_bytes()).hexdigest())
        blob = "".join(digests)
        return hashlib.sha256(blob.encode()).hexdigest()

    # ------------------------------------------------------------------
    def _resolve_hf(self, uri: str, revision: str | None, dest: Path) -> Path:
        """Resolve a Hugging Face ``hf://`` URI to a local directory."""

        # uri format: hf://org/repo@rev/subdir/
        path = uri[len("hf://") :]
        parts = path.split("/")
        if len(parts) < 2:
            raise ModelLoadError("invalid hf uri")
        repo_part = "/".join(parts[:2])
        subpath = "/".join(parts[2:]) if len(parts) > 2 else ""
        if "@" in repo_part:
            repo_id, rev_part = repo_part.split("@", 1)
            revision = rev_part
        else:
            repo_id = repo_part
        repo_dir = Path(snapshot_download(repo_id, revision=revision, local_dir=self.cache_dir))
        return repo_dir / subpath if subpath else repo_dir

    # ------------------------------------------------------------------
    def _resolve_fs(self, uri: str, dest: Path) -> Path:
        """Download an adapter from a generic filesystem URI."""

        scheme, path = uri.split("://", 1)
        fs = fsspec.filesystem(scheme)
        fs.get(path, str(dest), recursive=True)
        return dest

    # ------------------------------------------------------------------
    def load(
        self,
        *,
        base_id: str,
        adapter_uri: str,
        revision: str | None = None,
        sha256: str | None = None,
        loader: str = "peft-lora",
        quant: str | None = None,
        device_hint: str = "auto",
    ) -> Tuple[AutoTokenizer, AutoModelForCausalLM]:
        """Resolve, verify, cache, and load a model."""
        if loader != "peft-lora":
            raise ModelLoadError(f"Unsupported loader: {loader}")

        if base_id == "stub":
            class Dummy:
                def eval(self):
                    pass

            return Dummy(), Dummy()

        key = sha256 or hashlib.sha256(f"{adapter_uri}@{revision}".encode()).hexdigest()
        local_dir = self.cache_dir / key
        if not local_dir.exists():
            tmp_dir = local_dir.with_suffix(".tmp")
            tmp_dir.mkdir(parents=True, exist_ok=True)
            if adapter_uri.startswith("hf://"):
                src = self._resolve_hf(adapter_uri, revision, tmp_dir)
                if src != tmp_dir:
                    shutil.copytree(src, tmp_dir, dirs_exist_ok=True)
            else:
                self._resolve_fs(adapter_uri, tmp_dir)
            tmp_dir.replace(local_dir)
        if sha256:
            digest = self._bundle_hash(local_dir)
            if digest != sha256:
                raise ModelLoadError("SHA mismatch")

        tokenizer = AutoTokenizer.from_pretrained(base_id)
        model = AutoModelForCausalLM.from_pretrained(
            base_id,
            device_map="auto" if device_hint == "auto" else None,
            load_in_4bit=quant == "4bit",
            load_in_8bit=quant == "8bit",
        )
        model = PeftModel.from_pretrained(model, str(local_dir))
        model.eval()
        return tokenizer, model
