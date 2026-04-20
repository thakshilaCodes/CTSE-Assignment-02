"""Tests for correlation tools: signature extraction and incident lookup."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from mas.tools.correlation.query_incidents import query_known_incidents
from mas.tools.correlation.signatures import extract_signatures


def _seed_incident_db(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE incidents (
            signature TEXT,
            incident_class TEXT,
            severity TEXT,
            title TEXT,
            resolution TEXT,
            last_seen TEXT
        )
        """
    )
    cur.execute(
        """
        INSERT INTO incidents(signature, incident_class, severity, title, resolution, last_seen)
        VALUES(?, ?, ?, ?, ?, ?)
        """,
        (
            "HTTP_503",
            "UPSTREAM_OUTAGE",
            "high",
            "Upstream service unavailable",
            "Check dependency status and retry policy.",
            "2026-04-20T10:00:00Z",
        ),
    )
    conn.commit()
    conn.close()


def test_extract_signatures_from_ingest_findings() -> None:
    findings = """
    ERROR request failed status=503
    PaymentGatewayTimeout: upstream deadline exceeded
    Traceback (most recent call last):
    """
    signatures = extract_signatures(findings)
    assert signatures
    assert any("HTTP_503" == s or "503" in s for s in signatures)
    assert any("PaymentGatewayTimeout" in s for s in signatures)


def test_query_known_incidents_uses_sqlite_when_available(tmp_path: Path) -> None:
    db = tmp_path / "incidents.db"
    _seed_incident_db(db)
    rows = query_known_incidents("HTTP_503", db_path=str(db))
    assert rows
    assert rows[0]["source"] == "sqlite"
    assert rows[0]["incident_class"] == "UPSTREAM_OUTAGE"


def test_query_known_incidents_fallback_catalog() -> None:
    rows = query_known_incidents("connection refused", db_path=None)
    assert rows
    assert any(r["source"] == "fallback_catalog" for r in rows)
