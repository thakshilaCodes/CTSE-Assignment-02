"""Optional shared helpers or scenario data for ingest evaluation (not pytest)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class IngestEvalScenario:
    """Named fixture for ingest tests: raw log text and signals we expect to remain extractable."""

    name: str
    log_body: str
    expected_signals: tuple[str, ...]


# Typical application log: HTTP error + stack flavor for downstream correlation signatures.
INGEST_FINDINGS_PAYMENT_TIMEOUT: str = """\
2025-04-01T10:00:01Z payment-service ERROR PaymentGatewayTimeout: deadline exceeded after 30s
  File "/app/payment.py", line 42, in charge
ConnectionError: upstream payment provider unreachable
status=503 trace_id=abc123
"""

INGEST_FINDINGS_UPSTREAM_503: str = """\
2025-04-01T09:59:00Z edge-proxy WARN retried=3
2025-04-01T09:59:02Z edge-proxy ERROR upstream dependency returned HTTP 503
TRACEBACK (most recent call last):
  http.client.RemoteDisconnected
"""

# Benign / low-signal log for contrast (fewer ERROR lines).
INGEST_FINDINGS_MOSTLY_INFO: str = """\
2025-04-01T08:00:00Z app INFO request completed in 12ms
2025-04-01T08:00:01Z app INFO health check ok
"""

SCENARIOS: tuple[IngestEvalScenario, ...] = (
    IngestEvalScenario(
        name="payment_timeout",
        log_body=INGEST_FINDINGS_PAYMENT_TIMEOUT,
        expected_signals=("503", "PaymentGatewayTimeout", "ERROR"),
    ),
    IngestEvalScenario(
        name="upstream_503",
        log_body=INGEST_FINDINGS_UPSTREAM_503,
        expected_signals=("503", "ERROR", "TRACEBACK"),
    ),
)

# Paths that must never resolve under normal allowlists (security evaluation strings).
PATH_OUTSIDE_ALLOWLIST_EXAMPLES: tuple[str, ...] = (
    "/etc/passwd",
    "C:\\Windows\\System32\\config\\SAM",
    "../../../etc/shadow",
)

# Relative filename safe for writing under a temp `artifacts/logs`-style directory.
def safe_sample_log_filename(component: str = "sample_app") -> str:
    """Return a conservative log filename (no path separators)."""
    safe = "".join(c for c in component if c.isalnum() or c in ("-", "_")).strip("-_") or "sample"
    return f"{safe}.log"


def allowed_subdir_for_tests(base: Path, *parts: str) -> Path:
    """Build e.g. ``base / 'artifacts' / 'logs'`` for tests that need a realistic tree."""
    p = base
    for part in parts:
        p = p / part
    return p
