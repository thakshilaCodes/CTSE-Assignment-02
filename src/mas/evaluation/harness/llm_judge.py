"""Optional LLM-as-a-Judge evaluation using local Ollama (assignment-friendly, zero cloud cost)."""

from __future__ import annotations

import json
import os
import re
from typing import Any

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore[misc, assignment]


def _skip_judge() -> bool:
    return os.environ.get("OLLAMA_SKIP", "").lower() in {"1", "true", "yes"}


def _ollama_chat(messages: list[dict[str, str]], *, timeout_s: float = 90.0) -> str | None:
    if _skip_judge() or httpx is None:
        return None
    host = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
    model = os.environ.get("OLLAMA_MODEL", "llama3:8b")
    url = f"{host}/api/chat"
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0.1, "num_predict": 512},
    }
    try:
        with httpx.Client(timeout=timeout_s) as client:
            r = client.post(url, json=payload)
            r.raise_for_status()
            data = r.json()
        msg = data.get("message", {}).get("content", "")
        return msg.strip() if isinstance(msg, str) else None
    except Exception:
        return None


def _extract_json_object(text: str) -> dict[str, Any] | None:
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        return None
    try:
        out = json.loads(m.group(0))
        return out if isinstance(out, dict) else None
    except json.JSONDecodeError:
        return None


def judge_agent_output(
    *,
    agent_name: str,
    output_text: str,
    rubric: str,
) -> dict[str, Any]:
    """
    Ask a local SLM to score output against a rubric.

    Returns a dict with keys: ``pass`` (bool), ``score`` (0-1 float), ``issues`` (list[str]),
    ``raw_model`` (str|None). If Ollama is unavailable, returns a deterministic heuristic result.
    """
    system = (
        "You are a strict evaluator for a local incident-triage system. "
        "Respond with ONLY a JSON object, no markdown fences, with keys: "
        'pass (boolean), score (number 0-1), issues (array of short strings). '
        "Fail if the output appears to invent log lines, paths, or secrets not present in context."
    )
    user = f"Agent: {agent_name}\n\nRubric:\n{rubric}\n\nOutput to evaluate:\n{output_text[:8000]}"
    raw = _ollama_chat(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
    )
    if raw:
        parsed = _extract_json_object(raw)
        if parsed and "pass" in parsed:
            return {
                "pass": bool(parsed.get("pass")),
                "score": float(parsed.get("score", 0.0)),
                "issues": list(parsed.get("issues", [])) if isinstance(parsed.get("issues"), list) else [],
                "raw_model": raw,
                "source": "ollama",
            }

    # Offline fallback: non-LLM structural check only (CI-safe)
    ok = len(output_text.strip()) >= 10
    return {
        "pass": ok,
        "score": 0.5 if ok else 0.0,
        "issues": ["ollama_unavailable_or_non_json_response_use_fallback"],
        "raw_model": raw,
        "source": "fallback",
    }
