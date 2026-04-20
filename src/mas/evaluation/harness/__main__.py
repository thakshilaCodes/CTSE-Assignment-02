"""Run: ``python -m mas.evaluation.harness`` (delegates to :mod:`mas.evaluation.harness.run_all`)."""

from __future__ import annotations

import sys

from mas.evaluation.harness.run_all import main

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
