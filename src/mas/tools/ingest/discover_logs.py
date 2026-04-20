"""Discover candidate log files under allowed roots (bounded search)."""

from __future__ import annotations

import os
from pathlib import Path

from mas.tools.ingest.paths import load_allowed_roots_from_env

_LOG_SUFFIXES = frozenset({".log", ".out", ".txt"})
_NAME_HINTS = ("log", "error", "trace", "crash")


def list_log_candidates(
    *,
    max_files: int = 50,
    max_depth: int = 4,
    roots: list[Path] | None = None,
) -> list[str]:
    """
    List paths to probable log files under allowed roots.

    Includes files ending with ``.log``, ``.out``, ``.txt``, or whose name suggests logging.
    Search is depth-limited and stops after ``max_files`` paths.

    Args:
        max_files: Maximum number of paths to return.
        max_depth: Maximum directory depth below each root (0 = root only).
        roots: Optional allowlist; defaults to :func:`load_allowed_roots_from_env`.

    Returns:
        Sorted absolute paths as strings (may be empty).
    """
    roots = roots if roots is not None else load_allowed_roots_from_env()
    found: list[str] = []

    def consider(p: Path) -> None:
        if len(found) >= max_files:
            return
        name = p.name.lower()
        suf = p.suffix.lower()
        if suf in _LOG_SUFFIXES:
            found.append(str(p.resolve()))
            return
        if any(h in name for h in _NAME_HINTS) and p.is_file():
            found.append(str(p.resolve()))

    for root in roots:
        if not root.exists():
            continue
        root = root.resolve()
        base_depth = len(root.parts)
        for dirpath, dirnames, filenames in os.walk(root, topdown=True):
            current = Path(dirpath)
            depth = len(current.parts) - base_depth
            if depth > max_depth:
                dirnames[:] = []
                continue
            for fn in filenames:
                if len(found) >= max_files:
                    return sorted(found)
                consider(current / fn)

    return sorted(found)
