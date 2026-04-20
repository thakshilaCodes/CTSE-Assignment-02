"""Briefing stage: generate final operator markdown from prior stage outputs."""

from __future__ import annotations

from mas.agents.briefing.agent import SYSTEM_PROMPT
from mas.agents.briefing.ollama import refine_briefing
from mas.agents.briefing.report import BriefingReport
from mas.core.observability import log_agent_step, log_tool_invocation
from mas.tools.briefing import (
    extract_incident_class,
    extract_top_actions,
    format_incident_markdown,
    infer_severity,
    summarize_user_impact,
)


def _derive_likely_root_cause(rca_hypotheses: str) -> str:
    for line in rca_hypotheses.splitlines():
        s = line.strip()
        if s.startswith("#### 1.") or s.startswith("1. "):
            return s.replace("####", "").strip()
    return "Top RCA hypothesis requires additional validation."


def run_briefing_pipeline(
    *,
    ingest_findings: str,
    correlation_findings: str,
    rca_hypotheses: str,
    use_ollama: bool = True,
) -> BriefingReport:
    """Build final briefing markdown from global-state inputs."""
    severity = infer_severity(ingest_findings, correlation_findings, rca_hypotheses)
    incident_class = extract_incident_class(correlation_findings, rca_hypotheses)
    user_impact = summarize_user_impact(ingest_findings)
    actions = extract_top_actions(rca_hypotheses, limit=6)
    likely_root_cause = _derive_likely_root_cause(rca_hypotheses)

    log_tool_invocation("infer_severity", {}, severity)
    log_tool_invocation("extract_incident_class", {}, incident_class)
    log_tool_invocation("extract_top_actions", {"limit": 6}, str(actions))

    title = f"{incident_class.replace('_', ' ').title()} Incident Briefing"
    summary = (
        f"This incident is currently classified as {incident_class} at {severity}. "
        "The report below summarizes user impact, likely root cause, and immediate mitigations."
    )
    follow_up = [
        "Confirm mitigation effectiveness with error-rate and latency monitoring.",
        "Update incident history with validated root cause and timeline.",
    ]
    markdown = format_incident_markdown(
        title=title,
        severity=severity,
        incident_class=incident_class,
        user_impact=user_impact,
        summary=summary,
        likely_root_cause=likely_root_cause,
        actions=actions,
        follow_up_checks=follow_up,
    )
    report = BriefingReport(
        title=title,
        severity=severity,
        incident_class=incident_class,
        markdown=markdown,
    )

    if use_ollama:
        refined = refine_briefing(SYSTEM_PROMPT, markdown)
        if refined:
            report.ollama_refinement = refined
            log_agent_step("briefing", {"ollama_refinement_chars": len(refined)})

    log_agent_step(
        "briefing",
        {
            "severity": severity,
            "incident_class": incident_class,
            "actions_count": len(actions),
        },
    )
    return report
