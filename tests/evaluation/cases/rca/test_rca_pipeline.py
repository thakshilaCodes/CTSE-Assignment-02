"""Integration tests for RCA pipeline and orchestrator state handoff."""

from mas.agents.rca.pipeline import run_rca_pipeline
from mas.core.orchestrator import run_rca_stage


def test_run_rca_pipeline_builds_hypotheses() -> None:
    ingest = "ERROR request failed status=503\nPaymentGatewayTimeout\nTraceback"
    correlation = "## Correlation findings\n- Class: `UPSTREAM_OUTAGE`\n- Confidence: `high`"
    report = run_rca_pipeline(
        ingest_findings=ingest,
        correlation_findings=correlation,
        use_ollama=False,
    )
    text = report.to_state_string()
    assert "RCA hypotheses" in text
    assert report.hypotheses
    assert report.incident_class == "UPSTREAM_OUTAGE"


def test_orchestrator_writes_rca_hypotheses_into_state() -> None:
    state = {
        "ingest_findings": "ERROR timeout upstream status=503",
        "correlation_findings": "- Class: `UPSTREAM_OUTAGE`\n- Confidence: `medium`",
    }
    out = run_rca_stage(state, use_ollama=False)
    assert "rca_hypotheses" in out
    assert "RCA hypotheses" in out["rca_hypotheses"]
    assert out["scratchpad"]["rca_incident_class"] == "UPSTREAM_OUTAGE"


def test_orchestrator_handles_missing_inputs() -> None:
    out = run_rca_stage({}, use_ollama=False)
    assert "rca_hypotheses" in out
    assert "Missing required state keys" in out["rca_hypotheses"]
