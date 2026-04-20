"""Check local service connectivity for Ollama and PostgreSQL in one command."""

from __future__ import annotations

import argparse
import os
import sys
from typing import Any

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore[assignment]

try:
    import psycopg
except ImportError:
    psycopg = None  # type: ignore[assignment]


def check_ollama(host: str, timeout_s: float) -> tuple[bool, str]:
    """Check Ollama `/api/tags` health endpoint."""
    if httpx is None:
        return False, "httpx not installed"
    url = host.rstrip("/") + "/api/tags"
    try:
        with httpx.Client(timeout=timeout_s) as client:
            res = client.get(url)
            if res.status_code != 200:
                return False, f"HTTP {res.status_code} from {url}"
            data: Any = res.json()
    except Exception as e:  # noqa: BLE001 - surface error to user
        return False, f"{type(e).__name__}: {e}"

    models = data.get("models", []) if isinstance(data, dict) else []
    model_count = len(models) if isinstance(models, list) else 0
    return True, f"reachable ({model_count} model(s) listed)"


def check_postgres(timeout_s: float) -> tuple[bool, str]:
    """Check PostgreSQL connectivity and existence of `public.incidents` table."""
    if psycopg is None:
        return False, "psycopg not installed"

    required = ("PGHOST", "PGPORT", "PGDATABASE", "PGUSER", "PGPASSWORD")
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        return False, f"missing env vars: {', '.join(missing)}"

    try:
        conn = psycopg.connect(
            host=os.environ["PGHOST"],
            port=os.environ["PGPORT"],
            dbname=os.environ["PGDATABASE"],
            user=os.environ["PGUSER"],
            password=os.environ["PGPASSWORD"],
            connect_timeout=max(1, int(timeout_s)),
        )
        with conn:
            with conn.cursor() as cur:
                cur.execute("SELECT to_regclass('public.incidents')")
                reg = cur.fetchone()
                table_name = reg[0] if reg else None
                if table_name is None:
                    return False, "connected, but table public.incidents was not found"
                cur.execute("SELECT COUNT(*) FROM incidents")
                count_row = cur.fetchone()
                row_count = int(count_row[0]) if count_row else 0
                return True, f"connected, incidents table present ({row_count} row(s))"
    except Exception as e:  # noqa: BLE001 - surface error to user
        return False, f"{type(e).__name__}: {e}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check Ollama and PostgreSQL service connectivity.")
    parser.add_argument(
        "--ollama-host",
        default=os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434"),
        help="Ollama base URL (default: env OLLAMA_HOST or http://127.0.0.1:11434).",
    )
    parser.add_argument("--timeout", type=float, default=3.0, help="Network timeout in seconds.")
    args = parser.parse_args(argv)

    ok_ollama, msg_ollama = check_ollama(args.ollama_host, args.timeout)
    ok_pg, msg_pg = check_postgres(args.timeout)

    print(f"Ollama   : {'OK' if ok_ollama else 'FAIL'} - {msg_ollama}")
    print(f"Postgres : {'OK' if ok_pg else 'FAIL'} - {msg_pg}")

    return 0 if ok_ollama and ok_pg else 1


if __name__ == "__main__":
    raise SystemExit(main())
