"""Group-owned unified harness: run full evaluation via ``python -m mas.evaluation.harness``."""

from __future__ import annotations

import importlib


def test_harness_module_has_main() -> None:
    mod = importlib.import_module("mas.evaluation.harness.run_all")
    assert callable(mod.main)
