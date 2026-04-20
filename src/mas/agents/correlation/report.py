"""Structured output for correlation stage and state handoff."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CorrelationReport:
    """Correlation stage output used to populate ``GlobalState['correlation_findings']``."""

    signatures: list[str] = field(default_factory=list)
    matches_by_signature: dict[str, list[dict[str, str]]] = field(default_factory=dict)
    candidate_incident_class: str = "UNKNOWN"
    confidence: str = "low"
    summary_markdown: str = ""

    def to_state_string(self) -> str:
        """Serialize final correlation findings for downstream RCA stage."""
        return self.summary_markdown.strip()
