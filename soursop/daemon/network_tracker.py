import logging
import os
from datetime import date, datetime
from threading import Thread
from time import sleep

import psutil

import soursop.db.network_repository as repository
from soursop import util
from soursop.beans import NetworkUsage


def get_time_now() -> tuple[date, int]:
    date_now = datetime.now().replace(minute=0, second=0, microsecond=0)
    return date_now, date_now.hour


def get_counters(interface):
    stats = psutil.net_io_counters(pernic=True)
    if interface not in stats:
        raise RuntimeError(f"Interface '{interface}' not found! Available: {list(stats.keys())}")
    iface = stats[interface]
    return iface.bytes_recv, iface.bytes_sent


def get_wifi_interface():
    net_path = "/sys/class/net/"
    for interface in os.listdir(net_path):
        if os.path.isdir(os.path.join(net_path, interface, "wireless")):
            return interface
    raise RuntimeError("No Wi-Fi interface found!")


def listen_and_save_usage():
    wif_name = get_wifi_interface()
    start_date, start_hour = get_time_now()
    baseline_recv, baseline_sent = get_counters(wif_name)
    starting_incoming, starting_outgoing = repository.get_usage_bytes(start_date, start_hour, wif_name)

    while util.RUNNING_FLAG:
        sleep(util.FIFTEEN_SECONDS)
        new_usage = create_new_usage_entry(wif_name)
        bytes_recv, bytes_sent = get_counters(wif_name)

        if start_hour != new_usage.hour:
            starting_incoming, starting_outgoing = 0, 0
            baseline_recv, baseline_sent = bytes_recv, bytes_sent
            start_hour = new_usage.hour
            logging.info(f"New date: {new_usage.date_str}, hour: {start_hour}, "
                         f"resetting baseline counters to {baseline_recv}/{baseline_sent} bytes.")

        new_usage.incoming_bytes = starting_incoming + bytes_recv - baseline_recv
        new_usage.outgoing_bytes = starting_outgoing + bytes_sent - baseline_sent
        logging.info(f"Saving network usage: {new_usage}")
        repository.update(new_usage)


def create_new_usage_entry(wif_name):
    now_date, now_hour = get_time_now()
    now_date_str = now_date.strftime(util.DB_DATE_FORMAT)
    return NetworkUsage(network=wif_name, date_str=now_date_str, hour=now_hour)


def sniff_network():
    logging.info("Started network sniffing thread....")
    while util.RUNNING_FLAG:
        try:
            listen_and_save_usage()
        except Exception as e:
            logging.error(f"Error occurred while handling save_process_usages", e)
            sleep(util.FIVE_SECONDS)
    logging.info("Stopped network sniffing thread....")


def start_network_tracking():
    sniff_thread = Thread(target=sniff_network, daemon=False)
    sniff_thread.start()
