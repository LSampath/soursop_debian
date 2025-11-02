import logging
import os
from collections import defaultdict
from datetime import datetime
from threading import Thread
from time import sleep

import psutil
from scapy.interfaces import ifaces
from scapy.layers.inet import IP
from scapy.sendrecv import sniff

# MAC addresses of every network adapter
ALL_MACS = {iface.mac for iface in ifaces.values()}

# dictionary to map each connection to its corresponding process ID (PID)
CONNECTION_PID_MAP = {}

# dictionary to map each process ID (PID) to total Upload (0) and Download (1) traffic
PID_TRAFFIC_MAP = defaultdict(lambda: [0, 0])

# dataframe to track previous traffic usages
PREVIOUS_USAGES = None


def process_packet(packet):
    """
    find destination and source ports of each packet to determine which connection this packet belongs
    and update the CONNECTION_PID_MAP
    """
    global PID_TRAFFIC_MAP
    try:
        ip_packet = packet[IP]
        packet_connection = (ip_packet.sport, ip_packet.dport)
    except (AttributeError, IndexError):
        pass
    else:
        packet_pid = CONNECTION_PID_MAP.get(packet_connection)
        if packet_pid:
            if ip_packet.src in ALL_MACS:
                PID_TRAFFIC_MAP[packet_pid][0] += len(ip_packet)  # outgoing/upload
            else:
                PID_TRAFFIC_MAP[packet_pid][1] += len(ip_packet)  # incoming/download


def get_connections():
    """
    Keeps listening for connections on this machine, and add them to global CONNECTION_PID_MAP
    (local_address.port, remove_address.port) -> pid
    """
    print("Start connection updating thread....")

    global CONNECTION_PID_MAP
    # while config.RUNNING_FLAG:
    while True:
        for c in psutil.net_connections():
            if c.laddr and c.raddr and c.pid:
                CONNECTION_PID_MAP[(c.laddr.port, c.raddr.port)] = c.pid
                CONNECTION_PID_MAP[(c.raddr.port, c.laddr.port)] = c.pid
        sleep(1)

    print("stopped connection updating thread...")


def sniff_packets():
    print("started sniffing thread.....")
    logging.info("started sniffing thread")
    # sniff(prn=process_packet, store=False, filter="ip", stop_filter=lambda _: not config.RUNNING_FLAG)
    sniff(prn=process_packet, store=False, filter="ip", stop_filter=lambda _: not True)
    print("Stopped sniffing thread...")
    logging.info("Stopped sniffing thread")


def calculate_and_save_usage():
    global PREVIOUS_USAGES
    process_info_map = {}
    for pid, (up_traffic, down_traffic) in PID_TRAFFIC_MAP.items():
        try:
            process = psutil.Process(pid)
        except psutil.NoSuchProcess:
            continue
        name = process.name()
        create_time = get_process_create_time(process)
        process_info = {
            "pid": pid, "name": name, "create_time": create_time,
            "Upload": up_traffic, "Download": down_traffic,
        }
        try:
            process_info["Upload Speed"] = up_traffic - PREVIOUS_USAGES[pid]["Upload"]
            process_info["Download Speed"] = down_traffic - PREVIOUS_USAGES[pid]["Download"]
        except (KeyError, AttributeError):
            process_info["Upload Speed"] = up_traffic
            process_info["Download Speed"] = down_traffic
        process_info_map[pid] = process_info

    print_stats(process_info_map)

    PREVIOUS_USAGES = process_info_map


def print_stats(process_info_map):
    for pid, process_info in process_info_map.items():
        print(process_info)
    os.system("clear")


def get_process_create_time(process):
    try:
        create_time = datetime.fromtimestamp(process.create_time())
    except OSError:
        create_time = datetime.fromtimestamp(psutil.boot_time())
    return create_time


def save_usages():
    print("Started usage saving thread....")
    # while config.RUNNING_FLAG:
    while True:
        calculate_and_save_usage()
        sleep(1)
    print("Stopped usage saving thread.....")


def start_packet_sniffing():
    sniff_thread = Thread(target=sniff_packets, daemon=False)
    sniff_thread.start()

    connections_thread = Thread(target=get_connections, daemon=True)
    connections_thread.start()

    save_usage_thread = Thread(target=save_usages, daemon=True)
    save_usage_thread.start()


# remove later
if __name__ == "__main__":
    print("Starting soursop daemon service.....")
    start_packet_sniffing()
