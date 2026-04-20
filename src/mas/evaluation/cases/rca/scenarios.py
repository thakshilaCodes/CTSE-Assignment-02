"""Optional shared helpers or scenario data for RCA evaluation (not pytest)."""

from __future__ import annotations

from dataclasses import dataclass

from mas.evaluation.cases.ingest.scenarios import INGEST_FINDINGS_UPSTREAM_503
from mas.tools.correlation.signatures import extract_signatures
from mas.tools.rca.evidence_bundle import build_structured_evidence, merge_evidence_for_rca


@dataclass(frozen=True, slots=True)
class RcaEvalScenario:
    """End-to-end-ish text handoff: ingest + correlation + stub RCA output."""

    name: str
    ingest_findings: str
    correlation_findings: str
    rca_hypotheses: str


CORRELATION_FINDINGS_UPSTREAM_MATCH: str = """\
## Correlation
- **Candidate incident class:** `UPSTREAM_OUTAGE`
- **Confidence:** `high`
- **Matched signatures:** `HTTP_503`
- **Gaps for RCA:** confirm blast radius and dependency map
"""

RCA_HYPOTHESES_UPSTREAM_STUB: str = """\
#### 1. Upstream dependency unavailable
- **Likelihood:** high
- **Evidence:** HTTP 503 from edge-proxy toward payment/upstream
- **Disprove:** health checks green on all internal services

#### 2. Misconfigured routing
- **Likelihood:** low
- **Evidence:** intermittent retries
"""

STANDARD_TRIAGE: RcaEvalScenario = RcaEvalScenario(
    name="upstream_503_triage",
    ingest_findings=INGEST_FINDINGS_UPSTREAM_503,
    correlation_findings=CORRELATION_FINDINGS_UPSTREAM_MATCH,
    rca_hypotheses=RCA_HYPOTHESES_UPSTREAM_STUB,
)

SCENARIOS: tuple[RcaEvalScenario, ...] = (STANDARD_TRIAGE,)


def merged_evidence_block(scenario: RcaEvalScenario | None = None) -> str:
    """Single string passed to RCA-style reasoning (same shape as pipeline merge)."""
    s = scenario or STANDARD_TRIAGE
    return merge_evidence_for_rca(s.ingest_findings, s.correlation_findings)


def structured_evidence_dict(scenario: RcaEvalScenario | None = None) -> dict[str, str]:
    """Structured ingest/correlation/merged blocks for tools that avoid raw concatenation."""
    s = scenario or STANDARD_TRIAGE
    return build_structured_evidence(s.ingest_findings, s.correlation_findings)


def quick_correlation_stub_from_ingest(ingest_findings: str, *, limit: int = 4) -> str:
    """Minimal correlation markdown listing top extracted signatures (for dry runs / notebooks)."""
    sigs = extract_signatures(ingest_findings, limit=limit)
    if not sigs:
        return "- Matched signatures: (none)\n"
    joined = ", ".join(f"`{s}`" for s in sigs)
    return f"- Matched signatures: {joined}\n"
