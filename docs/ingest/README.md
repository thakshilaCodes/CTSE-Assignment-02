# Ingest agent — how it works and how to run locally

This document describes the **Log Ingest** stage of the incident triage multi-agent system: what it does, which components it uses, and how you can run it on your machine.

## What ingest does

**Ingest** turns raw log files into structured material for the next agents (**correlation → rca → briefing**). It does **not** replace the rest of the pipeline; it produces **`ingest_findings`** (text) that downstream agents consume.

Rough flow:

1. **Resolve paths** — Only files under **allowed directories** can be read (see [Path safety](#path-safety)).
2. **Discover (optional)** — Scan allowed roots for likely log files (e.g. `*.log`, `*.out`, names containing `error`, `log`, …).
3. **Read tools** — For each file: metadata (size, time), **head** excerpt, **tail** excerpt (recent errors are often at the end).
4. **Normalize (heuristics)** — Strip ANSI codes, score lines by keywords (`ERROR`, `TRACEBACK`, …), aggregate counts.
5. **Build evidence markdown** — Deterministic sections: files reviewed, stats, signal lines, raw excerpts.
6. **Ollama (local SLM)** — By default, the same evidence is sent to **Ollama** with the ingest **system prompt** so a small local model writes a short **operator summary**. Tool output remains the source of truth; the model must not invent log lines that are not in the evidence.
7. **Output** — `IngestReport.to_state_string()` combines the Ollama summary (if any) with the full tool-backed markdown for `GlobalState["ingest_findings"]`.

If Ollama is unavailable or skipped, you still get the full **tool-backed** markdown only.

## Repository layout (ingest)

| Path | Role |
|------|------|
| `src/mas/agents/ingest/agent.py` | System prompt and output hints for the SLM |
| `src/mas/agents/ingest/ollama.py` | HTTP client for local Ollama (`/api/chat`, `/api/tags`) |
| `src/mas/agents/ingest/pipeline.py` | `run_ingest_pipeline(...)` orchestrates tools + Ollama |
| `src/mas/agents/ingest/report.py` | `IngestReport` and serialization for state |
| `src/mas/tools/ingest/` | Path allowlist, read head/tail, discover logs, normalize text |
| `tests/evaluation/cases/ingest/` | Tests (usually run with Ollama disabled) |

## Prerequisites

- **Python 3.11+** and project dependencies (see `pyproject.toml` / `requirements.txt`).
- **Ollama** installed and running on your machine for SLM summaries: [https://ollama.com](https://ollama.com)
- A model pulled locally, for example:

  ```bash
  ollama pull llama3:8b
  ```

  Match the tag to **`OLLAMA_MODEL`** (default `llama3:8b`).

## Environment variables

| Variable | Meaning |
|----------|---------|
| `OLLAMA_HOST` | Base URL of the Ollama API (default `http://127.0.0.1:11434`). |
| `OLLAMA_MODEL` | Model name as shown by `ollama list` (default `llama3:8b`). |
| `OLLAMA_SKIP` | Set to `1` (or `true`) to **disable** all Ollama calls (tests, CI, or offline debugging). |
| `OLLAMA_OPTIONS_JSON` | Optional JSON for generation options, e.g. `{"temperature":0.2,"num_predict":1024}`. |
| `MAS_INGEST_ALLOWED_ROOTS` | Comma-separated list of directories ingest may read. Paths are resolved; reads must stay **inside** these roots. If unset, sensible defaults under the current working directory are used (e.g. `artifacts/logs`, `logs`). |

Copy `config/.env.example` ideas into a local `.env` if your shell or tooling loads it; **do not commit secrets**.

## Path safety

Ingest **refuses** to read files outside **`MAS_INGEST_ALLOWED_ROOTS`** (after resolution). This limits damage if prompts ever asked for arbitrary paths. For local development, point the allowlist at folders that contain only logs you are willing to expose (e.g. `artifacts/logs`).

## How to run locally

### 1. Install dependencies

From the repository root:

```bash
pip install -e .
```

(or `pip install -r requirements.txt` if you prefer a flat install.)

### 2. Start Ollama

Ensure the Ollama daemon is listening (default port **11434**). Then verify from the project:

```bash
python -m mas.agents.ingest --check-ollama
```

Exit code **0** means the HTTP API responded; **1** means it did not (Ollama not running or wrong host).

### 3. Run ingest on sample logs

Example using the sample file in the repo:

```bash
python -m mas.agents.ingest artifacts/logs/sample_app.log
```

Discover logs under allowed roots (and merge with any paths you pass):

```bash
python -m mas.agents.ingest --discover
```

Evidence only (no SLM — useful if Ollama is down or for quick checks):

```bash
python -m mas.agents.ingest --no-ollama artifacts/logs/sample_app.log
```

### 4. Run from Python

```python
from mas.agents.ingest import run_ingest_pipeline

report = run_ingest_pipeline(
    file_paths=["artifacts/logs/sample_app.log"],
    discover=False,
    use_ollama=True,  # set False if OLLAMA_SKIP=1 or no Ollama
)
print(report.to_state_string())
```

### 5. Run tests

Tests normally avoid calling Ollama (`OLLAMA_SKIP` / `use_ollama=False`). From repo root:

```bash
python -m pytest tests/evaluation/cases/ingest -q
```

## Troubleshooting

| Issue | What to try |
|-------|-------------|
| `--check-ollama` fails | Start Ollama; confirm `OLLAMA_HOST` matches your setup (firewall, port). |
| Empty or “no log files” | Set `MAS_INGEST_ALLOWED_ROOTS` to the folder containing your logs, or run from the repo root so defaults include `artifacts/logs`. |
| No SLM section in output | Ollama unreachable or `OLLAMA_SKIP=1`; you should still see deterministic **Ingest findings** markdown. |
| Wrong or slow model | `ollama pull <tag>` and set `OLLAMA_MODEL` to that tag. |

## Related assignment criteria

- **Local SLM:** Ollama only; no paid cloud APIs for ingest.
- **Tools:** File read, discovery, normalization — implemented in `mas.tools.ingest`.
- **Observability:** `log_tool_invocation` and `log_agent_step` in `mas.core.observability` record tool usage and ingest steps.

For the full multi-agent orchestration (graph connecting ingest → correlation → …), see `src/mas/core/orchestrator.py` as your team wires LangGraph / CrewAI / AutoGen.
