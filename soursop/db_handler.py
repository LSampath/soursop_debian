import os
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path("/var/lib/soursop/soursop.db").expanduser()


def create_db_file():
    if not DB_PATH.parent.exists():
        if os.geteuid() == 0:
            DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        else:
            print(f"Error: Required directory {DB_PATH.parent} does not exist. "
                  f"Does your daemon have enough permissions?",
                  file=sys.stderr)
            sys.exit(1)


def get_connection():
    if not DB_PATH.parent.exists():
        print(f"Error: Database file {DB_PATH} does not exist. "
              f"Has the daemon initialized the system?",
              file=sys.stderr)
        sys.exit(1)

    return sqlite3.connect(DB_PATH)


def init_db():
    create_db_file()
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS daily_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_str TEXT NOT NULL UNIQUE,
            bytes_received INTEGER NOT NULL,
            bytes_sent INTEGER NOT NULL
        )
        """)
        conn.commit()


def get_usage_by_date(date_str):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT bytes_received, bytes_sent FROM daily_usage WHERE date_str = ?", (date_str,))
        result = cur.fetchone()
        if result is None:
            return 0, 0
        else:
            return result


def get_usage_by_date_range(start_date_str, end_date_str):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT date_str, bytes_received, bytes_sent
            FROM daily_usage
            WHERE date_str BETWEEN ? AND ?
            ORDER BY date_str
        """, (start_date_str, end_date_str))
        return cur.fetchall()


def update_or_insert_usage(date_str, bytes_received, bytes_sent):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO daily_usage (date_str, bytes_received, bytes_sent)
            VALUES (?, ?, ?)
            ON CONFLICT(date_str) DO UPDATE SET
                bytes_received=excluded.bytes_received,
                bytes_sent=excluded.bytes_sent
        """, (date_str, bytes_received, bytes_sent))
        conn.commit()
