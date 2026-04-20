"""Run ingest pipeline from the CLI: ``python -m mas.agents.ingest``."""

from __future__ import annotations

import argparse
import os
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run log ingest with local Ollama SLM + tool-backed evidence.",
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Log files to read (relative to CWD or absolute under allowed roots).",
    )
    parser.add_argument(
        "--discover",
        action="store_true",
        help="Also scan allowed roots for *.log and similar files.",
    )
    parser.add_argument(
        "--no-ollama",
        action="store_true",
        help="Skip Ollama (sets OLLAMA_SKIP=1); evidence-only markdown.",
    )
    parser.add_argument(
        "--check-ollama",
        action="store_true",
        help="Print whether Ollama HTTP API is reachable and exit (0=up, 1=down).",
    )
    args = parser.parse_args(argv)

    from mas.agents.ingest import ollama as ollama_client

    if args.check_ollama:
        ok = ollama_client.is_ollama_available()
        print(f"ollama_reachable={ok} base={ollama_client.ollama_base_url()} model={ollama_client.ollama_model()}")
        return 0 if ok else 1

    if args.no_ollama:
        os.environ["OLLAMA_SKIP"] = "1"

    from mas.agents.ingest.pipeline import run_ingest_pipeline

    report = run_ingest_pipeline(
        file_paths=list(args.files) if args.files else None,
        discover=args.discover or not args.files,
        use_ollama=not args.no_ollama,
    )
    sys.stdout.write(report.to_state_string())
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
