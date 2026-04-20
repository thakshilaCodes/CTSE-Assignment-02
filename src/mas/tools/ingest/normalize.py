"""Normalize and extract high-signal lines from raw log text (no LLM required)."""

from __future__ import annotations

import re
from typing import Final

_ANSI_RE: Final[re.Pattern[str]] = re.compile(r"\x1b\[[0-9;]*m")
_SEVERITY_KEYWORDS: Final[tuple[tuple[str, int], ...]] = (
    ("FATAL", 100),
    ("PANIC", 95),
    ("CRITICAL", 90),
    ("ERROR", 80),
    ("EXCEPTION", 75),
    ("TRACEBACK", 70),
    ("FAILED", 65),
    ("WARN", 40),
    ("WARNING", 40),
    ("TIMEOUT", 50),
    ("500", 35),
    ("503", 35),
)


def strip_ansi(text: str) -> str:
    """Remove ANSI color / style escape sequences from log text."""
    return _ANSI_RE.sub("", text)


def score_line_for_incident_signal(line: str) -> int:
    """
    Heuristic score: higher means more likely to be incident-relevant.

    Uses severity keywords (case-insensitive). Empty lines score 0.
    """
    u = line.upper()
    score = 0
    for needle, weight in _SEVERITY_KEYWORDS:
        if needle in u:
            score = max(score, weight)
    if "HTTP" in u and any(x in u for x in ("4", "5")) and any(c.isdigit() for c in u):
        score = max(score, 30)
    return score


def extract_top_signal_lines(text: str, *, max_lines: int = 30) -> list[str]:
    """
    From raw log text, pick the highest-scoring lines after stripping ANSI.

    Preserves original order among ties by sorting stable on (score, index).
    """
    cleaned = strip_ansi(text)
    lines = cleaned.splitlines()
    scored: list[tuple[int, int, str]] = []
    for i, line in enumerate(lines):
        s = score_line_for_incident_signal(line.strip())
        if s > 0:
            scored.append((s, i, line.rstrip()))
    scored.sort(key=lambda t: (-t[0], t[1]))
    out: list[str] = []
    seen: set[int] = set()
    for _, idx, line in scored:
        if idx in seen:
            continue
        seen.add(idx)
        out.append(line)
        if len(out) >= max_lines:
            break
    return out


def summarize_counts(text: str) -> dict[str, int]:
    """Count coarse signals in log text (for structured handoff)."""
    u = strip_ansi(text).upper()
    return {
        "error_hits": u.count("ERROR"),
        "exception_hits": u.count("EXCEPTION"),
        "warn_hits": u.count("WARN"),
        "fatal_hits": u.count("FATAL"),
        "traceback_hits": u.count("TRACEBACK"),
        "line_count": len(text.splitlines()),
    }
