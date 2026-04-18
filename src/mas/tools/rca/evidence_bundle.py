"""Bundle structured evidence for RCA (optional helper tool)."""

from __future__ import annotations


def merge_evidence_for_rca(ingest_summary: str, correlation_summary: str) -> str:
    """
    Combine ingest and correlation text into one evidence block for the RCA agent.

    Args:
        ingest_summary: Normalized output from the ingest stage.
        correlation_summary: Output from the correlation stage.

    Returns:
        A single string suitable as context for hypothesis generation.
    """
    return f"---INGEST---\n{ingest_summary}\n---CORRELATION---\n{correlation_summary}\n"
