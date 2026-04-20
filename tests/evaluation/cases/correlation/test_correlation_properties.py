"""Property-based tests for correlation agent: signatures and query stability (student: correlation owner)."""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from mas.tools.correlation.signatures import extract_signatures


@settings(max_examples=40)
@given(
    prefix=st.text(min_size=0, max_size=80),
    suffix=st.text(min_size=0, max_size=80),
)
def test_property_extract_signatures_finds_http_marker(prefix: str, suffix: str) -> None:
    text = prefix + " status=503 " + suffix
    sigs = extract_signatures(text, limit=20)
    assert any("503" in s or "HTTP" in s for s in sigs)


@settings(max_examples=20)
@given(body=st.text(min_size=1, max_size=200))
def test_property_extract_signatures_bounded(body: str) -> None:
    sigs = extract_signatures(body, limit=12)
    assert len(sigs) <= 12
