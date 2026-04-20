"""Structured RCA output for downstream briefing and state handoff."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RCAHypothesis:
    """One ranked root-cause hypothesis."""

    rank: int
    title: str
    likelihood: str
    supporting_evidence: list[str] = field(default_factory=list)
    disproof_checks: list[str] = field(default_factory=list)


@dataclass
class RCAReport:
    """RCA stage output used to populate ``GlobalState['rca_hypotheses']``."""

    incident_class: str = "UNKNOWN"
    confidence: str = "low"
    hypotheses: list[RCAHypothesis] = field(default_factory=list)
    summary_markdown: str = ""
    ollama_refinement: str | None = None

    def to_state_string(self) -> str:
        """Serialize RCA findings for briefing stage."""
        if self.ollama_refinement:
            return (
                "## RCA summary (local Ollama SLM)\n\n"
                f"{self.ollama_refinement}\n\n---\n\n"
                + self.summary_markdown
            ).strip()
        return self.summary_markdown.strip()
