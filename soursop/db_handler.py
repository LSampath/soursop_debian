import sqlite3
from pathlib import Path

DB_PATH = "/var/lib/soursop/data.db"
Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    return conn


def init_db():
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


def get_usage(date_str):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT bytes_received, bytes_sent FROM daily_usage WHERE date_str = ?", (date_str,))
        result = cur.fetchone()
        print("result:")
        print(result)
        return result


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
