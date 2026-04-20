"""Integration tests for briefing pipeline and orchestrator handoff."""

from mas.agents.briefing.pipeline import run_briefing_pipeline
from mas.core.orchestrator import run_briefing_stage


def test_run_briefing_pipeline_builds_markdown() -> None:
    report = run_briefing_pipeline(
        ingest_findings="ERROR timeout payment checkout status=503",
        correlation_findings="- Class: `UPSTREAM_OUTAGE`\n- Confidence: `high`",
        rca_hypotheses="#### 1. Upstream dependency outage or saturation\n- Check upstream health endpoint",
        use_ollama=False,
    )
    text = report.to_state_string()
    assert "Incident Snapshot" in text
    assert "Likely Root Cause" in text
    assert report.severity in {"SEV1", "SEV2", "SEV3"}


def test_orchestrator_writes_briefing_markdown_into_state() -> None:
    state = {
        "ingest_findings": "ERROR timeout payment checkout status=503",
        "correlation_findings": "- Class: `UPSTREAM_OUTAGE`\n- Confidence: `high`",
        "rca_hypotheses": "#### 1. Upstream dependency outage or saturation\n- Check upstream health endpoint",
    }
    out = run_briefing_stage(state, use_ollama=False)
    assert "briefing_markdown" in out
    assert "# " in out["briefing_markdown"]
    assert out["scratchpad"]["briefing_incident_class"] == "UPSTREAM_OUTAGE"


def test_orchestrator_handles_missing_inputs() -> None:
    out = run_briefing_stage({}, use_ollama=False)
    assert "briefing_markdown" in out
    assert "Missing required state keys" in out["briefing_markdown"]
