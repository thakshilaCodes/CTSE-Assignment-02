"""Smoke tests for briefing agent exports."""

from mas.agents.briefing import BRIEFING_OUTPUT_HINT, SYSTEM_PROMPT, run_briefing_pipeline


def test_agent_prompt_and_schema_defined() -> None:
    assert "Incident Briefing" in SYSTEM_PROMPT
    assert "severity" in BRIEFING_OUTPUT_HINT


def test_pipeline_importable() -> None:
    assert callable(run_briefing_pipeline)
