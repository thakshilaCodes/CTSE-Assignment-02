"""End-to-end ingest stage: discover/read logs, normalize, Ollama SLM + evidence for state."""

from __future__ import annotations

from pathlib import Path

from mas.agents.ingest.agent import SYSTEM_PROMPT
from mas.agents.ingest import ollama as ollama_client
from mas.agents.ingest.report import IngestReport
from mas.core.observability import log_agent_step, log_tool_invocation
from mas.tools.ingest.discover_logs import list_log_candidates
from mas.tools.ingest.normalize import extract_top_signal_lines, strip_ansi, summarize_counts
from mas.tools.ingest.read_logs import log_file_stats, read_log_excerpt, read_log_tail


def run_ingest_pipeline(
    *,
    file_paths: list[str] | None = None,
    discover: bool = False,
    prefer_tail: bool = True,
    head_max_lines: int = 80,
    tail_max_lines: int = 200,
    roots: list[Path] | None = None,
    use_ollama: bool = True,
) -> IngestReport:
    """
    Run ingest tools, then (by default) call **local Ollama** for the ingest narrative.

    Tool outputs are always assembled into ``summary_markdown``. When ``use_ollama`` is True
    and Ollama is reachable, the same evidence is passed to the SLM with :data:`SYSTEM_PROMPT`;
    the reply is stored in ``ollama_summary``. If Ollama is skipped or down, only evidence remains.

    Args:
        file_paths: Explicit log paths; if empty and ``discover`` is True, uses discovery.
        discover: If True, append paths from :func:`list_log_candidates`.
        prefer_tail: Include tail excerpts (recommended for recent failures).
        head_max_lines: Lines read from file head per file.
        tail_max_lines: Lines read from file tail per file.
        roots: Optional path allowlist for all tools.
        use_ollama: If True, call Ollama (unless ``OLLAMA_SKIP=1``). Set False for offline tests.

    Returns:
        Populated :class:`IngestReport`.
    """
    trace: list[dict[str, str]] = []
    paths: list[str] = list(file_paths or [])
    if discover:
        found = list_log_candidates(roots=roots)
        for p in found:
            if p not in paths:
                paths.append(p)

    if not paths:
        report = IngestReport(
            source_files=[],
            summary_markdown=(
                "## Ingest\n\nNo log files provided and none discovered under allowed roots. "
                "Set `MAS_INGEST_ALLOWED_ROOTS` or place logs under `artifacts/logs/`."
            ),
        )
        log_agent_step("ingest", {"event": "empty", "summary_len": len(report.summary_markdown)})
        return report

    head_excerpts: dict[str, str] = {}
    tail_excerpts: dict[str, str] = {}
    combined_for_norm: list[str] = []

    for fp in paths:
        st = log_file_stats(fp, roots=roots)
        log_tool_invocation("log_file_stats", {"path": fp}, st)
        trace.append({"tool": "log_file_stats", "path": fp, "result": st[:500]})

        head = read_log_excerpt(fp, max_lines=head_max_lines, roots=roots)
        log_tool_invocation("read_log_excerpt", {"path": fp}, head[:500])
        trace.append({"tool": "read_log_excerpt", "path": fp, "result": head[:2000]})
        head_excerpts[fp] = head
        combined_for_norm.append(head)

        if prefer_tail:
            tail = read_log_tail(fp, max_lines=tail_max_lines, roots=roots)
            log_tool_invocation("read_log_tail", {"path": fp}, tail[:500])
            trace.append({"tool": "read_log_tail", "path": fp, "result": tail[:2000]})
            tail_excerpts[fp] = tail
            combined_for_norm.append(tail)

    blob = "\n".join(combined_for_norm)
    counts = summarize_counts(blob)
    signals = extract_top_signal_lines(blob, max_lines=40)

    md_parts = [
        "## Ingest findings",
        "",
        "### Files reviewed",
        "",
    ]
    for p in paths:
        md_parts.append(f"- `{p}`")
    md_parts.extend(
        [
            "",
            "### Stats",
            "",
            f"- Signal line candidates: {len(signals)}",
            f"- Counts: {counts}",
            "",
        ]
    )
    md_parts.extend(["### Key signal lines (heuristic)", ""])
    if signals:
        for line in signals[:25]:
            md_parts.append(f"- `{strip_ansi(line)[:500]}`")
    else:
        md_parts.append("- (no high-severity keywords detected in sampled text)")
    md_parts.extend(["", "### Raw excerpts (truncated)", ""])
    for fp in paths:
        md_parts.append(f"#### Head: `{fp}`")
        md_parts.append("```text")
        md_parts.append(head_excerpts.get(fp, "")[:4000])
        md_parts.append("```")
        if prefer_tail and fp in tail_excerpts:
            md_parts.append(f"#### Tail: `{fp}`")
            md_parts.append("```text")
            md_parts.append(tail_excerpts[fp][:4000])
            md_parts.append("```")

    summary = "\n".join(md_parts)
    report = IngestReport(
        source_files=paths,
        tool_trace=trace,
        head_excerpts=head_excerpts,
        tail_excerpts=tail_excerpts,
        signal_lines=signals,
        counts=counts,
        summary_markdown=summary,
    )

    log_agent_step(
        "ingest",
        {
            "files": len(paths),
            "signals": len(signals),
            "evidence_chars": len(summary),
        },
    )

    if use_ollama:
        slm_text = ollama_client.synthesize_ingest_with_ollama(SYSTEM_PROMPT, summary)
        if slm_text:
            report.ollama_summary = slm_text
            log_agent_step(
                "ingest",
                {
                    "ollama": True,
                    "model": ollama_client.ollama_model(),
                    "ollama_summary_chars": len(slm_text),
                },
            )
        else:
            log_agent_step(
                "ingest",
                {
                    "ollama": False,
                    "note": "OLLAMA_SKIP, unreachable, or error — evidence only in state",
                },
            )

    return report
