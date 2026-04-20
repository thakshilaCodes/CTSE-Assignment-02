"""Extract incident signatures from ingest findings text."""

from __future__ import annotations

import re
from collections import Counter

HTTP_STATUS_RE = re.compile(r"\b([45]\d{2})\b")
EXCEPTION_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*(?:Error|Exception|Timeout))\b")
KEYWORD_RE = re.compile(
    r"\b(database|db|connection refused|timeout|upstream|payment|gateway|auth|rate limit|traceback)\b",
    re.IGNORECASE,
)


def extract_signatures(ingest_findings: str, *, limit: int = 12) -> list[str]:
    """
    Extract likely correlation query signatures from ingest findings.

    The output is ranked by frequency and usefulness (exceptions/status codes first).
    """
    if not ingest_findings.strip():
        return []

    counter: Counter[str] = Counter()
    for m in HTTP_STATUS_RE.finditer(ingest_findings):
        counter[f"HTTP_{m.group(1)}"] += 3
    for m in EXCEPTION_RE.finditer(ingest_findings):
        counter[m.group(1)] += 4
    for m in KEYWORD_RE.finditer(ingest_findings):
        counter[m.group(1).lower()] += 2

    if not counter:
        words = [w.strip("`.,:;()[]{}").lower() for w in ingest_findings.split()]
        for w in words:
            if len(w) >= 5 and w.isalpha():
                counter[w] += 1

    ranked = [sig for sig, _ in counter.most_common(limit)]
    return ranked
