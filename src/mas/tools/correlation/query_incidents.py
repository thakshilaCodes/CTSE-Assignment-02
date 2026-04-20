"""Query local incident history (PostgreSQL first, then SQLite, then fallback catalog)."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

try:
    import psycopg
except ImportError:  # pragma: no cover - optional dependency in some environments
    psycopg = None  # type: ignore[misc, assignment]

FALLBACK_INCIDENTS: tuple[dict[str, str], ...] = (
    {
        "signature": "HTTP_503",
        "incident_class": "UPSTREAM_OUTAGE",
        "severity": "high",
        "title": "Dependency service unavailable",
        "resolution": "Retry with backoff and check upstream health endpoints.",
        "source": "fallback_catalog",
    },
    {
        "signature": "PaymentGatewayTimeout",
        "incident_class": "PAYMENT_GATEWAY_TIMEOUT",
        "severity": "high",
        "title": "Payment gateway timeout spike",
        "resolution": "Increase gateway timeout and verify provider latency.",
        "source": "fallback_catalog",
    },
    {
        "signature": "connection refused",
        "incident_class": "DB_CONNECTIVITY",
        "severity": "critical",
        "title": "Database connection refused",
        "resolution": "Check DB process, firewall rules, and connection strings.",
        "source": "fallback_catalog",
    },
    {
        "signature": "Traceback",
        "incident_class": "UNHANDLED_EXCEPTION",
        "severity": "medium",
        "title": "Unhandled exception path",
        "resolution": "Capture stack trace context and patch failing function.",
        "source": "fallback_catalog",
    },
)


def _query_postgres_incidents(
    error_signature: str,
    *,
    limit: int,
) -> list[dict[str, str]]:
    """
    Query incidents from PostgreSQL using PG* environment variables.

    Required env vars for connection:
    - PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD
    """
    if psycopg is None:
        return []

    required = ("PGHOST", "PGPORT", "PGDATABASE", "PGUSER", "PGPASSWORD")
    if not all(os.environ.get(k) for k in required):
        return []

    query = """
    SELECT signature, incident_class, severity, title, resolution, COALESCE(last_seen::text, '') AS last_seen
    FROM incidents
    WHERE LOWER(signature) LIKE '%' || LOWER(%s) || '%'
       OR LOWER(title) LIKE '%' || LOWER(%s) || '%'
       OR LOWER(incident_class) LIKE '%' || LOWER(%s) || '%'
    ORDER BY CASE
        WHEN LOWER(signature) = LOWER(%s) THEN 0
        WHEN LOWER(signature) LIKE LOWER(%s) || '%' THEN 1
        ELSE 2
    END, created_at DESC NULLS LAST
    LIMIT %s
    """
    rows: list[dict[str, str]] = []
    try:
        with psycopg.connect(
            host=os.environ["PGHOST"],
            port=int(os.environ["PGPORT"]),
            dbname=os.environ["PGDATABASE"],
            user=os.environ["PGUSER"],
            password=os.environ["PGPASSWORD"],
        ) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    query,
                    (
                        error_signature,
                        error_signature,
                        error_signature,
                        error_signature,
                        error_signature,
                        limit,
                    ),
                )
                for row in cur.fetchall():
                    rows.append(
                        {
                            "signature": str(row[0]),
                            "incident_class": str(row[1]),
                            "severity": str(row[2]),
                            "title": str(row[3]),
                            "resolution": str(row[4]),
                            "last_seen": str(row[5]),
                            "source": "postgres",
                        }
                    )
    except Exception:
        return []
    return rows


def _query_sqlite_incidents(
    db_path: Path,
    error_signature: str,
    *,
    limit: int,
) -> list[dict[str, str]]:
    if not db_path.exists():
        return []
    query = """
    SELECT signature, incident_class, severity, title, resolution, COALESCE(last_seen, '') AS last_seen
    FROM incidents
    WHERE LOWER(signature) LIKE '%' || LOWER(?) || '%'
       OR LOWER(title) LIKE '%' || LOWER(?) || '%'
       OR LOWER(incident_class) LIKE '%' || LOWER(?) || '%'
    ORDER BY CASE
        WHEN LOWER(signature) = LOWER(?) THEN 0
        WHEN LOWER(signature) LIKE LOWER(?) || '%' THEN 1
        ELSE 2
    END, rowid DESC
    LIMIT ?
    """
    results: list[dict[str, str]] = []
    conn: sqlite3.Connection | None = None
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(query, (error_signature, error_signature, error_signature, error_signature, error_signature, limit))
        for row in cur.fetchall():
            results.append(
                {
                    "signature": str(row["signature"]),
                    "incident_class": str(row["incident_class"]),
                    "severity": str(row["severity"]),
                    "title": str(row["title"]),
                    "resolution": str(row["resolution"]),
                    "last_seen": str(row["last_seen"]),
                    "source": "sqlite",
                }
            )
    except sqlite3.Error:
        return []
    finally:
        try:
            if conn is not None:
                conn.close()
        except Exception:
            pass
    return results


def query_known_incidents(
    error_signature: str,
    limit: int = 10,
    *,
    db_path: str | None = None,
) -> list[dict[str, str]]:
    """
    Look up past incidents matching an error signature or keyword.

    Args:
        error_signature: Short text or code to match (e.g. exception name, HTTP status).
        limit: Maximum number of rows to return.
        db_path: Optional SQLite file path with an ``incidents`` table.

    Returns:
        Rows as dictionaries with values from PostgreSQL, SQLite, and fallback catalog.
    """
    if not error_signature.strip():
        return []

    rows: list[dict[str, str]] = []
    rows.extend(_query_postgres_incidents(error_signature, limit=limit))
    if db_path:
        rows.extend(_query_sqlite_incidents(Path(db_path), error_signature, limit=limit))

    signature_lower = error_signature.lower()
    for item in FALLBACK_INCIDENTS:
        if len(rows) >= limit:
            break
        haystack = f"{item['signature']} {item['title']} {item['incident_class']}".lower()
        if signature_lower in haystack:
            rows.append(dict(item))

    # Dedupe by (signature, incident_class, source)
    seen: set[tuple[str, str, str]] = set()
    unique: list[dict[str, str]] = []
    for row in rows:
        key = (
            row.get("signature", ""),
            row.get("incident_class", ""),
            row.get("source", ""),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(row)
        if len(unique) >= limit:
            break
    return unique
