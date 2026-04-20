"""Read log file excerpts and tails with encoding safety and size limits."""

from __future__ import annotations

from pathlib import Path

from mas.tools.ingest.paths import load_allowed_roots_from_env, resolve_path_under_roots

_DEFAULT_MAX_LINES = 500
_DEFAULT_MAX_BYTES_HEAD = 512 * 1024
_DEFAULT_MAX_TAIL_BYTES = 512 * 1024


def read_log_excerpt(
    file_path: str,
    max_lines: int = 200,
    *,
    max_bytes: int = _DEFAULT_MAX_BYTES_HEAD,
    roots: list[Path] | None = None,
) -> str:
    """
    Read up to ``max_lines`` from the start of a log file under an allowed root.

    Uses UTF-8 with replacement for invalid bytes. Stops after ``max_bytes`` of raw data
    to avoid loading huge files into memory.

    Args:
        file_path: Path to a log file (relative to CWD or absolute).
        max_lines: Maximum number of lines to return from the beginning.
        max_bytes: Hard cap on bytes read from the file start.
        roots: Optional allowlist; defaults to :func:`load_allowed_roots_from_env`.

    Returns:
        Log text, or a single-line error message prefixed with ``ERROR:``.
    """
    roots = roots if roots is not None else load_allowed_roots_from_env()
    resolved, err = resolve_path_under_roots(file_path, roots)
    if err or resolved is None:
        return f"ERROR: {err or 'access denied'}"

    if not resolved.is_file():
        return f"ERROR: Not a file: {resolved}"

    try:
        raw = resolved.read_bytes()[:max_bytes]
    except OSError as e:
        return f"ERROR: Cannot read file: {e}"

    text = raw.decode("utf-8", errors="replace")
    lines = text.splitlines()
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        body = "\n".join(lines)
        return body + f"\n... truncated to {max_lines} lines (head)"
    return "\n".join(lines)


def read_log_tail(
    file_path: str,
    max_lines: int = 200,
    *,
    max_bytes: int = _DEFAULT_MAX_TAIL_BYTES,
    roots: list[Path] | None = None,
) -> str:
    """
    Read up to ``max_lines`` from the end of a log file (typical for recent errors).

    For files larger than ``max_bytes``, only the last ``max_bytes`` bytes are decoded
    (sufficient for recent stack traces in most cases).

    Args:
        file_path: Path to a log file.
        max_lines: Maximum number of lines to return from the end.
        max_bytes: Maximum tail window in bytes to load.
        roots: Optional allowlist; defaults to :func:`load_allowed_roots_from_env`.

    Returns:
        Log text (most recent lines at the end), or ``ERROR: ...`` message.
    """
    roots = roots if roots is not None else load_allowed_roots_from_env()
    resolved, err = resolve_path_under_roots(file_path, roots)
    if err or resolved is None:
        return f"ERROR: {err or 'access denied'}"

    if not resolved.is_file():
        return f"ERROR: Not a file: {resolved}"

    try:
        size = resolved.stat().st_size
    except OSError as e:
        return f"ERROR: Cannot stat file: {e}"

    if size == 0:
        return ""

    try:
        with resolved.open("rb") as f:
            if size <= max_bytes:
                raw = f.read()
            else:
                f.seek(size - max_bytes)
                raw = f.read()
    except OSError as e:
        return f"ERROR: Cannot read file: {e}"

    text = raw.decode("utf-8", errors="replace")
    lines = text.splitlines()
    if len(lines) > max_lines:
        lines = lines[-max_lines:]
        body = "\n".join(lines)
        return f"... truncated to last {max_lines} lines (tail)\n" + body
    return "\n".join(lines)


def log_file_stats(
    file_path: str,
    *,
    roots: list[Path] | None = None,
) -> str:
    """
    Return human-readable size and mtime for a log file under allowed roots.

    Args:
        file_path: Path to a file.
        roots: Optional allowlist.

    Returns:
        A short text summary or ``ERROR: ...``.
    """
    roots = roots if roots is not None else load_allowed_roots_from_env()
    resolved, err = resolve_path_under_roots(file_path, roots)
    if err or resolved is None:
        return f"ERROR: {err or 'access denied'}"

    if not resolved.is_file():
        return f"ERROR: Not a file: {resolved}"

    try:
        st = resolved.stat()
    except OSError as e:
        return f"ERROR: {e}"

    from datetime import datetime, timezone

    mtime = datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat()
    return f"path={resolved} size_bytes={st.st_size} mtime_utc={mtime}"
