from collections import deque
from threading import Lock
from typing import Any, List


class BatchDeque:
    def __init__(self) -> None:
        self._dq = deque()
        self._lock = Lock()

    def put(self, item: Any) -> None:
        """Append an item to the right end (atomic)."""
        with self._lock:
            self._dq.append(item)

    def drain(self) -> List[Any]:
        """Atomically remove and return all items currently present."""
        with self._lock:
            if not self._dq:
                return []
            items = list(self._dq)
            self._dq.clear()
            return items
