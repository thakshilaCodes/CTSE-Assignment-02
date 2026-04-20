"""Integration tests for correlation pipeline and orchestrator state handoff."""

from __future__ import annotations

from mas.agents.correlation.pipeline import run_correlation_pipeline
from mas.core.orchestrator import run_correlation_stage


def test_run_correlation_pipeline_builds_findings() -> None:
    ingest_findings = """
    ## Ingest findings
    ERROR request failed path=/api/checkout status=503
    PaymentGatewayTimeout: upstream deadline exceeded
    """
    report = run_correlation_pipeline(ingest_findings=ingest_findings)
    text = report.to_state_string()
    assert "Correlation findings" in text
    assert report.signatures
    assert report.candidate_incident_class != ""


def test_orchestrator_writes_correlation_findings_into_state() -> None:
    state = {
        "ingest_findings": "ERROR request failed status=503\nPaymentGatewayTimeout",
    }
    out = run_correlation_stage(state, db_path=None)
    assert "correlation_findings" in out
    assert "Correlation findings" in out["correlation_findings"]
    assert "scratchpad" in out
    assert "correlation_signatures" in out["scratchpad"]


def test_orchestrator_handles_missing_ingest_findings() -> None:
    out = run_correlation_stage({}, db_path=None)
    assert "correlation_findings" in out
    assert "Missing `ingest_findings`" in out["correlation_findings"]
