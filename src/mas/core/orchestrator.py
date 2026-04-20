"""Minimal orchestration helpers with concrete RCA state handoff."""

from __future__ import annotations

import argparse
import json

from mas.agents.rca import run_rca_pipeline
from mas.core.observability import log_agent_step
from mas.core.state import GlobalState


def run_rca_stage(
    state: GlobalState | None = None,
    *,
    use_ollama: bool = True,
) -> GlobalState:
    """
    Execute RCA stage and persist output to ``state['rca_hypotheses']``.

    Requires:
    - ``state['ingest_findings']``
    - ``state['correlation_findings']``
    """
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


def main(argv: list[str] | None = None) -> int:
    """CLI entry for RCA handoff demo."""
    parser = argparse.ArgumentParser(description="Run RCA stage from ingest+correlation files.")
    parser.add_argument("--ingest-file", required=True, help="Path to ingest findings text.")
    parser.add_argument("--correlation-file", required=True, help="Path to correlation findings text.")
    parser.add_argument("--no-ollama", action="store_true", help="Skip local Ollama refinement.")
    args = parser.parse_args(argv)

    with open(args.ingest_file, "r", encoding="utf-8") as f:
        ingest = f.read()
    with open(args.correlation_file, "r", encoding="utf-8") as f:
        correlation = f.read()

    state: GlobalState = {
        "ingest_findings": ingest,
        "correlation_findings": correlation,
    }
    state = run_rca_stage(state, use_ollama=not args.no_ollama)
    print(json.dumps(state, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
