'''\
net_usage_tracker.py

A simple Linux network-usage tracker that:
- Polls your Wi-Fi interface counters once per minute
- Detects day boundaries (midnight) and computes total bytes in/out for the past day
- Saves the daily totals to an SQLite database (net_usage.db)
- Resets the baseline counters at the start of each new day

Usage:
  python3 net_usage_tracker.py &

You can also daemonize via systemd (see service example below).
'''
import datetime
import signal
import sqlite3
import time

import psutil

# CONFIGURATION
INTERFACE = 'wlan0'  # change to your Wi-Fi adapter name
DB_PATH = 'net_usage.db'
POLL_INTERVAL = 60  # seconds

running = True


def signal_handler(sig, frame):
    global running
    running = False
    print("Shutting down gracefully...")


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def init_db(conn):
    conn.execute(
        '''
        CREATE TABLE IF NOT EXISTS daily_usage (
            day TEXT PRIMARY KEY,
            rx_bytes INTEGER,
            tx_bytes INTEGER
        )
        '''
    )
    conn.commit()


def get_counters():
    stats = psutil.net_io_counters(pernic=True)
    if INTERFACE not in stats:
        raise RuntimeError(f"Interface '{INTERFACE}' not found! Available: {list(stats.keys())}")
    iface = stats[INTERFACE]
    return iface.bytes_recv, iface.bytes_sent


def main():
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    # Initial baseline at startup
    baseline_rx, baseline_tx = get_counters()
    current_day = datetime.date.today()

    print(f"Starting tracker on interface {INTERFACE}, baseline set at {baseline_rx}/{baseline_tx} bytes.")

    while running:
        time.sleep(POLL_INTERVAL)
        now = datetime.datetime.now()
        today = now.date()

        # On day change (past midnight)
        if today != current_day:
            # read counters at boundary
            rx, tx = get_counters()
            delta_rx = rx - baseline_rx
            delta_tx = tx - baseline_tx

            # store yesterday's totals
            day_str = current_day.isoformat()
            conn.execute(
                'INSERT OR REPLACE INTO daily_usage(day, rx_bytes, tx_bytes) VALUES (?, ?, ?)',
                (day_str, delta_rx, delta_tx)
            )
            conn.commit()
            print(f"[{day_str}] RX={delta_rx} bytes, TX={delta_tx} bytes saved.")

            # reset baseline for new day
            baseline_rx, baseline_tx = rx, tx
            current_day = today
            print(f"New baseline for {current_day} set at {baseline_rx}/{baseline_tx} bytes.")

    # On shutdown, optionally flush current day's data (not resetting)
    rx, tx = get_counters()
    delta_rx = rx - baseline_rx
    delta_tx = tx - baseline_tx
    day_str = current_day.isoformat()
    conn.execute(
        'INSERT OR REPLACE INTO daily_usage(day, rx_bytes, tx_bytes) VALUES (?, ?, ?)',
        (day_str, delta_rx, delta_tx)
    )
    conn.commit()
    print(f"Shutdown flush: [{day_str}] RX={delta_rx} bytes, TX={delta_tx} bytes saved.")
    conn.close()


if __name__ == '__main__':
    main()

# -------------------------
# Example systemd service (save as net_usage_tracker.service):
#
# [Unit]
# Description=Daily Network Usage Tracker
# After=network.target
#
# [Service]
# ExecStart=/usr/bin/python3 /path/to/net_usage_tracker.py
# Restart=always
#
# [Install]
# WantedBy=multi-user.target
#
# To enable:
# sudo cp net_usage_tracker.service /etc/systemd/system/
# sudo systemctl daemon-reload
# sudo systemctl enable --now net_usage_tracker.service
