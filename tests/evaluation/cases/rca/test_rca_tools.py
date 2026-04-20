"""Tests for RCA tools."""

from mas.tools.rca import build_structured_evidence, extract_error_signals, parse_correlation_summary


def test_build_structured_evidence_merges_sections() -> None:
    e = build_structured_evidence("ingest text", "correlation text")
    assert "ingest text" in e["merged"]
    assert "correlation text" in e["merged"]


def test_extract_error_signals_from_ingest() -> None:
    ingest = "ERROR timeout to upstream\nTraceback: PaymentGatewayTimeout\nstatus=503"
    signals = extract_error_signals(ingest)
    assert signals
    assert "timeout" in signals or "503" in signals


def test_parse_correlation_summary() -> None:
    corr = "- Class: `UPSTREAM_OUTAGE`\n- Confidence: `high`"
    cls, conf = parse_correlation_summary(corr)
    assert cls == "UPSTREAM_OUTAGE"
    assert conf == "high"
