"""Minimal orchestration helpers with ingest -> correlation state handoff."""

from __future__ import annotations

import argparse
import json

from mas.agents.correlation import run_correlation_pipeline
from mas.agents.ingest import run_ingest_pipeline
from mas.core.observability import log_agent_step
from mas.core.state import GlobalState


def run_ingest_stage(
    state: GlobalState | None = None,
    *,
    file_paths: list[str] | None = None,
    discover: bool = False,
    use_ollama: bool = True,
) -> GlobalState:
    """
    Execute ingest and store its serialized output in shared state.

    This is the handoff required for the next stage (correlation):
        state["ingest_findings"] = report.to_state_string()
    """
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
    """
    Execute correlation stage and persist results into shared state.

    Requires ``state['ingest_findings']`` populated by the ingest stage.
    """
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


def run_once(
    *,
    file_paths: list[str] | None = None,
    discover: bool = False,
    use_ollama: bool = True,
    run_correlation: bool = False,
    incident_db: str | None = None,
) -> GlobalState:
    """Run ingest, and optionally run correlation after ingest."""
    state: GlobalState = {}
    state = run_ingest_stage(
        state,
        file_paths=file_paths,
        discover=discover,
        use_ollama=use_ollama,
    )
    if run_correlation:
        state = run_correlation_stage(state, db_path=incident_db)
    return state


def main(argv: list[str] | None = None) -> int:
    """CLI entry for ingest/correlation handoff."""
    parser = argparse.ArgumentParser(description="Run orchestrator ingest and/or correlation handoff.")
    parser.add_argument("files", nargs="*", help="Log files to ingest.")
    parser.add_argument("--discover", action="store_true", help="Discover logs under allowed roots.")
    parser.add_argument("--no-ollama", action="store_true", help="Skip local Ollama calls.")
    parser.add_argument(
        "--run-correlation",
        action="store_true",
        help="After ingest, run correlation stage using ingest_findings in state.",
    )
    parser.add_argument("--incident-db", default=None, help="Optional SQLite incidents DB for correlation.")
    parser.add_argument(
        "--ingest-file",
        default=None,
        help="Run only correlation stage from an existing ingest findings markdown/text file.",
    )
    args = parser.parse_args(argv)

    if args.ingest_file:
        with open(args.ingest_file, "r", encoding="utf-8") as f:
            ingest_text = f.read()
        state: GlobalState = {"ingest_findings": ingest_text}
        state = run_correlation_stage(state, db_path=args.incident_db)
    else:
        state = run_once(
            file_paths=list(args.files) if args.files else None,
            discover=args.discover or not args.files,
            use_ollama=not args.no_ollama,
            run_correlation=args.run_correlation,
            incident_db=args.incident_db,
        )

    print(json.dumps(state, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())