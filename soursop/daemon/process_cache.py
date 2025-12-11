import logging
import time

import psutil

from soursop.beans import ProcessInfo
from soursop.util import CACHE_TTL

# map of pid and their corresponding process information
_PROCESS_CACHE: dict[int, ProcessInfo] = {}


def get_process_info(pid: int) -> ProcessInfo | None:
    now = time.time()
    if pid in _PROCESS_CACHE:
        info = _PROCESS_CACHE[pid]
        if now - info.timestamp < CACHE_TTL:
            return info

    try:
        p = psutil.Process(pid)
        with p.oneshot():
            name = p.name()
            path = p.exe()
        new_info = ProcessInfo(pid=pid, name=name, path=path, timestamp=now)
        _PROCESS_CACHE[pid] = new_info
        logging.info(f"Updated process info entry {new_info}")
        return new_info
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None
