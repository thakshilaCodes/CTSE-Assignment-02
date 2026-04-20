"""Tests for ingest path policy, read tools, discovery, and normalization."""

from __future__ import annotations

from pathlib import Path

import pytest

from mas.tools.ingest.discover_logs import list_log_candidates
from mas.tools.ingest.normalize import extract_top_signal_lines, strip_ansi, summarize_counts
from mas.tools.ingest.paths import resolve_path_under_roots
from mas.tools.ingest.read_logs import read_log_excerpt, read_log_tail


def test_resolve_rejects_path_outside_roots(tmp_path: Path) -> None:
    safe = tmp_path / "logs"
    safe.mkdir()
    inner = safe / "app.log"
    inner.write_text("ok", encoding="utf-8")

    roots = [safe.resolve()]
    p, err = resolve_path_under_roots(str(inner), roots)
    assert err is None
    assert p == inner.resolve()

    outside = tmp_path / "secret.txt"
    outside.write_text("x", encoding="utf-8")
    p2, err2 = resolve_path_under_roots(str(outside), roots)
    assert p2 is None
    assert err2 is not None


def test_resolve_blocks_parent_traversal(tmp_path: Path) -> None:
    safe = tmp_path / "logs"
    safe.mkdir()
    roots = [safe.resolve()]
    outside = tmp_path / "outside.log"
    outside.write_text("secret", encoding="utf-8")
    p, err = resolve_path_under_roots(str(outside), roots)
    assert p is None
    assert err is not None


def test_read_excerpt_and_tail(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    log = tmp_path / "test.log"
    lines = [f"{i} LINE\n" for i in range(50)]
    lines.append("ERROR final boom\n")
    log.write_text("".join(lines), encoding="utf-8")

    monkeypatch.setenv("MAS_INGEST_ALLOWED_ROOTS", str(tmp_path))

    head = read_log_excerpt(str(log), max_lines=5)
    assert "0 LINE" in head
    assert "ERROR" not in head or len(head.splitlines()) <= 5

    tail = read_log_tail(str(log), max_lines=5)
    assert "ERROR final boom" in tail


def test_strip_ansi_and_signals() -> None:
    raw = "\x1b[31mERROR\x1b[0m: failed\nINFO ok\n"
    assert "ERROR" in strip_ansi(raw)
    sigs = extract_top_signal_lines(raw, max_lines=5)
    assert any("ERROR" in s for s in sigs)


def test_discover_finds_log(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    d = tmp_path / "d"
    d.mkdir()
    (d / "foo.log").write_text("ERROR x\n", encoding="utf-8")
    monkeypatch.setenv("MAS_INGEST_ALLOWED_ROOTS", str(tmp_path))
    found = list_log_candidates(max_files=10, roots=None)
    assert any(str(d / "foo.log") in f or f.endswith("foo.log") for f in found)


def test_summarize_counts() -> None:
    c = summarize_counts("ERROR\nERROR\nWARN\n")
    assert c["error_hits"] == 2
    assert c["warn_hits"] >= 1
