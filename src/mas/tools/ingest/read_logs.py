"""Read and excerpt local log files for the ingest agent (implement with path allowlists)."""

from __future__ import annotations


def read_log_excerpt(file_path: str, max_lines: int = 200) -> str:
    """
    Read up to ``max_lines`` from a log file under an allowed project directory.

    Args:
        file_path: Absolute or project-relative path to a log file.
        max_lines: Maximum number of lines to return from the start of the file.

    Returns:
        Log content as a single string, or an error message if the read fails.
    """
    # Stub: replace with validated open() and allowlist checks
    return f"[stub] would read {max_lines} lines from {file_path!r}"
