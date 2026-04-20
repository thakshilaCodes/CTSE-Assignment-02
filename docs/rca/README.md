# RCA agent - how it works and how to run locally

This stage consumes:

- `ingest_findings`
- `correlation_findings`

and produces:

- `rca_hypotheses` (stored in global state)

## RCA flow

1. Build structured evidence from ingest + correlation text.
2. Extract error signals from ingest (timeout, traceback, 5xx, database/upstream keywords).
3. Parse correlation class/confidence from correlation findings.
4. Generate ranked hypotheses with:
   - likelihood
   - supporting evidence
   - disproof checks
5. Optionally refine the RCA summary with local Ollama (can be skipped).
6. Save output to `GlobalState["rca_hypotheses"]`.

## Main files

- `src/mas/agents/rca/pipeline.py`
- `src/mas/agents/rca/report.py`
- `src/mas/agents/rca/ollama.py`
- `src/mas/tools/rca/evidence_bundle.py`
- `src/mas/tools/rca/signals.py`
- `src/mas/core/orchestrator.py` (`run_rca_stage`)

## Run locally (agent CLI)

```bash
python -m mas.agents.rca --ingest-file artifacts/outputs/ingest_findings.md --correlation-file artifacts/outputs/correlation_findings.md --no-ollama
```

Use Ollama refinement (if Ollama is running):

```bash
python -m mas.agents.rca --ingest-file artifacts/outputs/ingest_findings.md --correlation-file artifacts/outputs/correlation_findings.md
```

## Run through orchestrator handoff

```bash
python -m mas.core.orchestrator --ingest-file artifacts/outputs/ingest_findings.md --correlation-file artifacts/outputs/correlation_findings.md --no-ollama
```

This prints JSON global state containing `rca_hypotheses` and RCA metadata in `scratchpad`.

## Expected state keys

- input: `ingest_findings`, `correlation_findings`
- output: `rca_hypotheses`
- scratchpad:
  - `rca_incident_class`
  - `rca_confidence`
  - `rca_hypothesis_count`
