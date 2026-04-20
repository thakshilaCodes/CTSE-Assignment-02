"""Smoke tests for RCA agent exports."""

from mas.agents.rca import RCA_OUTPUT_HINT, SYSTEM_PROMPT, run_rca_pipeline


def test_agent_prompt_and_schema_defined() -> None:
    assert "Root Cause Analysis" in SYSTEM_PROMPT
    assert "hypotheses" in RCA_OUTPUT_HINT


def test_pipeline_importable() -> None:
    assert callable(run_rca_pipeline)
