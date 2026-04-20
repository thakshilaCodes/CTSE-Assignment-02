"""Run the full MAS pipeline and persist outputs under artifacts/outputs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow running from repo root without requiring editable install first.
ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mas.core.orchestrator import (  # noqa: E402
    run_with_langgraph,
)
from mas.core.state import GlobalState  # noqa: E402


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run ingest -> correlation -> rca -> briefing and save outputs.",
    )
    parser.add_argument("files", nargs="*", help="Log files for ingest stage.")
    parser.add_argument(
        "--discover",
        action="store_true",
        help="Discover log files under allowed roots in addition to explicit files.",
    )
    parser.add_argument("--incident-db", default=None, help="Optional SQLite incidents DB for correlation.")
    parser.add_argument("--no-ollama", action="store_true", help="Skip local Ollama refinement calls.")
    parser.add_argument(
        "--orchestrator",
        choices=("langgraph", "custom"),
        default="langgraph",
        help="Use LangGraph (default) or fallback custom sequential runner.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(ROOT / "artifacts" / "outputs"),
        help="Directory to write pipeline outputs.",
    )
    args = parser.parse_args(argv)

    use_ollama = not args.no_ollama
    discover = args.discover or not args.files
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.orchestrator == "langgraph":
        state: GlobalState = run_with_langgraph(
            file_paths=list(args.files) if args.files else None,
            discover=discover,
            use_ollama=use_ollama,
            incident_db=args.incident_db,
        )
    else:
        from mas.core.orchestrator import (  # noqa: E402
            run_briefing_stage,
            run_correlation_stage,
            run_ingest_stage,
            run_rca_stage,
        )

        state = {}
        state = run_ingest_stage(
            state,
            file_paths=list(args.files) if args.files else None,
            discover=discover,
            use_ollama=use_ollama,
        )
        state = run_correlation_stage(state, db_path=args.incident_db)
        state = run_rca_stage(state, use_ollama=use_ollama)
        state = run_briefing_stage(state, use_ollama=use_ollama)

    _write_text(output_dir / "ingest_findings.md", state.get("ingest_findings", ""))
    _write_text(output_dir / "correlation_findings.md", state.get("correlation_findings", ""))
    _write_text(output_dir / "rca_hypotheses.md", state.get("rca_hypotheses", ""))
    _write_text(output_dir / "briefing_markdown.md", state.get("briefing_markdown", ""))

    state_json = output_dir / "pipeline_state.json"
    state_json.write_text(json.dumps(state, indent=2), encoding="utf-8")

    print("Pipeline completed.")
    print(f"- ingest:      {output_dir / 'ingest_findings.md'}")
    print(f"- correlation: {output_dir / 'correlation_findings.md'}")
    print(f"- rca:         {output_dir / 'rca_hypotheses.md'}")
    print(f"- briefing:    {output_dir / 'briefing_markdown.md'}")
    print(f"- state json:  {state_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
