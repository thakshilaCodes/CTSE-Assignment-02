"""System prompt and config for the briefing agent."""

SYSTEM_PROMPT = """You are the Incident Briefing agent.

You receive ingest, correlation, and RCA outputs and produce the final operator report.

Rules:
- Keep wording concise and actionable.
- Do not invent facts not present in previous stage outputs.
- Preserve severity/class consistency from upstream evidence.
- Always include immediate mitigations and follow-up checks.
"""

BRIEFING_OUTPUT_HINT = {
    "title": "string",
    "severity": "SEV1|SEV2|SEV3",
    "incident_class": "string",
    "sections": [
        "Incident Snapshot",
        "Executive Summary",
        "Likely Root Cause",
        "Immediate Mitigations",
        "Follow-up Checks",
    ],
}
