"""Minimal orchestration helpers with concrete ingest -> correlation state handoff."""

from __future__ import annotations

import argparse
import json

from mas.agents.correlation import run_correlation_pipeline
from mas.core.observability import log_agent_step
from mas.core.state import GlobalState


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


def main(argv: list[str] | None = None) -> int:
    """CLI entry for correlation handoff demo."""
    parser = argparse.ArgumentParser(description="Run correlation stage from ingest findings file.")
    parser.add_argument("--ingest-file", required=True, help="Path to ingest findings markdown/text.")
    parser.add_argument("--incident-db", default=None, help="Optional SQLite incidents DB.")
    args = parser.parse_args(argv)

    with open(args.ingest_file, "r", encoding="utf-8") as f:
        ingest_text = f.read()

    state: GlobalState = {"ingest_findings": ingest_text}
    state = run_correlation_stage(state, db_path=args.incident_db)
    print(json.dumps(state, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
