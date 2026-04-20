# CTSE Assignment 2 - Multi-Agent Incident Pipeline

This repository implements a **local, zero-cost Multi-Agent System (MAS)** for incident triage.
Given raw application logs, the system automatically produces an operator-ready incident briefing.

The pipeline is:

1. **Ingest** -> collect and normalize log evidence  
2. **Correlation** -> map evidence to known incident patterns/history  
3. **RCA** -> generate ranked root-cause hypotheses and validation checks  
4. **Briefing** -> produce final incident report for operations teams

## What each agent does

### Ingest agent
- Reads log files (head/tail), discovers logs under allowlisted paths.
- Extracts high-signal lines (`ERROR`, `TRACEBACK`, timeouts, status codes).
- Produces `ingest_findings` in shared global state.

### Correlation agent
- Parses signatures from ingest output (`HTTP_503`, exception names, keywords).
- Queries incident knowledge in **PostgreSQL first**, then SQLite, then fallback catalog.
- Produces `correlation_findings` with candidate incident class and confidence.

### RCA agent
- Combines ingest and correlation evidence.
- Builds ranked hypotheses with supporting evidence + disproof checks.
- Produces `rca_hypotheses` for downstream reporting.

### Briefing agent
- Converts all prior outputs into a fixed markdown report:
  - Severity
  - User impact
  - Likely root cause
  - Immediate mitigations
  - Follow-up checks
- Produces `briefing_markdown` (final output).

## How orchestration/routing works

- **LangGraph** is used for orchestration and routing between stages.
- Shared state is managed through `GlobalState` keys:
  - `ingest_findings`
  - `correlation_findings`
  - `rca_hypotheses`
  - `briefing_markdown`
  - `scratchpad` (metadata and diagnostics)
- Routing graph (default):
  - `ingest -> correlation -> rca -> briefing`
- A custom sequential fallback also exists for debugging, but default runtime uses LangGraph.

## Technologies used

- **Python 3.11/3.12** - core implementation
- **LangGraph** - multi-agent orchestration and state routing
- **Ollama** - local SLM inference (optional refinement in stages)
- **PostgreSQL (pgAdmin4)** - incident knowledge store for correlation
- **SQLite** - optional local fallback DB
- **pytest / Hypothesis** - automated tests and property-based evaluation
- **httpx / psycopg** - API and PostgreSQL connectivity

## Observability (LLMOps / AgentOps)

The assignment requires logging/tracing of **agent steps**, **tool calls**, and **short output previews**.

Implementation: `src/mas/core/observability.py`

- `log_agent_step(agent_name, payload)` — each stage records structured metadata (e.g. ingest file counts, correlation signatures).
- `log_tool_invocation(tool_name, arguments, result_preview)` — each tool call records arguments and a bounded result snippet (up to 2000 chars).

**How to see traces in the console**

Run the pipeline; logging is configured automatically when you use `run_pipeline.py`:

```bash
python run_pipeline.py artifacts/logs/sample_app.log --no-ollama
```

You should see lines like `INFO [mas] tool=...` and `INFO [mas] agent=...` on stderr.

**How to save traces to a file**

PowerShell:

```powershell
$env:MAS_LOG_FILE="artifacts/logs/mas_trace.log"
python run_pipeline.py artifacts/logs/sample_app.log --no-ollama
```

Then open `artifacts/logs/mas_trace.log` for a full run audit trail.

## Run full pipeline

From repo root (activate your venv first if you use one):

```bash
python run_pipeline.py artifacts/logs/sample_app.log --no-ollama
```

`run_pipeline.py` uses LangGraph by default. To force custom sequential fallback:

```bash
python run_pipeline.py artifacts/logs/sample_app.log --no-ollama --orchestrator custom
```

With Ollama enabled (if running locally):

```bash
python run_pipeline.py artifacts/logs/sample_app.log
```

Discover logs automatically:

```bash
python run_pipeline.py --discover --no-ollama
```

## Outputs

The runner saves stage outputs to `artifacts/outputs/`:

- `ingest_findings.md`
- `correlation_findings.md`
- `rca_hypotheses.md`
- `briefing_markdown.md`
- `pipeline_state.json`

## Check local services (Ollama + PostgreSQL)

Use the helper script:

```bash
python check_services.py
```

It verifies:

- Ollama API reachability (`/api/tags`)
- PostgreSQL connection + `public.incidents` table presence

If Postgres fails with missing env vars, set them in PowerShell (same terminal session):

```powershell
$env:PGHOST="localhost"
$env:PGPORT="5432"
$env:PGDATABASE="ctse_incidents"
$env:PGUSER="postgres"
$env:PGPASSWORD="your_password"
```

Then run again:

```bash
python check_services.py
```

## Run agent by agent

You can run each stage manually and pass outputs to the next stage.

### 1) Ingest

```bash
python -m mas.agents.ingest artifacts/logs/sample_app.log --no-ollama > artifacts/outputs/ingest_findings.md
```

### 2) Correlation

```bash
python -m mas.agents.correlation --ingest-file artifacts/outputs/ingest_findings.md > artifacts/outputs/correlation_findings.md
```

Optional SQLite incidents DB:

```bash
python -m mas.agents.correlation --ingest-file artifacts/outputs/ingest_findings.md --incident-db artifacts/incident_history.db > artifacts/outputs/correlation_findings.md
```

Optional PostgreSQL incidents DB (pgAdmin4)

Correlation now checks PostgreSQL first (if `PG*` env vars are set), then SQLite (`--incident-db`), then fallback catalog.

1. Create table in pgAdmin Query Tool:

```sql
CREATE TABLE IF NOT EXISTS incidents (
    id SERIAL PRIMARY KEY,
    signature TEXT NOT NULL,
    incident_class TEXT NOT NULL,
    severity TEXT NOT NULL,
    title TEXT NOT NULL,
    resolution TEXT NOT NULL,
    last_seen TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_incidents_signature ON incidents (LOWER(signature));
CREATE INDEX IF NOT EXISTS idx_incidents_class ON incidents (LOWER(incident_class));
```

2. Insert sample rows:

```sql
INSERT INTO incidents (signature, incident_class, severity, title, resolution, last_seen)
VALUES
('HTTP_503', 'UPSTREAM_OUTAGE', 'high', 'Dependency service unavailable', 'Retry with backoff and check upstream health.', NOW()),
('PaymentGatewayTimeout', 'PAYMENT_GATEWAY_TIMEOUT', 'high', 'Payment gateway timeout spike', 'Increase timeout and verify provider latency.', NOW()),
('connection refused', 'DB_CONNECTIVITY', 'critical', 'Database connection refused', 'Check DB process/firewall/connection string.', NOW());
```

3. Set env vars before running correlation:

```powershell
$env:PGHOST="localhost"
$env:PGPORT="5432"
$env:PGDATABASE="ctse_incidents"
$env:PGUSER="postgres"
$env:PGPASSWORD="your_password"
```

4. Run correlation normally (it will use PostgreSQL automatically):

```bash
python -m mas.agents.correlation --ingest-file artifacts/outputs/ingest_findings.md > artifacts/outputs/correlation_findings.md
```

### 3) RCA

```bash
python -m mas.agents.rca --ingest-file artifacts/outputs/ingest_findings.md --correlation-file artifacts/outputs/correlation_findings.md --no-ollama > artifacts/outputs/rca_hypotheses.md
```

### 4) Briefing

```bash
python -m mas.agents.briefing --ingest-file artifacts/outputs/ingest_findings.md --correlation-file artifacts/outputs/correlation_findings.md --rca-file artifacts/outputs/rca_hypotheses.md --no-ollama > artifacts/outputs/briefing_markdown.md
```

### Optional: run via orchestrator stage handoff

```bash
python -m mas.core.orchestrator artifacts/logs/sample_app.log --run-correlation --run-rca --run-briefing --no-ollama > artifacts/outputs/pipeline_state.json
```

Use LangGraph explicitly in orchestrator CLI:

```bash
python -m mas.core.orchestrator artifacts/logs/sample_app.log --orchestrator langgraph --no-ollama > artifacts/outputs/pipeline_state.json
```

## Automated evaluation (unified harness)

The group-owned harness runs **property-based tests**, **per-agent evaluation cases**, **security checks**, and an optional **LLM-as-judge** (Ollama) when available.

**Run the full evaluation suite**

```bash
python -m pytest tests/evaluation -v
```

**Or use the harness entry point** (defaults to `pytest tests/evaluation -v`):

```bash
python -m mas.evaluation.harness
```

Pass through pytest arguments, for example:

```bash
python -m mas.evaluation.harness tests/evaluation/cases/ingest -q
```

**LLM judge (optional)**

If Ollama is not running, judge-related tests use a deterministic fallback. To skip live Ollama calls entirely:

```powershell
$env:OLLAMA_SKIP="1"
python -m pytest tests/evaluation -q
```

## Notes

- Use `--no-ollama` for fully offline/deterministic runs.
- For Ollama runs, configure `OLLAMA_HOST` and `OLLAMA_MODEL` as needed.
- For PostgreSQL in correlation, install dependencies from `requirements.txt` and set `PG*` env vars.
