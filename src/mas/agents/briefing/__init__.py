"""Incident briefing agent — produces the final human-readable incident report."""

from mas.agents.briefing.agent import BRIEFING_OUTPUT_HINT, SYSTEM_PROMPT
from mas.agents.briefing.pipeline import run_briefing_pipeline
from mas.agents.briefing.report import BriefingReport

__all__ = [
    "BRIEFING_OUTPUT_HINT",
    "BriefingReport",
    "SYSTEM_PROMPT",
    "run_briefing_pipeline",
]
