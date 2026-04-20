"""Property-based tests for briefing agent: report structure (student: briefing owner)."""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from mas.agents.briefing.pipeline import run_briefing_pipeline


@settings(max_examples=15)
@given(extra=st.text(min_size=0, max_size=100))
def test_property_briefing_has_required_sections(extra: str) -> None:
    ingest = f"ERROR payment timeout 503\n{extra}"
    correlation = "- Class: `UPSTREAM_OUTAGE`\n- Confidence: `high`"
    rca = "#### 1. Upstream dependency outage\n- Check upstream health"
    report = run_briefing_pipeline(
        ingest_findings=ingest,
        correlation_findings=correlation,
        rca_hypotheses=rca,
        use_ollama=False,
    )
    md = report.to_state_string()
    for needle in ("# ", "Severity", "Summary", "Mitigations", "Follow-up"):
        assert needle in md
