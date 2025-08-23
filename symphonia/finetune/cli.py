import typer
from pathlib import Path
from .datagen.assemble import run as assemble_run
from .datagen.generate import run as generate_run
from .datagen.filter import run as filter_run
from .train.sft import run as train_run
from .evals.harness import run as eval_run
from .packaging.export import run as export_run

app = typer.Typer(help="Micrographia finetune CLI")

@app.command("datagen-assemble")
def datagen_assemble(in_path: Path, out: Path, task: str = "notes_kg"):
    assemble_run(in_path, out, plugin=task)

@app.command("datagen-generate")
def datagen_generate(
    task: str,
    seeds: Path,
    out: Path,
    provider: str = "oai",
    model: str = "gpt-4o-mini",
    json_only: bool = True,
    max_examples: int | None = None,
    qps: float = 2.0,
    strict: bool = False,
):
    generate_run(task, seeds, out, provider, model, json_only, max_examples, qps, strict)

@app.command("datagen-filter")
def datagen_filter(raw: Path, outdir: Path, task: str = "notes_kg", min_json_valid: float = 0.95):
    filter_run(raw, outdir, task, min_json_valid)

@app.command("train-sft")
def train_sft(config: Path, exp: str):
    train_run(config, exp)

@app.command("eval-run")
def do_eval(exp: str, base_id: str = "google/gemma-3-270m", max_examples: int = 200, task: str = "notes_kg"):
    eval_run(exp, base_id, max_examples, task=task)

@app.command("package-export")
def package_export(exp: str, dest: Path):
    export_run(exp, dest)

if __name__ == "__main__":
    app()
