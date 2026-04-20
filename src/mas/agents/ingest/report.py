"""Structured ingest output for downstream agents and global state."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class IngestReport:
    """Result of the ingest pipeline (tools + deterministic evidence + optional Ollama SLM)."""

    source_files: list[str]
    """Log files that were read."""

    tool_trace: list[dict[str, str]] = field(default_factory=list)
    """Lightweight record of tool outcomes for observability."""

    head_excerpts: dict[str, str] = field(default_factory=dict)
    """Per-file head excerpt (first chunk)."""

    tail_excerpts: dict[str, str] = field(default_factory=dict)
    """Per-file tail excerpt (recent lines)."""

    signal_lines: list[str] = field(default_factory=list)
    """Highest-signal lines extracted by heuristics."""

    counts: dict[str, int] = field(default_factory=dict)
    """Aggregate counts across combined text."""

    summary_markdown: str = ""
    """Deterministic tool-backed markdown (excerpts, counts, signal lines)."""

    ollama_summary: str | None = None
    """SLM-written ingest narrative via local Ollama (``None`` if skipped or unreachable)."""

    def to_state_string(self) -> str:
        """Serialize for ``ingest_findings``: Ollama narrative first when present, then tool evidence."""
        if self.ollama_summary:
            return (
                "## Ingest summary (local Ollama SLM)\n\n"
                f"{self.ollama_summary}\n\n---\n\n"
                + self.summary_markdown
            ).strip()
        return self.summary_markdown.strip()
