"""Local Ollama (SLM) client for the ingest agent — uses ``/api/chat`` on your machine."""

from __future__ import annotations

import os
from typing import Any

try:
    import httpx
except ImportError:  # pragma: no cover
    httpx = None  # type: ignore[misc, assignment]


def _skip_ollama() -> bool:
    return os.environ.get("OLLAMA_SKIP", "").lower() in {"1", "true", "yes"}


def ollama_base_url() -> str:
    """Base URL, e.g. ``http://127.0.0.1:11434`` (see Ollama docs)."""
    return os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")


def ollama_model() -> str:
    """Model tag pulled in Ollama, e.g. ``llama3:8b``, ``phi3``, ``qwen2.5``."""
    return os.environ.get("OLLAMA_MODEL", "llama3:8b")


def is_ollama_available(*, timeout_s: float = 3.0) -> bool:
    """
    Return True if the Ollama HTTP server responds (``GET /api/tags``).

    Use before running the pipeline in demos to fail fast with a clear message.
    """
    if httpx is None or _skip_ollama():
        return False
    url = f"{ollama_base_url()}/api/tags"
    try:
        with httpx.Client(timeout=timeout_s) as client:
            r = client.get(url)
            return r.status_code == 200
    except Exception:
        return False


def _chat_options() -> dict[str, Any]:
    """Low temperature by default for grounded ingest; override via ``OLLAMA_OPTIONS_JSON``."""
    raw = os.environ.get("OLLAMA_OPTIONS_JSON", "").strip()
    if raw:
        import json

        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
    return {"temperature": 0.2, "num_predict": 1024}


def ollama_chat(
    messages: list[dict[str, str]],
    *,
    timeout_s: float = 180.0,
) -> str | None:
    """
    Call ``POST /api/chat`` with the given OpenAI-style messages.

    Returns assistant text, or ``None`` if skipped, unreachable, or error.
    """
    if _skip_ollama() or httpx is None:
        return None

    payload: dict[str, Any] = {
        "model": ollama_model(),
        "messages": messages,
        "stream": False,
        "options": _chat_options(),
    }

    url = f"{ollama_base_url()}/api/chat"
    try:
        with httpx.Client(timeout=timeout_s) as client:
            r = client.post(url, json=payload)
            r.raise_for_status()
            data = r.json()
    except Exception:
        return None

    try:
        msg = data["message"]["content"]
    except (KeyError, TypeError):
        return None
    if isinstance(msg, str) and msg.strip():
        return msg.strip()
    return None


def build_ingest_user_message(evidence_markdown: str) -> str:
    """Wrap tool-backed markdown so the SLM knows it must not invent new log lines."""
    return (
        "Below is ONLY tool-backed log content and heuristics from our pipeline. "
        "Do not add stack traces, paths, or error codes that do not appear there.\n\n"
        + evidence_markdown.strip()
    )


def synthesize_ingest_with_ollama(system_prompt: str, evidence_markdown: str) -> str | None:
    """
    Run the ingest **agent persona** (``system_prompt``) over tool evidence via Ollama.

    This is the primary SLM step for ingest: it produces the operator-facing summary;
    raw excerpts remain in ``IngestReport.summary_markdown``.
    """
    if _skip_ollama() or httpx is None:
        return None

    user = build_ingest_user_message(evidence_markdown)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user},
    ]
    return ollama_chat(messages)
