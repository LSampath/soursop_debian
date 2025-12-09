import logging
import os
import sqlite3
import sys
from pathlib import Path

from soursop.beans import ProcessUsage

DB_PATH = Path("/var/lib/soursop/soursop.db").expanduser()


def create_db_file():
    if not DB_PATH.parent.exists():
        if os.geteuid() == 0:
            DB_PATH.parent.mkdir(parents=True, exist_ok=True)
            logging.info(f"SQLite database file created in {DB_PATH}.")
        else:
            logging.error(f"Error: Required directory {DB_PATH.parent} does not exist. "
                          f"Does your daemon have enough permissions?")
            sys.exit(1)


def get_connection():
    if not DB_PATH.parent.exists():
        logging.error(f"Error: Database file {DB_PATH} does not exist. "
                      f"Has the daemon initialized the system?")
        sys.exit(1)

    return sqlite3.connect(DB_PATH)


def init_db():
    create_db_file()
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS network_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_str TEXT NOT NULL UNIQUE,
            bytes_received INTEGER NOT NULL,
            bytes_sent INTEGER NOT NULL);
        """)
        cur.execute("""
                CREATE TABLE IF NOT EXISTS process_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date_str TEXT NOT NULL,
                    hour INTEGER NOT NULL,
                    pid INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    path TEXT NULL,
                    network TEXT NOT NULL,
                    incoming_bytes INTEGER NOT NULL,
                    outgoing_bytes INTEGER NOT NULL,
                    packet_count INTEGER NOT NULL,
                    UNIQUE (date_str, hour, pid)
                );
                """)
        # include indexes as well, if needed
        conn.commit()
        logging.info("SQLite database initialization successful.")


def get_network_usage_by_date(date_str):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT bytes_received, bytes_sent FROM network_usage WHERE date_str = ?", (date_str,))
        result = cur.fetchone()
        if result is None:
            return 0, 0
        else:
            return result


def get_network_usage_by_date_range(start_date_str, end_date_str):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT date_str, bytes_received, bytes_sent
            FROM network_usage
            WHERE date_str BETWEEN ? AND ?
            ORDER BY date_str
        """, (start_date_str, end_date_str))
        return cur.fetchall()


def update_network_usage(date_str, bytes_received, bytes_sent):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO network_usage (date_str, bytes_received, bytes_sent)
            VALUES (?, ?, ?)
            ON CONFLICT(date_str) DO 
            UPDATE SET
                bytes_received=excluded.bytes_received,
                bytes_sent=excluded.bytes_sent
        """, (date_str, bytes_received, bytes_sent))
        conn.commit()


def get_process_usage_by_pid_name(pid: int, name: str) -> list[ProcessUsage]:
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM process_usage WHERE pid = ? AND name = ?", (pid, name))
        rows = cur.fetchall()

        entries = []
        for r in rows:
            entries.append(ProcessUsage(
                pid=r["pid"], name=r["name"], path=r["path"], date_str=r["date_str"], hour=r["hour"], id=r["id"],
                network=r["network"], incoming_bytes=r["incoming_bytes"], outgoing_bytes=r["outgoing_bytes"],
                packet_count=r["packet_count"]
            ))
        return entries
