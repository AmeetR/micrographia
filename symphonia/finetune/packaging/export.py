from pathlib import Path
import hashlib, json, shutil

IGNORE = {".DS_Store"}


def bundle_sha(root: Path) -> str:
    files = []
    for p in root.rglob("*"):
        if p.is_file() and p.name not in IGNORE:
            files.append(p.relative_to(root).as_posix())
    files.sort()
    h = hashlib.sha256()
    for rel in files:
        h.update(rel.encode())
        h.update((root / rel).read_bytes())
    return h.hexdigest()


def run(exp: str, dest: Path, base_id="google/gemma-3-270m"):
    src = Path(f"runs/finetune/{exp}/checkpoints/adapter")
    dest = Path(dest)
    (dest / "adapter").mkdir(parents=True, exist_ok=True)
    for p in src.iterdir():
        shutil.copy2(p, dest / "adapter" / p.name)

    sha = bundle_sha(dest / "adapter")
    (dest / "checksums.json").write_text(json.dumps({"adapter_sha256": sha}, indent=2))

    manifest = {
        "name": "extractor_A",
        "version": "local",
        "kind": "inproc",
        "entrypoint": "examples.tools.extractor.factory",
        "input_schema": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
        "output_schema": {"type": "object"},
        "model": {
            "base_id": base_id,
            "adapter_uri": f"file://{(dest / 'adapter').resolve().as_posix()}/",
            "loader": "peft-lora",
            "quant": "4bit",
            "device_hint": "auto",
            "sha256": sha,
        },
    }
    (dest / "manifest.json").write_text(json.dumps(manifest, indent=2))
    (dest / "MODEL_CARD.md").write_text(f"# {exp}\n\nAdapter for {base_id}.\n")
    print(json.dumps({"export_done": str(dest)}))
    return dest
