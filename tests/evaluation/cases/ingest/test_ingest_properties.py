"""Property-based tests for ingest agent: path policy and tool safety (student: ingest owner)."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

from mas.tools.ingest.paths import resolve_path_under_roots
from mas.tools.ingest.read_logs import read_log_excerpt

_safe_name = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N"), min_codepoint=48, max_codepoint=122),
    min_size=1,
    max_size=24,
).filter(lambda s: s.strip() and not s.startswith("."))


@settings(max_examples=30)
@given(name=_safe_name)
def test_property_resolve_accepts_files_under_allowed_root(name: str) -> None:
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        allowed = base / "allowed"
        allowed.mkdir()
        log_file = allowed / f"{name}.log"
        log_file.write_text("LINE\n", encoding="utf-8")
        roots = [allowed.resolve()]
        p, err = resolve_path_under_roots(str(log_file), roots)
        assert err is None
        assert p is not None
        assert p.resolve() == log_file.resolve()


@settings(max_examples=25)
@given(content=st.text(min_size=0, max_size=500))
def test_property_read_excerpt_never_reads_outside_root(content: str) -> None:
    """Malicious-looking paths must not return real filesystem content outside roots."""
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        safe = base / "logs"
        safe.mkdir()
        secret = base / "secret.txt"
        secret.write_text("SECRET_DATA" + content, encoding="utf-8")
        old = os.environ.get("MAS_INGEST_ALLOWED_ROOTS")
        os.environ["MAS_INGEST_ALLOWED_ROOTS"] = str(safe)
        try:
            out = read_log_excerpt(str(secret), max_lines=10, roots=[safe.resolve()])
            assert out.startswith("ERROR:") or "SECRET_DATA" not in out
        finally:
            if old is None:
                os.environ.pop("MAS_INGEST_ALLOWED_ROOTS", None)
            else:
                os.environ["MAS_INGEST_ALLOWED_ROOTS"] = old
