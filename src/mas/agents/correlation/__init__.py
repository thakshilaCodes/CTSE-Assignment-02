"""Correlation agent — links ingest signals with known incidents and outputs class/confidence."""

from mas.agents.correlation.agent import CORRELATION_OUTPUT_HINT, SYSTEM_PROMPT
from mas.agents.correlation.pipeline import run_correlation_pipeline
from mas.agents.correlation.report import CorrelationReport

__all__ = [
    "CORRELATION_OUTPUT_HINT",
    "CorrelationReport",
    "SYSTEM_PROMPT",
    "run_correlation_pipeline",
]
