"""Integration tests for the ingest pipeline."""

from __future__ import annotations

from pathlib import Path

import pytest

from mas.agents.ingest.pipeline import run_ingest_pipeline


def test_pipeline_on_sample_log(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("OLLAMA_SKIP", "1")
    log = tmp_path / "crash.log"
    log.write_text(
        "INFO start\nERROR database connection refused\nTraceback (most recent call last):\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("MAS_INGEST_ALLOWED_ROOTS", str(tmp_path))

    report = run_ingest_pipeline(
        file_paths=[str(log)],
        discover=False,
        use_ollama=False,
    )
    assert report.source_files
    assert "ERROR" in report.summary_markdown or "error" in report.summary_markdown.lower()
    assert report.counts.get("error_hits", 0) >= 1
    state = report.to_state_string()
    assert len(state) > 50


def test_pipeline_empty_when_no_files(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("OLLAMA_SKIP", "1")
    monkeypatch.setenv("MAS_INGEST_ALLOWED_ROOTS", str(tmp_path))
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    monkeypatch.chdir(tmp_path)

    report = run_ingest_pipeline(file_paths=[], discover=False, use_ollama=False)
    assert "No log files" in report.summary_markdown or "none" in report.summary_markdown.lower()
