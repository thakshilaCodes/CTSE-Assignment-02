"""Optional shared helpers or scenario data for briefing evaluation (not pytest)."""

from __future__ import annotations

from dataclasses import dataclass

from mas.evaluation.cases.rca.scenarios import STANDARD_TRIAGE


@dataclass(frozen=True, slots=True)
class BriefingEvalScenario:
    """Inputs that mirror pipeline state keys consumed by the briefing stage."""

    name: str
    ingest_findings: str
    correlation_findings: str
    rca_hypotheses: str


# Kept in sync with ``tests/evaluation/cases/briefing/test_briefing_properties.py`` expectations.
BRIEFING_INPUTS_MINIMAL: BriefingEvalScenario = BriefingEvalScenario(
    name="minimal_sections_smoke",
    ingest_findings="ERROR payment timeout 503\n",
    correlation_findings="- Class: `UPSTREAM_OUTAGE`\n- Confidence: `high`",
    rca_hypotheses="#### 1. Upstream dependency outage\n- Check upstream health",
)

FULL_PIPELINE_STUB: BriefingEvalScenario = BriefingEvalScenario(
    name="full_pipeline_stub",
    ingest_findings=STANDARD_TRIAGE.ingest_findings,
    correlation_findings=STANDARD_TRIAGE.correlation_findings,
    rca_hypotheses=STANDARD_TRIAGE.rca_hypotheses,
)

SCENARIOS: tuple[BriefingEvalScenario, ...] = (BRIEFING_INPUTS_MINIMAL, FULL_PIPELINE_STUB)


def expected_briefing_markdown_needles() -> tuple[str, ...]:
    """Substrings the briefing template should normally include (for smoke / property tests)."""
    return ("# ", "Severity", "Summary", "Mitigations", "Follow-up")


def briefing_kwargs(scenario: BriefingEvalScenario, *, extra_ingest_suffix: str = "") -> dict[str, str]:
    """Keyword args shaped for :func:`mas.agents.briefing.pipeline.run_briefing_pipeline`."""
    ingest = scenario.ingest_findings
    if extra_ingest_suffix:
        ingest = f"{ingest.rstrip()}\n{extra_ingest_suffix}"
    return {
        "ingest_findings": ingest,
        "correlation_findings": scenario.correlation_findings,
        "rca_hypotheses": scenario.rca_hypotheses,
    }
