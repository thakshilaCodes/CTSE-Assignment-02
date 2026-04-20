"""Logging/tracing for inputs, tool calls, and outputs (assignment requirement)."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("mas")


def log_agent_step(agent_name: str, payload: dict[str, Any]) -> None:
    """Record one agent step; replace/extend with structured tracing as needed."""
    logger.info("agent=%s payload=%s", agent_name, payload)


def log_tool_invocation(tool_name: str, arguments: dict[str, Any], result_snippet: str) -> None:
    """Record tool calls and a bounded result preview."""
    preview = result_snippet if len(result_snippet) <= 2000 else result_snippet[:2000] + "..."
    logger.info("tool=%s args=%s result_preview=%s", tool_name, arguments, preview)
