"""Optional shared helpers or scenario data for correlation evaluation (not pytest)."""

from __future__ import annotations

from dataclasses import dataclass

from mas.evaluation.cases.ingest.scenarios import INGEST_FINDINGS_PAYMENT_TIMEOUT, INGEST_FINDINGS_UPSTREAM_503
from mas.tools.correlation.query_incidents import FALLBACK_INCIDENTS
from mas.tools.correlation.signatures import extract_signatures


@dataclass(frozen=True, slots=True)
class CorrelationEvalScenario:
    """Ingest-shaped text plus expected top signatures for deterministic checks."""

    name: str
    ingest_findings: str
    expected_signatures_contain: tuple[str, ...]


SCENARIOS: tuple[CorrelationEvalScenario, ...] = (
    CorrelationEvalScenario(
        name="maps_to_upstream_503",
        ingest_findings=INGEST_FINDINGS_UPSTREAM_503,
        expected_signatures_contain=("HTTP_503",),
    ),
    CorrelationEvalScenario(
        name="maps_payment_timeout",
        ingest_findings=INGEST_FINDINGS_PAYMENT_TIMEOUT,
        expected_signatures_contain=("PaymentGatewayTimeout", "HTTP_503"),
    ),
)


def fallback_catalog_signatures() -> frozenset[str]:
    """Signatures present in the built-in fallback incident catalog."""
    return frozenset(row["signature"] for row in FALLBACK_INCIDENTS)


def top_signatures_for(ingest_findings: str, *, limit: int = 12) -> list[str]:
    """Thin wrapper around production :func:`extract_signatures` for tests and notebooks."""
    return extract_signatures(ingest_findings, limit=limit)


def scenario_signature_expectations() -> list[tuple[str, tuple[str, ...]]]:
    """(ingest text, substrings that should appear in ranked signatures) for table-driven tests."""
    return [(s.ingest_findings, s.expected_signatures_contain) for s in SCENARIOS]
