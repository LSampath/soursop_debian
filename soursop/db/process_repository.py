import sqlite3
from datetime import date
from typing import Optional

from soursop.beans import ProcessUsage
from soursop.db.connection import get_connection


def get_by_pid_name(pid: int, name: str) -> list[ProcessUsage]:
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


def search(from_date: date, to_date: date, name: Optional[str]) -> list[ProcessUsage]:
    start = from_date.isoformat()
    end = to_date.isoformat()
    params = [start, end]
    sql = """
        SELECT pid, date_str, hour, name, path, incoming_bytes, outgoing_bytes
        FROM process_usage WHERE date_str BETWEEN ? AND ?
    """
    if name:
        sql += " AND name LIKE ?"
        params.append(f"%{name}%")
    sql += " ORDER BY date_str, hour, pid"      # what is the most optimal order here??

    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(sql, params)
        rows = cur.fetchall()

    result = []
    for r in rows:
        result.append(ProcessUsage(
            pid=int(r["pid"]), name=r["name"],
            path=r["path"] if r["path"] is not None else "",
            date_str=r["date_str"], hour=int(r["hour"]), id=0, network=None,
            incoming_bytes=int(r["incoming_bytes"]) if r["incoming_bytes"] is not None else 0,
            outgoing_bytes=int(r["outgoing_bytes"]) if r["outgoing_bytes"] is not None else 0,
            packet_count=0,
        ))
    return result


def update(entries: list[ProcessUsage]) -> None:
    insert_update_query = """
        INSERT INTO process_usage
        (date_str, hour, pid, name, path, network, incoming_bytes, outgoing_bytes, packet_count)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (date_str, hour, pid, name)
        DO UPDATE SET
            incoming_bytes = excluded.incoming_bytes,
            outgoing_bytes = excluded.outgoing_bytes,
            packet_count = excluded.packet_count
    """
    params = []
    for e in entries:
        params.append((
            e.date_str, e.hour, e.pid, e.name, e.path,
            e.network if e.network is not None else "",
            int(e.incoming_bytes or 0), int(e.outgoing_bytes or 0), int(e.packet_count or 0),
        ))
    if not params:
        return

    with get_connection() as conn:
        cur = conn.cursor()
        cur.executemany(insert_update_query, params)
        conn.commit()
