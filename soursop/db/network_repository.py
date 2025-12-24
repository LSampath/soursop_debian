import sqlite3
from datetime import date
from typing import Optional

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


def update(entries: list[NetworkUsage]) -> None:
    params = [(e.date_str, e.hour, e.network, e.incoming_bytes, e.outgoing_bytes) for e in entries]
    query = """
        INSERT INTO network_usage 
        (date_str, hour, network, incoming_bytes, outgoing_bytes)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(date_str, hour, network) DO UPDATE SET
            incoming_bytes=excluded.incoming_bytes,
            outgoing_bytes=excluded.outgoing_bytes
    """
    if not params:
        return
    with get_connection() as conn:
        cur = conn.cursor()
        cur.executemany(query, params)
        conn.commit()


def search(from_date: date, to_date: date, network: Optional[str]) -> list[NetworkUsage]:
    start = from_date.isoformat()
    end = to_date.isoformat()
    params = [start, end]
    sql = """
        SELECT date_str, hour, network, incoming_bytes, outgoing_bytes
        FROM network_usage WHERE date_str BETWEEN ? AND ?
    """
    if network:
        sql += " AND network LIKE ?"
        params.append(f"%{network}%")
    sql += " ORDER BY date_str, hour, network"

    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(sql, params)
        rows = cur.fetchall()

    result = []
    for r in rows:
        result.append(NetworkUsage(
            date_str=r["date_str"], hour=int(r["hour"]), network=r["network"],
            incoming_bytes=int(r["incoming_bytes"]) if r["incoming_bytes"] is not None else 0,
            outgoing_bytes=int(r["outgoing_bytes"]) if r["outgoing_bytes"] is not None else 0
        ))
    return result
