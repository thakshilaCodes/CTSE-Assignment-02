"""Optional Ollama refinement for RCA summaries."""

from __future__ import annotations

import os
from typing import Any

try:
    import httpx
except ImportError:  # pragma: no cover
    httpx = None  # type: ignore[misc, assignment]


def _skip() -> bool:
    return os.environ.get("OLLAMA_SKIP", "").lower() in {"1", "true", "yes"}


def _host() -> str:
    return os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")


def _model() -> str:
    return os.environ.get("OLLAMA_MODEL", "llama3:8b")


def refine_rca_summary(system_prompt: str, evidence_markdown: str, *, timeout_s: float = 120.0) -> str | None:
    """Refine deterministic RCA summary through local Ollama."""
    if _skip() or httpx is None:
        return None

    payload: dict[str, Any] = {
        "model": _model(),
        "stream": False,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    "Polish the RCA summary below without adding new facts. "
                    "Preserve evidence grounding and uncertainty notes.\n\n"
                    + evidence_markdown
                ),
            },
        ],
        "options": {"temperature": 0.2, "num_predict": 1024},
    }

    try:
        with httpx.Client(timeout=timeout_s) as client:
            res = client.post(f"{_host()}/api/chat", json=payload)
            res.raise_for_status()
            data = res.json()
    except Exception:
        return None

    msg = data.get("message", {}).get("content", "")
    if isinstance(msg, str) and msg.strip():
        return msg.strip()
    return None
