"""
Minimal orchestrator utilities for state handoff between agents.

This module provides an immediate, testable implementation for the first stage:
ingest -> GlobalState["ingest_findings"].
"""

from __future__ import annotations

import argparse
import json
from typing import Any

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


def run_once(
    *,
    file_paths: list[str] | None = None,
    discover: bool = False,
    use_ollama: bool = True,
) -> GlobalState:
    """
    Run the currently-implemented orchestration path (ingest only for now).

    This function is intentionally small so the team can later insert
    correlation -> rca -> briefing stages while preserving state handoffs.
    """
    state: GlobalState = {}
    state = run_ingest_stage(
        state,
        file_paths=file_paths,
        discover=discover,
        use_ollama=use_ollama,
    )
    return state


def main(argv: list[str] | None = None) -> int:
    """CLI demo entry for ingest-to-state handoff."""
    parser = argparse.ArgumentParser(description="Run orchestrator ingest handoff.")
    parser.add_argument("files", nargs="*", help="Log files to ingest.")
    parser.add_argument("--discover", action="store_true", help="Discover logs under allowed roots.")
    parser.add_argument("--no-ollama", action="store_true", help="Skip local Ollama calls.")
    args = parser.parse_args(argv)

    state = run_once(
        file_paths=list(args.files) if args.files else None,
        discover=args.discover or not args.files,
        use_ollama=not args.no_ollama,
    )
    print(json.dumps(state, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
