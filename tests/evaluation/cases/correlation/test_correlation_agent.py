"""Smoke tests for correlation agent exports."""

from mas.agents.correlation import CORRELATION_OUTPUT_HINT, SYSTEM_PROMPT, run_correlation_pipeline


def test_agent_prompt_and_schema_defined() -> None:
    assert "Correlation agent" in SYSTEM_PROMPT
    assert "candidate_incident_class" in CORRELATION_OUTPUT_HINT


def test_pipeline_importable() -> None:
    assert callable(run_correlation_pipeline)
