"""Global state schema and helpers passed between agents (implement as a team)."""

from __future__ import annotations

from typing import Any, TypedDict


class GlobalState(TypedDict, total=False):
    """Shared handoff for the incident triage pipeline; extend as your orchestrator needs."""

    messages: list[dict[str, Any]]
    ingest_findings: str
    correlation_findings: str
    rca_hypotheses: str
    briefing_markdown: str
    scratchpad: dict[str, Any]
