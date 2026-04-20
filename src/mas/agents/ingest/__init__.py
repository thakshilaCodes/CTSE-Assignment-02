"""Log ingest agent: prompts, Ollama SLM, pipeline, and tool-backed evidence."""

from mas.agents.ingest.agent import INGEST_OUTPUT_HINT, SYSTEM_PROMPT
from mas.agents.ingest.pipeline import run_ingest_pipeline
from mas.agents.ingest.report import IngestReport

__all__ = [
    "INGEST_OUTPUT_HINT",
    "IngestReport",
    "SYSTEM_PROMPT",
    "run_ingest_pipeline",
]
