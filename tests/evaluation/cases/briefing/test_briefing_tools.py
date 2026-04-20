"""Tests for briefing tools and markdown formatting."""

from mas.tools.briefing import (
    extract_incident_class,
    extract_top_actions,
    format_incident_markdown,
    infer_severity,
    summarize_user_impact,
)


def test_infer_severity() -> None:
    sev = infer_severity("ERROR 503 payment timeout", "Class: `UPSTREAM_OUTAGE`", "")
    assert sev in {"SEV1", "SEV2", "SEV3"}
    assert sev in {"SEV1", "SEV2"}


def test_extract_incident_class() -> None:
    cls = extract_incident_class("- Class: `DB_CONNECTIVITY`", "")
    assert cls == "DB_CONNECTIVITY"


def test_extract_top_actions_and_impact() -> None:
    rca = "- Check upstream health endpoint\n- Verify retry circuit breaker"
    actions = extract_top_actions(rca)
    impact = summarize_user_impact("payment checkout timeout")
    assert actions
    assert "Users may" in impact


def test_format_incident_markdown_sections() -> None:
    md = format_incident_markdown(
        title="Test Incident",
        severity="SEV2",
        incident_class="UPSTREAM_OUTAGE",
        user_impact="Users may fail checkout.",
        summary="Summary text.",
        likely_root_cause="Likely cause text.",
        actions=["Action A", "Action B"],
        follow_up_checks=["Check A"],
    )
    assert "# Test Incident" in md
    assert "## Incident Snapshot" in md
    assert "## Immediate Mitigations" in md
