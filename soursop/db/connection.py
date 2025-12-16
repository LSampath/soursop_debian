import logging
import os
import sqlite3
import sys
from pathlib import Path

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
                date_str TEXT NOT NULL,
                hour INTEGER NOT NULL,
                network TEXT NOT NULL,
                incoming_bytes INTEGER NOT NULL,
                outgoing_bytes INTEGER NOT NULL,
                UNIQUE (date_str, hour, network))
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
                UNIQUE (date_str, hour, pid, name))
        """)
        # include indexes as well, if needed
        conn.commit()
        logging.info("SQLite database initialization successful.")
