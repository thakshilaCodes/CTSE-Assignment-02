"""Optional LLM-as-a-Judge tests (skipped when OLLAMA_SKIP=1)."""

from __future__ import annotations

import os

import pytest

from mas.evaluation.harness.llm_judge import judge_agent_output


def test_llm_judge_fallback_always_returns_struct() -> None:
    os.environ["OLLAMA_SKIP"] = "1"
    result = judge_agent_output(
        agent_name="ingest",
        output_text="## Ingest findings\nERROR timeout\n",
        rubric="Output must mention errors grounded in logs.",
    )
    assert "pass" in result
    assert "score" in result
    assert result["source"] == "fallback"


@pytest.mark.ollama
def test_llm_judge_ollama_path_when_available() -> None:
    if os.environ.get("OLLAMA_SKIP", "").lower() in {"1", "true", "yes"}:
        pytest.skip("OLLAMA_SKIP set")
    result = judge_agent_output(
        agent_name="briefing",
        output_text="# Title\n**Severity:** SEV2\n## Executive Summary\nImpact noted.\n",
        rubric="Must include severity and summary sections.",
    )
    assert result["source"] in {"ollama", "fallback"}
