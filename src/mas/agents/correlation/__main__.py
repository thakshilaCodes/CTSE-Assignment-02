"""Run correlation stage from CLI: ``python -m mas.agents.correlation``."""

from __future__ import annotations

import argparse
import sys

from mas.agents.correlation.pipeline import run_correlation_pipeline


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run correlation stage from ingest findings text.")
    parser.add_argument(
        "--ingest-file",
        required=True,
        help="Path to a text/markdown file containing ingest findings.",
    )
    parser.add_argument(
        "--incident-db",
        default=None,
        help="Optional SQLite DB path containing incidents table.",
    )
    args = parser.parse_args(argv)

    try:
        ingest_findings = open(args.ingest_file, "r", encoding="utf-8").read()
    except OSError as e:
        sys.stderr.write(f"Failed to read ingest file: {e}\n")
        return 1

    report = run_correlation_pipeline(
        ingest_findings=ingest_findings,
        db_path=args.incident_db,
    )
    sys.stdout.write(report.to_state_string())
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
