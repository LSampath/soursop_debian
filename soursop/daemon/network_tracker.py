import logging
import os
from datetime import date, datetime
from threading import Thread
from time import sleep

import psutil

import soursop.db.network_repository as repository
from soursop import util
from soursop.beans import NetworkUsage, NetworkInterface


def get_time_now() -> tuple[date, int]:
    date_now = datetime.now().replace(minute=0, second=0, microsecond=0)
    return date_now, date_now.hour


def get_counters(interface: str) -> tuple[int, int]:
    stats = psutil.net_io_counters(pernic=True)
    if interface not in stats:
        raise RuntimeError(f"Interface '{interface}' not found! Available: {list(stats.keys())}")
    iface = stats[interface]
    return iface.bytes_recv, iface.bytes_sent


# move to a separate thread in future
def get_physical_interfaces() -> list[str]:
    net_path = "/sys/class/net/"
    return [
        iface for iface in os.listdir(net_path)
        if os.path.exists(os.path.join(net_path, iface, "device"))
    ]


def create_network_interface_map(start_date: date,
                                 start_hour: int,
                                 interfaces: list[str]) -> dict[str, NetworkInterface]:
    interface_map = {}
    for name in interfaces:
        baseline_incoming, baseline_outgoing = get_counters(name)
        saved_incoming, saved_outgoing = repository.get_usage_bytes(start_date, start_hour, name)
        interface_info = NetworkInterface(name=name,
                                          saved_incoming=saved_incoming, saved_outgoing=saved_outgoing,
                                          baseline_incoming=baseline_incoming, baseline_outgoing=baseline_outgoing)
        interface_map[name] = interface_info
    return interface_map


def listen_and_save_usage():
    interfaces = get_physical_interfaces()
    start_date, start_hour = get_time_now()

    interface_info_map = create_network_interface_map(start_date, start_hour, interfaces)

    while util.RUNNING_FLAG:
        sleep(util.FIFTEEN_SECONDS)
        now_date, now_hour = get_time_now()
        now_date_str = now_date.strftime(util.DB_DATE_FORMAT)

        for name, info in interface_info_map.items():
            info.current_usage = NetworkUsage(network=name, date_str=now_date_str, hour=now_hour)
            bytes_incoming, bytes_outgoing = get_counters(name)

            if start_hour != now_hour:
                info.saved_incoming, info.saved_outgoing = 0, 0
                info.baseline_incoming, info.baseline_incoming = bytes_incoming, bytes_outgoing
                start_hour = now_hour
                logging.info(f"New time period: {now_date_str}:{start_hour}, for network: {name}"
                             f"resetting baseline counters to {bytes_incoming}/{bytes_outgoing} bytes.")

            info.current_usage.incoming_bytes = info.saved_incoming + bytes_incoming - info.baseline_incoming
            info.current_usage.outgoing_bytes = info.saved_outgoing + bytes_outgoing - info.baseline_outgoing

        usages = [iface.current_usage for iface in interface_info_map.values()]
        repository.update(usages)


def sniff_network():
    logging.info("Started network sniffing thread....")
    while util.RUNNING_FLAG:
        try:
            listen_and_save_usage()
        except Exception as e:
            logging.info(f"Error occurred while handling save_process_usages", e)
            sleep(util.FIVE_SECONDS)
    logging.info("Stopped network sniffing thread....")


def start_network_tracking():
    sniff_thread = Thread(target=sniff_network, daemon=False)
    sniff_thread.start()
