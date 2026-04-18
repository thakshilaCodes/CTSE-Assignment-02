"""Format the final incident briefing (template or markdown)."""

from __future__ import annotations


def format_incident_markdown(
    title: str,
    severity: str,
    summary: str,
    actions: list[str],
) -> str:
    """
    Render a fixed-layout incident markdown brief.

    Args:
        title: Short incident title.
        severity: Severity label (e.g. SEV1, SEV2).
        summary: One-paragraph summary.
        actions: Bullet list of recommended actions.

    Returns:
        Markdown string ready to save or display.
    """
    bullets = "\n".join(f"- {a}" for a in actions) if actions else "- (none)"
    return f"# {title}\n\n**Severity:** {severity}\n\n## Summary\n{summary}\n\n## Actions\n{bullets}\n"
