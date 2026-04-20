"""Unified evaluation harness: run pytest on all evaluation tests (group + per-agent cases)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    """
    Run the evaluation suite via pytest.

    Default::

        pytest tests/evaluation -v

    Pass through any pytest arguments, e.g.::

        python -m mas.evaluation.harness -q
        python -m mas.evaluation.harness tests/evaluation/cases/ingest -k property
    """
    args = list(argv if argv is not None else sys.argv[1:])
    if not args:
        args = ["tests/evaluation", "-v"]

    repo_root = Path(__file__).resolve().parents[4]
    if not (repo_root / "pyproject.toml").exists():
        repo_root = Path.cwd()

    cmd = [sys.executable, "-m", "pytest", *args]
    print("Running:", " ".join(cmd), flush=True)
    return subprocess.call(cmd, cwd=str(repo_root))


if __name__ == "__main__":
    raise SystemExit(main())
