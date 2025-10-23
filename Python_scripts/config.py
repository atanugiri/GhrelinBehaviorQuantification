"""Configuration helpers for the GhrelinBehaviorQuantification project.

Provides:
- load_env(): loads from .env (python-dotenv) when present.
- get_database_url(): returns DATABASE_URL or composes it from parts.
- get_conn(): attempts to connect to Postgres using psycopg2 with retries.
- get_data_dir(): returns DATA_DIR env var or project data/ fallback.
- read_dlc_table_csv(): convenience to read a dlc_table_*.csv from DATA_DIR.

This file is intentionally light-weight and optional. Notebooks and scripts
should import `get_conn` and `get_data_dir` rather than hard-coding host
or credentials.
"""
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Optional

try:
    from dotenv import load_dotenv
    _HAS_DOTENV = True
except Exception:
    _HAS_DOTENV = False

import psycopg2
from psycopg2 import OperationalError
import pandas as pd
from pandas import DataFrame
from typing import Any


def load_env(project_root: Optional[Path] = None) -> None:
    """Load .env from project root if python-dotenv is installed.

    Non-fatal if python-dotenv isn't available.
    """
    if not _HAS_DOTENV:
        return
    if project_root is None:
        project_root = Path(__file__).resolve().parents[1]
    env_path = project_root / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=str(env_path))


def get_database_url() -> Optional[str]:
    """Return a DATABASE_URL if present, else compose from parts.

    Returns None if required components are missing.
    """
    # Prefer an explicit DATABASE_URL
    url = os.environ.get('DATABASE_URL')
    if url:
        return url

    # Compose from DB_* env vars if present. Password may be omitted for local
    # socket authentication; still return a usable connection string.
    name = os.environ.get('DB_NAME')
    user = os.environ.get('DB_USER')
    password = os.environ.get('DB_PASSWORD')
    host = os.environ.get('DB_HOST')
    port = os.environ.get('DB_PORT', '5432')
    if name and user and host:
        if password is None or password == '':
            # omit password portion if not provided
            return f"postgres://{user}@{host}:{port}/{name}"
        return f"postgres://{user}:{password}@{host}:{port}/{name}"
    return None


def get_conn(retries: int = 3, backoff: float = 1.0):
    """Attempt to create and return a psycopg2 connection.

    If DATABASE_URL or DB_* env vars are not set, raises RuntimeError.
    Retries with exponential backoff on OperationalError.
    """
    load_env()
    db_url = get_database_url()
    if db_url is None:
        raise RuntimeError("No database configuration found in env (DATABASE_URL or DB_* vars)")

    for attempt in range(1, retries + 1):
        try:
            # psycopg2.connect accepts a connection string or keyword args
            conn = psycopg2.connect(db_url)
            return conn
        except OperationalError as exc:
            if attempt == retries:
                raise
            time.sleep(backoff * attempt)


def get_data_dir() -> Path:
    """Return a Path for DATA_DIR; default to project/data if unset."""
    project_root = Path(__file__).resolve().parents[1]
    data_dir = os.environ.get('DATA_DIR')
    if data_dir:
        return Path(data_dir).expanduser().resolve()
    candidate = project_root / 'data'
    return candidate


def read_dlc_table_csv(name_suffix: str = 'saline'):
    """Return path to dlc_table_{name_suffix}.csv if present in DATA_DIR.

    Example: read_dlc_table_csv('saline') -> /.../dlc_table_saline.csv
    """
    data_dir = get_data_dir()
    filename = f"dlc_table_{name_suffix}.csv"
    path = data_dir / filename
    if path.exists():
        return path
    raise FileNotFoundError(f"Expected CSV not found: {path}")


# --- Compatibility helper: safe replacement for pandas.read_sql_query ---
def read_sql_query_safe(sql: str, con: Any, params=None, **kwargs) -> DataFrame:
    """A lightweight wrapper that accepts DBAPI connection objects (psycopg2, sqlite3)
    and returns a pandas DataFrame. If `con` is a string or SQLAlchemy engine/URL,
    delegate to pandas.read_sql_query.

    This avoids the pandas warning about DBAPI connections not being SQLAlchemy
    connectables when existing code calls pd.read_sql_query(query, conn).
    """
    # If con looks like a SQLAlchemy engine/URL/string, just call pandas
    if isinstance(con, (str,)):
        return pd.read_sql_query(sql, con, params=params, **kwargs)

    # If it's an object exposing execute()/cursor(), use a DB cursor
    cur = None
    try:
        # prefer using a cursor() if available
        if hasattr(con, 'cursor'):
            cur = con.cursor()
            # Try psycopg2-style param substitution first
            try:
                cur.execute(sql, params or ())
            except Exception:
                # Fallback to sqlite-style '?' parameter markers
                try:
                    cur.execute(sql.replace('%s', '?'), params or ())
                except Exception:
                    # As final fallback, try executing without params
                    cur.execute(sql)

            rows = cur.fetchall()
            cols = [d[0] for d in cur.description] if cur.description else []
            return DataFrame(rows, columns=cols)
        else:
            # Unknown connection object: delegate to pandas and let it warn if needed
            return pd.read_sql_query(sql, con, params=params, **kwargs)
    finally:
        if cur is not None:
            try:
                cur.close()
            except Exception:
                pass


# Monkeypatch pandas.read_sql_query at import time so existing notebooks that
# call pd.read_sql_query(query, conn) will use the safe wrapper when `conn` is a
# DBAPI connection. This avoids editing many notebooks.
try:
    if getattr(pd, 'read_sql_query', None) is not read_sql_query_safe:
        pd_read_sql_orig = pd.read_sql_query
        pd.read_sql_query = read_sql_query_safe
except Exception:
    # Don't fail if pandas internals change; fall back to original behavior
    pass
