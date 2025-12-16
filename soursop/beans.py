from dataclasses import dataclass
from enum import Enum
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


@dataclass
class NetworkUsage:
    id: Optional[int] = 0,
    network: Optional[str] = None
    date_str: Optional[str] = None,
    hour: Optional[int] = 0
    incoming_bytes: Optional[int] = 0,
    outgoing_bytes: Optional[int] = 0


class Level(Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    HOUR = "hour"
