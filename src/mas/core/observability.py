"""Logging/tracing for inputs, tool calls, and outputs (assignment requirement)."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("mas")


def log_agent_step(agent_name: str, payload: dict[str, Any]) -> None:
    """Record one agent step; replace/extend with structured tracing as needed."""
    logger.info("agent=%s payload=%s", agent_name, payload)
