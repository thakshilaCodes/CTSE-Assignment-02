"""Run briefing stage from CLI: ``python -m mas.agents.briefing``."""

from __future__ import annotations

import argparse
import sys

from mas.agents.briefing.pipeline import run_briefing_pipeline


def _read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run briefing stage from ingest/correlation/rca findings.")
    parser.add_argument("--ingest-file", required=True, help="Path to ingest findings text.")
    parser.add_argument("--correlation-file", required=True, help="Path to correlation findings text.")
    parser.add_argument("--rca-file", required=True, help="Path to RCA hypotheses text.")
    parser.add_argument("--no-ollama", action="store_true", help="Skip local Ollama refinement.")
    args = parser.parse_args(argv)

    try:
        ingest = _read_text(args.ingest_file)
        correlation = _read_text(args.correlation_file)
        rca = _read_text(args.rca_file)
    except OSError as e:
        sys.stderr.write(f"Failed to read input file: {e}\n")
        return 1

    report = run_briefing_pipeline(
        ingest_findings=ingest,
        correlation_findings=correlation,
        rca_hypotheses=rca,
        use_ollama=not args.no_ollama,
    )
    sys.stdout.write(report.to_state_string())
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
