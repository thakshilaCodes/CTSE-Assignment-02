"""Tests for orchestrator ingest -> shared state handoff."""

from __future__ import annotations

from pathlib import Path

import pytest

from mas.core.orchestrator import run_ingest_stage, run_once


def test_run_ingest_stage_sets_ingest_findings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OLLAMA_SKIP", "1")
    monkeypatch.setenv("MAS_INGEST_ALLOWED_ROOTS", str(tmp_path))

    log_file = tmp_path / "service.log"
    log_file.write_text("INFO boot\nERROR db timeout\n", encoding="utf-8")

    state = run_ingest_stage(
        {},
        file_paths=[str(log_file)],
        discover=False,
        use_ollama=False,
    )

    assert "ingest_findings" in state
    assert "Ingest findings" in state["ingest_findings"]
    assert "ERROR" in state["ingest_findings"]
    assert "scratchpad" in state
    assert state["scratchpad"]["ingest_source_files"]


def test_run_once_returns_state_with_ingest(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OLLAMA_SKIP", "1")
    monkeypatch.setenv("MAS_INGEST_ALLOWED_ROOTS", str(tmp_path))
    log_file = tmp_path / "api.log"
    log_file.write_text("WARN retry\nERROR 503 upstream\n", encoding="utf-8")

    state = run_once(file_paths=[str(log_file)], use_ollama=False)
    assert state.get("ingest_findings")
