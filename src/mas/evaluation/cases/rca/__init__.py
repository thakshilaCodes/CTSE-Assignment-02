"""Optional scenario data/helpers for RCA agent evaluation."""

from mas.evaluation.cases.rca.scenarios import (
    CORRELATION_FINDINGS_UPSTREAM_MATCH,
    RCA_HYPOTHESES_UPSTREAM_STUB,
    SCENARIOS,
    RcaEvalScenario,
    STANDARD_TRIAGE,
    merged_evidence_block,
    quick_correlation_stub_from_ingest,
    structured_evidence_dict,
)

__all__ = [
    "CORRELATION_FINDINGS_UPSTREAM_MATCH",
    "RCA_HYPOTHESES_UPSTREAM_STUB",
    "SCENARIOS",
    "RcaEvalScenario",
    "STANDARD_TRIAGE",
    "merged_evidence_block",
    "quick_correlation_stub_from_ingest",
    "structured_evidence_dict",
]
