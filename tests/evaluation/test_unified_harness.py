"""Unified harness smoke tests: entrypoints and imports."""

from __future__ import annotations

import importlib


def test_harness_run_all_importable() -> None:
    mod = importlib.import_module("mas.evaluation.harness.run_all")
    assert callable(mod.main)


def test_llm_judge_importable() -> None:
    mod = importlib.import_module("mas.evaluation.harness.llm_judge")
    assert callable(mod.judge_agent_output)


def test_eval_scenario_helpers_importable() -> None:
    """Shared per-agent scenario modules (not pytest) stay importable."""
    ingest_e = importlib.import_module("mas.evaluation.cases.ingest")
    corr_e = importlib.import_module("mas.evaluation.cases.correlation")
    rca_e = importlib.import_module("mas.evaluation.cases.rca")
    br_e = importlib.import_module("mas.evaluation.cases.briefing")
    assert ingest_e.SCENARIOS
    assert "HTTP_503" in corr_e.top_signatures_for(ingest_e.INGEST_FINDINGS_UPSTREAM_503)
    assert "---INGEST---" in rca_e.merged_evidence_block()
    assert br_e.expected_briefing_markdown_needles()
