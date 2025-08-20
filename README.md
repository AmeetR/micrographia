# micrographonia

**Composable small models for structured reasoning.**

A toolkit for orchestrating **tiny specialists** (e.g., Gemma-270M fine-tunes) into **verifiable, domain-agnostic pipelines**. Turn free-form inputs into structured artifacts you can **execute, verify, and reuse**.

---

## Why micrographonia?

Large models are impressive — but they are:

- **Expensive** to run (memory + inference cost),
- **Opaque** in reasoning (hallucinations, uncheckable steps),
- **Monolithic** (hard to swap a part or verify each step).

**Small model paradigm** (e.g., Google’s new [Gemma 270M](https://developers.googleblog.com/en/introducing-gemma-3-270m/)) shifts the game:

- Train or distill **tiny, task-specific models** (extract triples, link entities, map relations, verify consistency).
- Each runs **cheaply on a single GPU or CPU**.
- Together, orchestrated in a plan, they can solve problems that a single giant model would handle — but with **greater control and transparency**.

We aim for:

- **Artifacts over answers**: output is triples, plans, verified structures — not just prose.
- **Composable orchestration**: one runtime, many interchangeable specialists.
- **Domain agnostic**: any domain (notes, biomedical papers, legal docs, financial reports) can use the same *plan IR* and *tool contracts*.
- **Scalable strategy**: start with stub services → replace each with Gemma-270M LoRAs → compose into full pipelines.

---

## What you get (final end state)

### The **North Star** (V3)

A system that:

1. **Accepts inputs**: text, tables, graphs, logs, or mixed.
2. Runs a **Plan IR** — a small DAG of tool calls (manual or agentic).
3. **Orchestrates N tiny specialists**:
   - extractors (raw → triples),
   - linkers (mention → entity),
   - mappers (relation → schema),
   - verifiers (consistency, type checks),
   - writers (to JSON/Neo4j/RDF).
4. Produces **verifiable artifacts** with provenance and confidence.
5. Provides a **CLI + SDK** to:
   - Run manual plans,
   - Use an agent to compose plans on the fly,
   - Evaluate correctness (faithfulness, exec-match),
   - Train/fine-tune specialists.

The result: an **ecosystem of small Gemma models** working together like microservices, forming an **agentic reasoning fabric**.

---

## Background: Small Models & Gemma

### What is Gemma?

Gemma is Google’s family of **lightweight open models** (newly including 270M parameters). Designed to run on commodity hardware, it makes it feasible to:

- Run **many parallel instances** cheaply,
- Fine-tune quickly with methods like **LoRA** or **QLoRA**,
- Specialize each copy for a **sub-task**.

### Why Small Specialists?

- **Efficiency**: one 270M model can run inference on a single 2080 GPU or even modern CPUs.
- **Parallelism**: spin up *ten different fine-tunes* for ten subtasks instead of one giant model.
- **Verifiability**: each specialist has a strict input/output schema. Failures are caught at the boundary.
- **Replaceability**: want a new linker? Drop in a new one. Everything else stays the same.
- **Transparency**: instead of “the model said so,” you see each artifact — triples, links, consistency checks.

---

## Example Use Case: Notes → Personal Knowledge Graph (PKG)

*(Domain-agnostic system; notes are just an illustrative case.)*

**Input (raw note):**

```
Met with Divya to discuss AI orchestration.
She suggested trying small Gemma models.
Follow up: Build a demo repo next week.
```

**Orchestrated plan:**

- Extract mentions + candidate triples,
- Link mentions to entities (Divya → Person:Divya),
- Map relations (discuss → rel:discussedTopic),
- Verify type consistency,
- Write to sandbox KG.

**Output (verifiable triples):**

```json
[
  ["Person:Divya","rel:discussedTopic","Concept:AI_orchestration"],
  ["User:Ameet","rel:followUp","Task:demo_repo_next_week"]
]
```

Later, replace “notes” with:

- Biomedical text → protein/gene interactions,
- Legal filings → case parties, precedents,
- Finance reports → company metrics, relationships,
- Incident logs → service dependencies and failure chains.

The plan stays the same, only the extractors/linkers differ.

---

## Repository Layout

```
micrographonia/
├─ README.md
├─ pyproject.toml
├─ micrographonia/
│  ├─ runtime/          # Plan engine (executes DAGs)
│  ├─ registry/         # Tool manifests (schemas, endpoints)
│  ├─ tools/            # Stub services (FastAPI, replace with Gemma fine-tunes)
│  ├─ sdk/              # CLI & schema definitions
│  └─ docs/             # background, plan IR spec, tutorials
└─ examples/
   ├─ manual_plans/     # Sample Plan IR YAMLs
   └─ datasets/         # Example inputs (notes, papers, logs)
```

---

## Core Concepts

### Plan IR (Intermediate Representation)

A domain-agnostic DAG of tool calls:

```yaml
version: "0.1"
graph:
  - id: extract
    tool: "extractor_A.v1"
    inputs: { text: "${context.text}" }
    out:    { triples: "$.triples", mentions: "$.mentions" }

  - id: link
    tool: "entity_linker.v1"
    needs: ["extract"]
    inputs: { mentions: "${extract.mentions}" }
    out: { links: "$.links" }

  - id: write
    tool: "kg_writer.v1"
    needs: ["link","extract"]
    inputs: { triples: [], namespace: "${context.namespace}" }
    out: { path: "$.path" }
```

Domain-agnostic: nothing here assumes “notes.” Could be medical abstracts, logs, etc.

### Tool Contracts

- Tools are strict JSON I/O services.
- Each has a manifest: endpoint, input schema, output schema.
- Runtime enforces compliance, catching hallucinations early.

---

## Getting Started

### Step 0.5 — Hello World (script only)

One note → One triple → JSON file.

```bash
python examples/run_hello.py
# ✅ Wrote 2 triples to examples/kg.json
```

### Step 1 — Minimal Orchestration (stub services + plan)

Spin up FastAPI stubs for extract/link/verify/write. Run a Plan IR YAML.
Output: JSON KG with provenance.

```bash
python -m micrographonia.sdk.cli plan.run \
  --plan examples/manual_plans/notes.yml \
  --context examples/datasets/note.json \
  --registry registry/manifests
```

Validate a plan without running it:

```bash
python -m micrographonia.sdk.cli plan.validate \
  --plan examples/manual_plans/notes.yml \
  --registry registry/manifests
```

### Tool Manifest (In‑Proc)

In‑process tools specify how their model should be loaded.  A manifest must
include an ``entrypoint`` (a dotted Python path) and a ``model`` block:

```json
{
  "name": "extractor_A",
  "version": "v2",
  "kind": "inproc",
  "entrypoint": "examples.tools.extractor.factory",
  "model": {
    "base_id": "google/gemma-3-270m",
    "adapter_uri": "hf://org/repo@rev/adapter/",
    "revision": "rev",            # optional for HF
    "sha256": "…",                 # optional integrity check
    "loader": "peft-lora",         # currently supported value
    "quant": "4bit",               # optional
    "device_hint": "auto"         # optional
  }
}
```

Supported ``adapter_uri`` schemes: ``hf://`` for Hugging Face, ``s3://`` or
``gs://`` for object storage and ``file://`` for local paths.  Providing a
``revision`` or ``sha256`` pins the artifact and guarantees reproducibility.

### Pre‑flight & ``plan.check-models``

Before executing any node, the runtime resolves and loads all referenced tools.
Use the CLI to dry‑run this resolution:

```bash
python -m micrographonia.sdk.cli plan.check-models \
  --plan examples/manual_plans/notes_inproc.yml \
  --registry registry/manifests
```

This command exits non‑zero on any missing or invalid model and mirrors the
pre‑flight step that happens automatically when running ``plan.run``.

### No central store needed

Micrographia remains stateless: manifests embed URIs and the
``ModelLoader`` uses ``huggingface_hub`` and ``fsspec`` to fetch adapters,
storing them in a local content‑addressed cache.  Swapping adapters or changing
revisions requires only updating the manifest.

---

## Roadmap

- **M0**: Stub services, runtime, registry, CLI.
- **M1**: Parallel scheduling, retries, budgets.
- **M2**: Swap stubs for Gemma-270M LoRAs (extract, link, map, verify).
- **M3**: Add agentic planner (Gemma micro-planner emits Plan IR).
- **M4**: Evaluation harness + graph UI.

---

## Benefits of this paradigm

- **Cheap + scalable**: Many Gemma-270M instances replace one giant model.
- **Trustable**: Every step produces a verifiable artifact.
- **Composable**: Swap tools, domains, or plans with no retraining of everything.
- **Portable**: Run on a single GPU, CPU cluster, or scaled cloud.
- **Extensible**: Add new tools (e.g., causal reasoning, forecasting) with strict contracts.

---

## Background & Related Work

micrographonia builds on ideas from several research threads:

- **Small model distillation** – work on compact yet capable models such as TinyLlama, Phi, and Google’s Gemma distillations shows that sub-billion parameter models can retain strong reasoning when specialized for tasks.
- **Multi-agent orchestration** – systems like AutoGPT, AI Legion, and other planner-executor frameworks inspire our approach of composing many focused agents into a cooperative pipeline.
- **Graph reasoning and knowledge capture** – projects like OpenIE, DeepDive, and graph databases (Neo4j, RDF stores) inform our emphasis on structured triples with provenance.

This project aims to unify these threads into a pragmatic toolkit for verifiable reasoning with small, composable models.

---

## License

MIT.

---

micrographonia = many small voices in harmony.
A system where dozens of tiny Gemma models, each weak alone, combine into structured, reliable reasoning.

