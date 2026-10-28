"""PostgreSQL connection helpers and schema bootstrap."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

import psycopg
from pgvector.psycopg import register_vector
from psycopg.rows import dict_row

from src.config import DATABASE_URL, ROOT_DIR

SCHEMA_PATH = ROOT_DIR / "sql" / "schema.sql"


def require_database_url() -> str:
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is missing. Copy .env.example to .env and set your "
            "PostgreSQL connection string."
        )
    return DATABASE_URL


@contextmanager
def get_connection():
    conn = psycopg.connect(require_database_url(), row_factory=dict_row)
    try:
        conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        register_vector(conn)
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    with get_connection() as conn:
        conn.execute(sql)
