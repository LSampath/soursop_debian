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
        cur.execute("CREATE TABLE IF NOT EXISTS counter (val INTEGER);")
        conn.commit()


def get_counter():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT val FROM counter")
        row = cur.fetchone()
        return row[0] if row else 0


def set_counter(val):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM counter")
        cur.execute("INSERT INTO counter (val) VALUES (?)", (val,))
        conn.commit()
