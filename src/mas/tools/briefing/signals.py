"""Briefing signal extraction and severity heuristics."""

from __future__ import annotations

import re

SEV_RE = re.compile(r"\b(critical|high|medium|low)\b", re.IGNORECASE)
CLASS_RE = re.compile(r"class:\s*`?([A-Z0-9_]+)`?", re.IGNORECASE)


def infer_severity(ingest_findings: str, correlation_findings: str, rca_hypotheses: str) -> str:
    """
    Infer incident severity using simple deterministic rules.

    Returns one of: ``SEV1``, ``SEV2``, ``SEV3``.
    """
    text = f"{ingest_findings}\n{correlation_findings}\n{rca_hypotheses}".lower()
    if any(token in text for token in ("critical", "sev1", "paymentgatewaytimeout", "connection refused")):
        return "SEV1"
    if any(token in text for token in ("high", "503", "timeout", "upstream_outage")):
        return "SEV2"
    return "SEV3"


def extract_incident_class(correlation_findings: str, rca_hypotheses: str) -> str:
    """Extract best incident class label from correlation or RCA text."""
    for source in (correlation_findings, rca_hypotheses):
        m = CLASS_RE.search(source)
        if m:
            return m.group(1).upper()
    return "UNKNOWN"


def extract_top_actions(rca_hypotheses: str, *, limit: int = 6) -> list[str]:
    """
    Extract actionable checks from RCA text.

    Pulls lines under disproof/next-step style bullets and falls back to generic actions.
    """
    actions: list[str] = []
    for raw in rca_hypotheses.splitlines():
        line = raw.strip().lstrip("-").strip()
        lower = line.lower()
        if not line:
            continue
        if any(k in lower for k in ("check ", "verify ", "inspect ", "test ", "confirm ", "validate ")):
            actions.append(line)
        if len(actions) >= limit:
            break

    if actions:
        return actions[:limit]
    return [
        "Validate top RCA hypothesis with service health checks.",
        "Collect missing telemetry around failure window.",
        "Prepare rollback/mitigation if impact increases.",
    ][:limit]


def summarize_user_impact(ingest_findings: str) -> str:
    """Generate a conservative user-impact statement from ingest signals."""
    text = ingest_findings.lower()
    if "checkout" in text or "payment" in text:
        return "Users may experience transaction failures on checkout/payment paths."
    if "503" in text or "timeout" in text:
        return "Users may encounter intermittent request failures and elevated latency."
    if "error" in text:
        return "Users may experience degraded reliability on affected endpoints."
    return "User impact is currently unclear; further monitoring is required."
