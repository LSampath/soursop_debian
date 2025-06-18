import datetime
import logging
import os
import signal
import time
from pathlib import Path

import psutil

from soursop.db_handler import init_db, update_or_insert_usage, get_usage_by_date

INTERVAL = 10
RUNNING_FLAG = True

LOG_FILE = Path("/var/log/soursop/soursop.log")
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler()
        ]
    )


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
    print("Starting Soursop 1.0 daemon...")
    init_db()

    wifi_interface = get_wifi_interface()
    start_date = datetime.date.today()
    start_date_str = start_date.isoformat()
    baseline_recv, baseline_sent = get_counters(wifi_interface)
    today_recv, today_sent = get_usage_by_date(start_date_str)

    while RUNNING_FLAG:
        time.sleep(INTERVAL)
        today_date = datetime.datetime.now().date()
        today_str = today_date.isoformat()

        bytes_recv, bytes_sent = get_counters(wifi_interface)
        delta_recv = today_recv + bytes_recv - baseline_recv
        delta_sent = today_sent + bytes_sent - baseline_sent
        update_or_insert_usage(today_str, delta_recv, delta_sent)

        # On day change (past midnight)
        if today_date != start_date:
            today_recv, today_sent = 0, 0
            baseline_recv, baseline_sent = bytes_recv, bytes_sent
            start_date = today_date
            print(f"New day: {today_str}, resetting baseline counters to {baseline_recv}/{baseline_sent} bytes.")

    # shutdown gracefully
    today_date = datetime.datetime.now().date()
    today_str = today_date.isoformat()

    bytes_recv, bytes_sent = get_counters(wifi_interface)
    delta_recv = today_recv + bytes_recv - baseline_recv
    delta_sent = today_sent + bytes_sent - baseline_sent
    update_or_insert_usage(today_str, delta_recv, delta_sent)


def shutdown_handler(sig, frame):
    global RUNNING_FLAG
    RUNNING_FLAG = False
    print("Shutting down gracefully...")


if __name__ == "__main__":
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    configure_logging()

    main()
