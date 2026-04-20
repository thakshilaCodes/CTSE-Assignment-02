"""Parse ingest/correlation text into RCA-relevant signals."""

from __future__ import annotations

import re
from collections import Counter

ERROR_KEYWORDS = (
    "timeout",
    "connection refused",
    "traceback",
    "exception",
    "503",
    "502",
    "500",
    "database",
    "upstream",
    "payment",
)

CLASS_RE = re.compile(r"Class:\s*`?([A-Z0-9_]+)`?", re.IGNORECASE)
CONF_RE = re.compile(r"Confidence:\s*`?([a-z]+)`?", re.IGNORECASE)


def extract_error_signals(ingest_findings: str, *, limit: int = 15) -> list[str]:
    """Extract high-signal phrases from ingest text."""
    text = ingest_findings.lower()
    counter: Counter[str] = Counter()
    for kw in ERROR_KEYWORDS:
        if kw in text:
            counter[kw] += text.count(kw)
    return [k for k, _ in counter.most_common(limit)]


def parse_correlation_summary(correlation_findings: str) -> tuple[str | None, str | None]:
    """Parse candidate class and confidence from correlation markdown."""
    class_match = CLASS_RE.search(correlation_findings)
    conf_match = CONF_RE.search(correlation_findings)
    incident_class = class_match.group(1).upper() if class_match else None
    confidence = conf_match.group(1).lower() if conf_match else None
    return incident_class, confidence
