import datetime
import logging
import os
import signal
import time
from pathlib import Path

import psutil

from soursop import util
from soursop.db.connection import init_db, update_network_usage, get_network_usage_by_date
from soursop.daemon.packet_sniffer import start_packet_sniffing
from soursop.daemon.utility_monitor import start_utility_monitor


def configure_logging():
    handlers = [logging.StreamHandler()]
    log_file = Path("/var/log/soursop/soursop.log")
    log_file.parent.mkdir(parents=True, exist_ok=True)
    handlers.append(logging.FileHandler(log_file))

    logging.root.handlers.clear()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=handlers,
    )
    logging.info("Logging configuration successful.")


def get_wifi_interface():
    net_path = "/sys/class/net/"
    for interface in os.listdir(net_path):
        if os.path.isdir(os.path.join(net_path, interface, "wireless")):
            return interface
    raise RuntimeError("No Wi-Fi interface found!")


def get_counters(interface):
    stats = psutil.net_io_counters(pernic=True)
    if interface not in stats:
        raise RuntimeError(f"Interface '{interface}' not found! Available: {list(stats.keys())}")
    iface = stats[interface]
    return iface.bytes_recv, iface.bytes_sent


def main():
    logging.info("Starting Soursop 1.0 daemon...")

    wifi_interface = get_wifi_interface()
    start_date = datetime.date.today()
    start_date_str = start_date.isoformat()
    baseline_recv, baseline_sent = get_counters(wifi_interface)
    today_recv, today_sent = get_network_usage_by_date(start_date_str)

    while util.RUNNING_FLAG:
        time.sleep(util.FIFTEEN_SECONDS)
        today_date = datetime.datetime.now().date()
        today_str = today_date.isoformat()

        bytes_recv, bytes_sent = get_counters(wifi_interface)
        delta_recv = today_recv + bytes_recv - baseline_recv
        delta_sent = today_sent + bytes_sent - baseline_sent
        update_network_usage(today_str, delta_recv, delta_sent)

        # On day change (past midnight)
        if today_date != start_date:
            today_recv, today_sent = 0, 0
            baseline_recv, baseline_sent = bytes_recv, bytes_sent
            start_date = today_date
            logging.info(f"New day: {today_str}, resetting baseline counters to {baseline_recv}/{baseline_sent} bytes.")

    # shutdown gracefully
    today_date = datetime.datetime.now().date()
    today_str = today_date.isoformat()

    bytes_recv, bytes_sent = get_counters(wifi_interface)
    delta_recv = today_recv + bytes_recv - baseline_recv
    delta_sent = today_sent + bytes_sent - baseline_sent
    update_network_usage(today_str, delta_recv, delta_sent)


def shutdown_handler(sig, frame):
    util.RUNNING_FLAG = False
    logging.info("Shutting down gracefully...")


if __name__ == "__main__":
    configure_logging()
    init_db()
    start_utility_monitor()

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    start_packet_sniffing()
    main()


# need to write a cleaner scheduler for both calculators