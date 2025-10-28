"""
Database utility functions for the Feature_functions package.

Common database operations used across multiple feature modules.
"""

import numpy as np
from typing import Optional, Tuple


def get_trial_meta(conn, trial_id: int, table: str = "dlc_table") -> Tuple[Optional[float], Optional[float]]:
    """
    Returns (trial_length_seconds, frame_rate_fps) from the DB (or (None, None) if missing).
    Uses psycopg2 '%s' style with sqlite fallback to '?'.
    
    Args:
        conn: Database connection
        trial_id: Trial identifier
        table: Database table name
        
    Returns:
        Tuple of (trial_length_s, frame_rate_fps)
    """
    # Use a DB cursor rather than pandas.read_sql_query to avoid pandas' SQLAlchemy
    # warning when given a DBAPI connection (psycopg2, sqlite3, etc.). This also
    # keeps the function dependency-light and works for both drivers.
    q_psycopg = f"SELECT trial_length, frame_rate FROM {table} WHERE id = %s;"
    q_sqlite = f"SELECT trial_length, frame_rate FROM {table} WHERE id = ?;"

    cur = None
    try:
        cur = conn.cursor()
        # Try psycopg2 style first
        try:
            cur.execute(q_psycopg, (trial_id,))
        except Exception:
            # Fallback to sqlite-style parameter marker
            cur.execute(q_sqlite, (trial_id,))

        rows = cur.fetchall()
        if not rows:
            return None, None

        # Build a dict from the first row using cursor.description
        cols = [d[0] for d in cur.description] if cur.description else []
        row = rows[0]
        rowd = dict(zip(cols, row))

        length = float(rowd.get("trial_length")) if rowd.get("trial_length") is not None else None
        fps = float(rowd.get("frame_rate")) if rowd.get("frame_rate") is not None else None
        return length, fps
    finally:
        if cur is not None:
            try:
                cur.close()
            except Exception:
                pass


def get_csv_path(conn, trial_id: int, table: str = "dlc_table") -> str:
    """
    Read CSV file path from database for a given trial ID.
    
    Args:
        conn: Database connection
        trial_id: Trial identifier
        table: Database table name
        
    Returns:
        CSV file path as string
        
    Raises:
        ValueError: If CSV path not found for the trial ID
    """
    cur = None
    try:
        cur = conn.cursor()
        # Try psycopg2 style first
        try:
            cur.execute(f"SELECT csv_file_path FROM {table} WHERE id = %s", (trial_id,))
        except Exception:
            # Fallback to sqlite-style parameter marker
            cur.execute(f"SELECT csv_file_path FROM {table} WHERE id = ?", (trial_id,))
        
        rows = cur.fetchall()
        if not rows or rows[0][0] is None:
            raise ValueError(f"csv_file_path not found for id={trial_id} in '{table}'")
        
        return str(rows[0][0])
    finally:
        if cur is not None:
            try:
                cur.close()
            except Exception:
                pass