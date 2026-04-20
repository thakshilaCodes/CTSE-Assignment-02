# Correlation agent — how it works and how to run locally

This stage receives `ingest_findings` (text/markdown) and maps extracted signatures to known incident patterns.

## What correlation does

1. **Parse signatures** from ingest findings:
   - HTTP status markers (`HTTP_503`, etc.)
   - exception/error identifiers (`PaymentGatewayTimeout`, `DatabaseError`, ...)
   - high-signal keywords (`connection refused`, `traceback`, `upstream`, ...)
2. **Query known incidents** for each signature:
   - optional SQLite table `incidents`
   - built-in fallback catalog (so local runs still work without DB)
3. **Rank candidate incident class** using evidence strength:
   - source weighting (`sqlite` > fallback)
   - severity weighting
   - margin against runner-up class
4. **Generate deterministic correlation markdown** and save to:
   - `GlobalState["correlation_findings"]`
   - plus debug metadata in `GlobalState["scratchpad"]`

## Files

- `src/mas/agents/correlation/agent.py` — prompt + output hint
- `src/mas/agents/correlation/pipeline.py` — end-to-end correlation flow
- `src/mas/agents/correlation/report.py` — `CorrelationReport`
- `src/mas/tools/correlation/signatures.py` — signature extraction
- `src/mas/tools/correlation/query_incidents.py` — SQLite + fallback lookup
- `src/mas/core/orchestrator.py` — `run_correlation_stage(...)` state handoff

## Required input

Correlation expects `ingest_findings` to already exist (from ingest stage), e.g.:

```python
state["ingest_findings"] = "<ingest markdown/text>"
```

## Run locally

### A) Run correlation stage directly from a file

```bash
python -m mas.agents.correlation --ingest-file artifacts/outputs/ingest_findings.md
```

Optional incidents DB:

```bash
python -m mas.agents.correlation --ingest-file artifacts/outputs/ingest_findings.md --incident-db artifacts/incident_history.db
```

### B) Run via orchestrator handoff (recommended for pipeline integration)

```bash
python -m mas.core.orchestrator --ingest-file artifacts/outputs/ingest_findings.md
```

This prints full JSON state containing:

- `ingest_findings` (input)
- `correlation_findings` (new output)
- `scratchpad.correlation_signatures`
- `scratchpad.candidate_incident_class`
- `scratchpad.correlation_confidence`

## SQLite schema (optional)

If you use a DB, create table:

```sql
CREATE TABLE incidents (
  signature TEXT,
  incident_class TEXT,
  severity TEXT,
  title TEXT,
  resolution TEXT,
  last_seen TEXT
);
```

Only this table is required for current correlation implementation.
