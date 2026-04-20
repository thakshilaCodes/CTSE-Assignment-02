"""Property-based tests for RCA stage: evidence handling (student: RCA owner)."""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from mas.agents.rca.pipeline import run_rca_pipeline


@settings(max_examples=15)
@given(
    noise=st.text(min_size=0, max_size=120),
)
def test_property_rca_output_contains_hypotheses_section(noise: str) -> None:
    ingest = f"ERROR timeout\n{noise}\n"
    correlation = "- Class: `UPSTREAM_OUTAGE`\n- Confidence: `high`"
    report = run_rca_pipeline(
        ingest_findings=ingest,
        correlation_findings=correlation,
        use_ollama=False,
    )
    text = report.to_state_string()
    assert "RCA hypotheses" in text
    assert "Ranked hypotheses" in text
