"""Logging/tracing for inputs, tool calls, and outputs (assignment requirement)."""

from __future__ import annotations

import logging
import os
from typing import Any

_LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def configure_observability(*, level: int = logging.INFO) -> None:
    """
    Attach handlers so agent/tool traces are visible (console and optional file).

    Set ``MAS_LOG_FILE`` to append the same lines to a trace file (e.g. ``artifacts/logs/mas_trace.log``).
    """
    mas_logger = logging.getLogger("mas")
    if mas_logger.handlers:
        mas_logger.setLevel(level)
        return

    mas_logger.setLevel(level)
    mas_logger.propagate = False

    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))
    mas_logger.addHandler(console)

    log_file = os.environ.get("MAS_LOG_FILE", "").strip()
    if log_file:
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))
        mas_logger.addHandler(fh)


logger = logging.getLogger("mas")


def log_agent_step(agent_name: str, payload: dict[str, Any]) -> None:
    """Record one agent step; replace/extend with structured tracing as needed."""
    configure_observability()
    logger.info("agent=%s payload=%s", agent_name, payload)


def log_tool_invocation(tool_name: str, arguments: dict[str, Any], result_snippet: str) -> None:
    """Record tool calls and a bounded result preview for observability."""
    configure_observability()
    preview = result_snippet if len(result_snippet) <= 2000 else result_snippet[:2000] + "..."
    logger.info("tool=%s args=%s result_preview=%s", tool_name, arguments, preview)