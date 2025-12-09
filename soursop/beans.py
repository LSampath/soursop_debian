from dataclasses import dataclass
from typing import Optional


@dataclass
class ProcessUsage:
    pid: int
    name: str
    path: str
    date_str: str
    hour: int
    id: Optional[int] = 0
    network: Optional[str] = None
    incoming_bytes: Optional[int] = 0
    outgoing_bytes: Optional[int] = 0
    packet_count: Optional[int] = 0


@dataclass
class ProcessInfo:
    pid: int
    name: str
    path: str
    timestamp: float
