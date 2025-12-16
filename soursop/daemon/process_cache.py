import logging
import time

import psutil

from soursop.beans import ProcessInfo
from soursop.util import TEN_SECONDS

# map of pid and their corresponding process information
_PROCESS_CACHE: dict[int, ProcessInfo] = {}


def get_process_info(pid: int) -> ProcessInfo | None:
    now = time.time()
    if pid in _PROCESS_CACHE:
        info = _PROCESS_CACHE[pid]
        if now - info.timestamp < TEN_SECONDS:
            return info

    try:
        p = psutil.Process(pid)
        with p.oneshot():
            name = p.name()
            path = p.exe()
        new_info = ProcessInfo(pid=pid, name=name, path=path, timestamp=now)
        _PROCESS_CACHE[pid] = new_info
        return new_info
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None
