# Briefing agent - how it works and how to run locally

This stage generates the final operator-facing incident report.

## Inputs and output

Required state inputs:

- `ingest_findings`
- `correlation_findings`
- `rca_hypotheses`

Output state key:

- `briefing_markdown`

## Briefing flow

1. Infer severity from combined ingest/correlation/rca signals.
2. Extract incident class and top recommended actions.
3. Summarize user impact and likely root cause.
4. Render fixed markdown sections for operator readability.
5. Optionally refine wording using local Ollama (facts unchanged).
6. Save final text into `GlobalState["briefing_markdown"]`.

## Main files

- `src/mas/agents/briefing/pipeline.py`
- `src/mas/agents/briefing/report.py`
- `src/mas/agents/briefing/ollama.py`
- `src/mas/tools/briefing/signals.py`
- `src/mas/tools/briefing/format_briefing.py`
- `src/mas/core/orchestrator.py` (`run_briefing_stage`)

## Run locally (agent CLI)

```bash
python -m mas.agents.briefing --ingest-file artifacts/outputs/ingest_findings.md --correlation-file artifacts/outputs/correlation_findings.md --rca-file artifacts/outputs/rca_hypotheses.md --no-ollama
```

Use Ollama refinement (if Ollama is running):

```bash
python -m mas.agents.briefing --ingest-file artifacts/outputs/ingest_findings.md --correlation-file artifacts/outputs/correlation_findings.md --rca-file artifacts/outputs/rca_hypotheses.md
```

## Run through orchestrator handoff

```bash
python -m mas.core.orchestrator --ingest-file artifacts/outputs/ingest_findings.md --correlation-file artifacts/outputs/correlation_findings.md --rca-file artifacts/outputs/rca_hypotheses.md --no-ollama
```

This prints JSON with final `briefing_markdown` plus briefing metadata under `scratchpad`.
