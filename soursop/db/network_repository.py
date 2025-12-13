import sqlite3
from datetime import date

from soursop import util
from soursop.beans import NetworkUsage
from soursop.db.connection import get_connection


def get_usage_bytes(date_obj: date, hour: int, network: str) -> tuple[int, int]:
    date_str = date_obj.strftime(util.DB_DATE_FORMAT)
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("""
            SELECT incoming_bytes, outgoing_bytes FROM network_usage 
            WHERE date_str = ? AND hour = ? AND network = ?
        """, (date_str, hour, network))
        result = cur.fetchone()
        if result is None:
            return 0, 0
        else:
            incoming = int(result["incoming_bytes"])
            outgoing = int(result["outgoing_bytes"])
            return incoming, outgoing


def update(entry: NetworkUsage):
    params = (entry.date_str, entry.hour, entry.network, entry.incoming_bytes, entry.outgoing_bytes)
    query = """
        INSERT INTO network_usage 
        (date_str, hour, network, incoming_bytes, outgoing_bytes)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(date_str, hour, network) DO 
        UPDATE SET
            incoming_bytes=excluded.incoming_bytes,
            outgoing_bytes=excluded.outgoing_bytes
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        conn.commit()
