"""Minimal orchestration helpers with concrete briefing state handoff."""

from __future__ import annotations

import argparse
import json

from mas.agents.briefing import run_briefing_pipeline
from mas.core.observability import log_agent_step
from mas.core.state import GlobalState


def run_briefing_stage(
    state: GlobalState | None = None,
    *,
    use_ollama: bool = True,
) -> GlobalState:
    """
    Execute briefing stage and persist output to ``state['briefing_markdown']``.

    Requires:
    - ``state['ingest_findings']``
    - ``state['correlation_findings']``
    - ``state['rca_hypotheses']``
    """
    current_state: GlobalState = dict(state or {})
    ingest = current_state.get("ingest_findings", "").strip()
    correlation = current_state.get("correlation_findings", "").strip()
    rca = current_state.get("rca_hypotheses", "").strip()

    missing: list[str] = []
    if not ingest:
        missing.append("ingest_findings")
    if not correlation:
        missing.append("correlation_findings")
    if not rca:
        missing.append("rca_hypotheses")

    if missing:
        current_state["briefing_markdown"] = (
            "# Incident Briefing (incomplete)\n\nMissing required state keys: "
            + ", ".join(f"`{k}`" for k in missing)
            + ". Run prior stages first."
        )
        log_agent_step("orchestrator", {"stage": "briefing", "status": "missing_inputs", "missing": missing})
        return current_state

    report = run_briefing_pipeline(
        ingest_findings=ingest,
        correlation_findings=correlation,
        rca_hypotheses=rca,
        use_ollama=use_ollama,
    )
    current_state["briefing_markdown"] = report.to_state_string()

    scratch = dict(current_state.get("scratchpad", {}))
    scratch["briefing_title"] = report.title
    scratch["briefing_severity"] = report.severity
    scratch["briefing_incident_class"] = report.incident_class
    current_state["scratchpad"] = scratch

    log_agent_step(
        "orchestrator",
        {
            "stage": "briefing",
            "title": report.title,
            "severity": report.severity,
            "incident_class": report.incident_class,
        },
    )
    return current_state


def main(argv: list[str] | None = None) -> int:
    """CLI entry for briefing handoff demo."""
    parser = argparse.ArgumentParser(description="Run briefing stage from ingest/correlation/rca files.")
    parser.add_argument("--ingest-file", required=True, help="Path to ingest findings text.")
    parser.add_argument("--correlation-file", required=True, help="Path to correlation findings text.")
    parser.add_argument("--rca-file", required=True, help="Path to RCA hypotheses text.")
    parser.add_argument("--no-ollama", action="store_true", help="Skip local Ollama refinement.")
    args = parser.parse_args(argv)

    with open(args.ingest_file, "r", encoding="utf-8") as f:
        ingest = f.read()
    with open(args.correlation_file, "r", encoding="utf-8") as f:
        correlation = f.read()
    with open(args.rca_file, "r", encoding="utf-8") as f:
        rca = f.read()

    state: GlobalState = {
        "ingest_findings": ingest,
        "correlation_findings": correlation,
        "rca_hypotheses": rca,
    }
    state = run_briefing_stage(state, use_ollama=not args.no_ollama)
    print(json.dumps(state, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
