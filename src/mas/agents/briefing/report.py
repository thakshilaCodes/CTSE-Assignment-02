"""Structured output for briefing stage."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BriefingReport:
    """Final operator-facing briefing report."""

    title: str
    severity: str
    incident_class: str
    markdown: str
    ollama_refinement: str | None = None

    def to_state_string(self) -> str:
        """Serialize briefing output for ``GlobalState['briefing_markdown']``."""
        if self.ollama_refinement:
            return (
                "## Briefing (local Ollama SLM refinement)\n\n"
                f"{self.ollama_refinement}\n\n---\n\n"
                + self.markdown
            ).strip()
        return self.markdown.strip()
