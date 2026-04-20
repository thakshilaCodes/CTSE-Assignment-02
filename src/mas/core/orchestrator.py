"""Minimal orchestration helpers with ingest -> correlation -> rca -> briefing state handoff."""

from __future__ import annotations

import argparse
import json

from mas.agents.briefing import run_briefing_pipeline
from mas.agents.correlation import run_correlation_pipeline
from mas.agents.ingest import run_ingest_pipeline
from mas.agents.rca import run_rca_pipeline
from mas.core.observability import log_agent_step
from mas.core.state import GlobalState


def run_ingest_stage(
    state: GlobalState | None = None,
    *,
    file_paths: list[str] | None = None,
    discover: bool = False,
    use_ollama: bool = True,
) -> GlobalState:
    """Execute ingest and store its serialized output in shared state."""
    current_state: GlobalState = dict(state or {})
    report = run_ingest_pipeline(
        file_paths=file_paths,
        discover=discover,
        use_ollama=use_ollama,
    )
    current_state["ingest_findings"] = report.to_state_string()

    scratch = dict(current_state.get("scratchpad", {}))
    scratch["ingest_source_files"] = report.source_files
    scratch["ingest_counts"] = report.counts
    current_state["scratchpad"] = scratch

    log_agent_step(
        "orchestrator",
        {
            "stage": "ingest",
            "files": len(report.source_files),
            "ingest_findings_chars": len(current_state["ingest_findings"]),
        },
    )
    return current_state


def run_correlation_stage(
    state: GlobalState | None = None,
    *,
    db_path: str | None = None,
) -> GlobalState:
    """Execute correlation and persist results into shared state."""
    current_state: GlobalState = dict(state or {})
    ingest_findings = current_state.get("ingest_findings", "").strip()
    if not ingest_findings:
        current_state["correlation_findings"] = (
            "## Correlation findings\n\nMissing `ingest_findings` in global state. "
            "Run ingest stage first."
        )
        log_agent_step("orchestrator", {"stage": "correlation", "status": "missing_ingest_findings"})
        return current_state

    report = run_correlation_pipeline(
        ingest_findings=ingest_findings,
        db_path=db_path,
    )
    current_state["correlation_findings"] = report.to_state_string()

    scratch = dict(current_state.get("scratchpad", {}))
    scratch["correlation_signatures"] = report.signatures
    scratch["candidate_incident_class"] = report.candidate_incident_class
    scratch["correlation_confidence"] = report.confidence
    current_state["scratchpad"] = scratch

    log_agent_step(
        "orchestrator",
        {
            "stage": "correlation",
            "signatures": len(report.signatures),
            "candidate_incident_class": report.candidate_incident_class,
            "confidence": report.confidence,
        },
    )
    return current_state


def run_rca_stage(
    state: GlobalState | None = None,
    *,
    use_ollama: bool = True,
) -> GlobalState:
    """Execute RCA stage and persist output to ``state['rca_hypotheses']``."""
    current_state: GlobalState = dict(state or {})
    ingest = current_state.get("ingest_findings", "").strip()
    correlation = current_state.get("correlation_findings", "").strip()

    missing: list[str] = []
    if not ingest:
        missing.append("ingest_findings")
    if not correlation:
        missing.append("correlation_findings")
    if missing:
        current_state["rca_hypotheses"] = (
            "## RCA hypotheses\n\nMissing required state keys: "
            + ", ".join(f"`{k}`" for k in missing)
            + ". Run prior stages first."
        )
        log_agent_step("orchestrator", {"stage": "rca", "status": "missing_inputs", "missing": missing})
        return current_state

    report = run_rca_pipeline(
        ingest_findings=ingest,
        correlation_findings=correlation,
        use_ollama=use_ollama,
    )
    current_state["rca_hypotheses"] = report.to_state_string()

    scratch = dict(current_state.get("scratchpad", {}))
    scratch["rca_incident_class"] = report.incident_class
    scratch["rca_confidence"] = report.confidence
    scratch["rca_hypothesis_count"] = len(report.hypotheses)
    current_state["scratchpad"] = scratch

    log_agent_step(
        "orchestrator",
        {
            "stage": "rca",
            "incident_class": report.incident_class,
            "confidence": report.confidence,
            "hypothesis_count": len(report.hypotheses),
        },
    )
    return current_state


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


def run_once(
    *,
    file_paths: list[str] | None = None,
    discover: bool = False,
    use_ollama: bool = True,
    run_correlation: bool = False,
    run_rca: bool = False,
    run_briefing: bool = False,
    incident_db: str | None = None,
) -> GlobalState:
    """Run ingest, and optionally correlation, RCA, and briefing in sequence."""
    state: GlobalState = {}
    state = run_ingest_stage(
        state,
        file_paths=file_paths,
        discover=discover,
        use_ollama=use_ollama,
    )
    if run_correlation or run_rca or run_briefing:
        state = run_correlation_stage(state, db_path=incident_db)
    if run_rca or run_briefing:
        state = run_rca_stage(state, use_ollama=use_ollama)
    if run_briefing:
        state = run_briefing_stage(state, use_ollama=use_ollama)
    return state


def main(argv: list[str] | None = None) -> int:
    """CLI entry for ingest/correlation/rca/briefing handoff."""
    parser = argparse.ArgumentParser(description="Run orchestrator pipeline handoff.")
    parser.add_argument("files", nargs="*", help="Log files to ingest.")
    parser.add_argument("--discover", action="store_true", help="Discover logs under allowed roots.")
    parser.add_argument("--no-ollama", action="store_true", help="Skip local Ollama calls/refinements.")
    parser.add_argument("--run-correlation", action="store_true", help="Run correlation after ingest.")
    parser.add_argument("--run-rca", action="store_true", help="Run RCA after correlation.")
    parser.add_argument("--run-briefing", action="store_true", help="Run briefing after RCA.")
    parser.add_argument("--incident-db", default=None, help="Optional SQLite incidents DB for correlation.")
    parser.add_argument("--ingest-file", default=None, help="Existing ingest findings markdown/text file.")
    parser.add_argument("--correlation-file", default=None, help="Existing correlation findings markdown/text file.")
    parser.add_argument("--rca-file", default=None, help="Existing RCA hypotheses markdown/text file.")
    args = parser.parse_args(argv)

    if args.ingest_file and args.correlation_file and args.rca_file:
        with open(args.ingest_file, "r", encoding="utf-8") as f:
            ingest_text = f.read()
        with open(args.correlation_file, "r", encoding="utf-8") as f:
            correlation_text = f.read()
        with open(args.rca_file, "r", encoding="utf-8") as f:
            rca_text = f.read()
        state: GlobalState = {
            "ingest_findings": ingest_text,
            "correlation_findings": correlation_text,
            "rca_hypotheses": rca_text,
        }
        state = run_briefing_stage(state, use_ollama=not args.no_ollama)
    elif args.ingest_file and args.correlation_file:
        with open(args.ingest_file, "r", encoding="utf-8") as f:
            ingest_text = f.read()
        with open(args.correlation_file, "r", encoding="utf-8") as f:
            correlation_text = f.read()
        state = {
            "ingest_findings": ingest_text,
            "correlation_findings": correlation_text,
        }
        state = run_rca_stage(state, use_ollama=not args.no_ollama)
        if args.run_briefing:
            state = run_briefing_stage(state, use_ollama=not args.no_ollama)
    elif args.ingest_file:
        with open(args.ingest_file, "r", encoding="utf-8") as f:
            ingest_text = f.read()
        state = {"ingest_findings": ingest_text}
        state = run_correlation_stage(state, db_path=args.incident_db)
        if args.run_rca or args.run_briefing:
            state = run_rca_stage(state, use_ollama=not args.no_ollama)
        if args.run_briefing:
            state = run_briefing_stage(state, use_ollama=not args.no_ollama)
    else:
        state = run_once(
            file_paths=list(args.files) if args.files else None,
            discover=args.discover or not args.files,
            use_ollama=not args.no_ollama,
            run_correlation=args.run_correlation,
            run_rca=args.run_rca,
            run_briefing=args.run_briefing,
            incident_db=args.incident_db,
        )

    print(json.dumps(state, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())