"""Resolve log paths against an explicit allowlist (security boundary for ingest tools)."""

from __future__ import annotations

import os
from pathlib import Path


def _split_roots(raw: str | None) -> list[Path]:
    if not raw or not raw.strip():
        return []
    return [Path(p.strip()).expanduser().resolve() for p in raw.split(",") if p.strip()]


def default_allowed_roots(cwd: Path | None = None) -> list[Path]:
    """
    Default directories ingest may read when ``MAS_INGEST_ALLOWED_ROOTS`` is unset.

    Uses ``cwd/artifacts/logs`` and ``cwd/logs`` if they exist; otherwise ``cwd`` only.
    """
    base = (cwd or Path.cwd()).resolve()
    candidates = [base / "artifacts" / "logs", base / "logs", base]
    roots: list[Path] = []
    for c in candidates:
        if c.exists() and c not in roots:
            roots.append(c.resolve())
    return roots if roots else [base]


def load_allowed_roots_from_env(cwd: Path | None = None) -> list[Path]:
    """
    Load allowed roots from ``MAS_INGEST_ALLOWED_ROOTS`` (comma-separated paths).

    If unset or empty, :func:`default_allowed_roots` is used.
    """
    raw = os.environ.get("MAS_INGEST_ALLOWED_ROOTS")
    roots = _split_roots(raw)
    return roots if roots else default_allowed_roots(cwd)


def resolve_path_under_roots(
    file_path: str,
    roots: list[Path],
) -> tuple[Path | None, str | None]:
    """
    Resolve ``file_path`` to an absolute path that must lie under one of ``roots``.

    Args:
        file_path: User-supplied path (absolute or relative to current working directory).
        roots: Allowed directory roots (absolute, resolved).

    Returns:
        ``(resolved_path, None)`` if allowed, or ``(None, error_message)``.
    """
    if not roots:
        return None, "No allowed roots configured; set MAS_INGEST_ALLOWED_ROOTS or use defaults."

    try:
        p = Path(file_path).expanduser()
        if not p.is_absolute():
            p = (Path.cwd() / p).resolve()
        else:
            p = p.resolve()
    except OSError as e:
        return None, f"Invalid path: {e}"

    for root in roots:
        r = root.resolve()
        try:
            p.relative_to(r)
            return p, None
        except ValueError:
            continue

    return None, (
        "Path is outside allowed ingest roots. "
        f"Allowed: {[str(r) for r in roots]}; got: {p}"
    )
