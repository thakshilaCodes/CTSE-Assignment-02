"""Format the final incident briefing (fixed operator-friendly markdown layout)."""

from __future__ import annotations


def format_incident_markdown(
    title: str,
    severity: str,
    incident_class: str,
    user_impact: str,
    summary: str,
    likely_root_cause: str,
    actions: list[str],
    follow_up_checks: list[str] | None = None,
) -> str:
    """
    Render a fixed-layout incident markdown brief.

    Args:
        title: Short incident title.
        severity: Severity label (e.g. SEV1, SEV2).
        incident_class: Predicted incident class label.
        user_impact: Concise user-impact statement.
        summary: One-paragraph executive summary.
        likely_root_cause: Most likely root cause statement.
        actions: Bullet list of recommended actions.
        follow_up_checks: Optional extra verification checks.

    Returns:
        Markdown string ready to save or display.
    """
    action_bullets = "\n".join(f"- {a}" for a in actions) if actions else "- (none)"
    follow_bullets = (
        "\n".join(f"- {c}" for c in follow_up_checks)
        if follow_up_checks
        else "- Continue monitoring errors and latency after mitigation."
    )
    return (
        f"# {title}\n\n"
        f"**Severity:** {severity}\n\n"
        "## Incident Snapshot\n"
        f"- Class: `{incident_class}`\n"
        f"- User impact: {user_impact}\n\n"
        "## Executive Summary\n"
        f"{summary}\n\n"
        "## Likely Root Cause\n"
        f"{likely_root_cause}\n\n"
        "## Immediate Mitigations\n"
        f"{action_bullets}\n\n"
        "## Follow-up Checks\n"
        f"{follow_bullets}\n"
    )
