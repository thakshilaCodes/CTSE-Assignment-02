"""Tools used by the log ingest agent."""

from mas.tools.ingest.discover_logs import list_log_candidates
from mas.tools.ingest.normalize import (
    extract_top_signal_lines,
    score_line_for_incident_signal,
    strip_ansi,
    summarize_counts,
)
from mas.tools.ingest.paths import default_allowed_roots, load_allowed_roots_from_env, resolve_path_under_roots
from mas.tools.ingest.read_logs import log_file_stats, read_log_excerpt, read_log_tail

__all__ = [
    "default_allowed_roots",
    "extract_top_signal_lines",
    "list_log_candidates",
    "load_allowed_roots_from_env",
    "log_file_stats",
    "read_log_excerpt",
    "read_log_tail",
    "resolve_path_under_roots",
    "score_line_for_incident_signal",
    "strip_ansi",
    "summarize_counts",
]
