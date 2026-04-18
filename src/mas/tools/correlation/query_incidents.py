"""Query local incident history (e.g. SQLite) for the correlation agent."""

from __future__ import annotations


def query_known_incidents(error_signature: str, limit: int = 10) -> list[dict[str, str]]:
    """
    Look up past incidents matching an error signature or keyword.

    Args:
        error_signature: Short text or code to match (e.g. exception name, HTTP status).
        limit: Maximum number of rows to return.

    Returns:
        Rows as dictionaries with string values (stub returns empty list).
    """
    return []
