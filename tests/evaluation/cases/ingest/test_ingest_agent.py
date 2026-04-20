"""Smoke tests for ingest agent exports."""

from mas.agents.ingest import INGEST_OUTPUT_HINT, SYSTEM_PROMPT, run_ingest_pipeline


def test_agent_prompt_and_schema_defined() -> None:
    assert "Log Ingest" in SYSTEM_PROMPT
    assert "sources" in INGEST_OUTPUT_HINT


def test_run_ingest_pipeline_importable() -> None:
    assert callable(run_ingest_pipeline)
