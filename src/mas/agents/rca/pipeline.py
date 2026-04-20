"""Deterministic RCA pipeline with optional Ollama refinement."""

from __future__ import annotations

from mas.agents.rca.agent import SYSTEM_PROMPT
from mas.agents.rca.ollama import refine_rca_summary
from mas.agents.rca.report import RCAHypothesis, RCAReport
from mas.core.observability import log_agent_step, log_tool_invocation
from mas.tools.rca import (
    build_structured_evidence,
    extract_error_signals,
    parse_correlation_summary,
)


def _build_hypotheses(incident_class: str, signals: list[str]) -> list[RCAHypothesis]:
    joined = ", ".join(signals[:6]) if signals else "limited signals"
    base = incident_class.upper()

    if base == "UPSTREAM_OUTAGE":
        return [
            RCAHypothesis(
                rank=1,
                title="Upstream dependency outage or saturation",
                likelihood="high",
                supporting_evidence=[f"Signals include: {joined}", "Correlation class is UPSTREAM_OUTAGE"],
                disproof_checks=[
                    "Check upstream status/health endpoint during failure window",
                    "Verify retries fail across multiple services, not a single node",
                ],
            ),
            RCAHypothesis(
                rank=2,
                title="Network path instability to dependency",
                likelihood="medium",
                supporting_evidence=["Timeout/503-like signal pattern can come from network hops"],
                disproof_checks=[
                    "Inspect packet loss/latency metrics between services",
                    "Validate DNS and service discovery resolution consistency",
                ],
            ),
        ]
    if base == "DB_CONNECTIVITY":
        return [
            RCAHypothesis(
                rank=1,
                title="Database service unreachable",
                likelihood="high",
                supporting_evidence=[f"Signals include: {joined}", "Correlation indicates DB_CONNECTIVITY"],
                disproof_checks=[
                    "Confirm DB process and listener ports are healthy",
                    "Test connection from app host with same credentials",
                ],
            ),
            RCAHypothesis(
                rank=2,
                title="Credential or connection string misconfiguration",
                likelihood="medium",
                supporting_evidence=["Connectivity errors can be caused by invalid DSN/auth settings"],
                disproof_checks=[
                    "Diff deployed env vars against known-good release",
                    "Rotate credentials and validate auth failure logs",
                ],
            ),
        ]

    return [
        RCAHypothesis(
            rank=1,
            title="Unhandled exception in application path",
            likelihood="medium",
            supporting_evidence=[f"Observed signals: {joined}"],
            disproof_checks=[
                "Reproduce with same input payload and capture stack trace",
                "Verify if error disappears in previous known-good build",
            ],
        ),
        RCAHypothesis(
            rank=2,
            title="Resource saturation causing secondary failures",
            likelihood="low",
            supporting_evidence=["Mixed error signals without single dominant class"],
            disproof_checks=[
                "Inspect CPU/memory/thread pool metrics near incident time",
                "Check queue backlog and timeout escalation chain",
            ],
        ),
    ]


def run_rca_pipeline(
    *,
    ingest_findings: str,
    correlation_findings: str,
    use_ollama: bool = True,
) -> RCAReport:
    """
    Build RCA hypotheses from ingest + correlation findings.

    Output is deterministic markdown with optional local-Ollama refinement.
    """
    evidence = build_structured_evidence(ingest_findings, correlation_findings)
    log_tool_invocation("build_structured_evidence", {"ingest_len": len(ingest_findings)}, evidence["merged"][:800])

    signals = extract_error_signals(evidence["ingest"], limit=12)
    log_tool_invocation("extract_error_signals", {"limit": 12}, str(signals))

    incident_class, confidence = parse_correlation_summary(evidence["correlation"])
    incident_class = incident_class or "UNKNOWN"
    confidence = confidence or "low"

    hypotheses = _build_hypotheses(incident_class, signals)

    lines: list[str] = [
        "## RCA hypotheses",
        "",
        "### Input context",
        "",
        f"- Incident class from correlation: `{incident_class}`",
        f"- Correlation confidence: `{confidence}`",
        f"- Extracted error signals: {', '.join(signals) if signals else '(none)'}",
        "",
        "### Ranked hypotheses",
        "",
    ]
    for h in hypotheses:
        lines.append(f"#### {h.rank}. {h.title}")
        lines.append(f"- Likelihood: `{h.likelihood}`")
        lines.append("- Supporting evidence:")
        for e in h.supporting_evidence:
            lines.append(f"  - {e}")
        lines.append("- Disproof checks:")
        for c in h.disproof_checks:
            lines.append(f"  - {c}")
        lines.append("")

    lines.extend(
        [
            "### Notes for briefing agent",
            "",
            "- Highlight uncertainty if top two hypotheses are close in likelihood.",
            "- Include concrete next validation steps from disproof checks.",
        ]
    )

    summary = "\n".join(lines).strip()
    report = RCAReport(
        incident_class=incident_class,
        confidence=confidence,
        hypotheses=hypotheses,
        summary_markdown=summary,
    )

    if use_ollama:
        refined = refine_rca_summary(SYSTEM_PROMPT, summary)
        if refined:
            report.ollama_refinement = refined
            log_agent_step("rca", {"ollama_refinement_chars": len(refined)})

    log_agent_step(
        "rca",
        {
            "incident_class": incident_class,
            "confidence": confidence,
            "hypothesis_count": len(hypotheses),
        },
    )
    return report
