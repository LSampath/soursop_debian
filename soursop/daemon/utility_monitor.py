import logging
import socket
from threading import Thread, Lock
from time import sleep

import psutil

from soursop import util

# list of ipv4 and ipv6 addresses of Wi-Fi adapter
_WIFI_IPS: set[str] = set()
_WIFI_IPS_LOCK = Lock()

# dictionary to map each connection to its corresponding process ID (PID)
_CONNECTION_PID_MAP: dict[tuple[int, int], int] = {}
_CONNECTION_LOCK = Lock()


def get_wifi_ips() -> set[str]:
    with _WIFI_IPS_LOCK:
        return _WIFI_IPS.copy()


def get_connection_pid(connection: tuple[int, int]) -> int:
    with _CONNECTION_LOCK:
        return _CONNECTION_PID_MAP.get(connection)


def derive_wifi_ips() -> set[str]:
    ip_set = set()
    try:
        for name, addrs in psutil.net_if_addrs().items():
            if "wl" in name or "wifi" in name.lower():
                for addr in addrs:
                    if addr.family == socket.AF_INET:
                        ip_set.add(addr.address)
                    elif addr.family == socket.AF_INET6:
                        ipv6 = addr.address.split('%')[0]
                        if not ipv6.startswith("fe80"):
                            ip_set.add(ipv6)
    except Exception as e:
        logging.exception(f"get_wifi_address() failed: {e}")
    return ip_set


def update_wifi_address() -> None:
    global _WIFI_IPS
    logging.info("Started wifi IP address updating thread...")
    last_ips = set()
    while util.RUNNING_FLAG:
        new_wifi_ips = derive_wifi_ips()
        if new_wifi_ips and new_wifi_ips != last_ips:
            with _WIFI_IPS_LOCK:
                _WIFI_IPS = new_wifi_ips
                last_ips = new_wifi_ips
            logging.info(f"Wifi address updated: {new_wifi_ips}")
        sleep(util.ONE_MINUTE)


def update_connections() -> None:  # is port-port connection is enough ??????
    """
    Keeps listening for connections IP on this machine, and add them to global CONNECTION_PID_MAP
    (local_address.port, remove_address.port) -> pid
    """
    logging.info("Started connections updating thread...")
    global _CONNECTION_PID_MAP
    while util.RUNNING_FLAG:
        for c in psutil.net_connections(kind='inet'):
            if c.laddr and c.raddr and c.pid:
                with _CONNECTION_LOCK:
                    _CONNECTION_PID_MAP[(c.laddr.port, c.raddr.port)] = c.pid
                    _CONNECTION_PID_MAP[(c.raddr.port, c.laddr.port)] = c.pid
        sleep(util.FIFTEEN_SECONDS)


def start_utility_monitor() -> None:
    wifi_address_thread = Thread(target=update_wifi_address, daemon=True)
    wifi_address_thread.start()

    connection_thread = Thread(target=update_connections, daemon=True)
    connection_thread.start()
