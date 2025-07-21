import os
import threading
import time
from collections import defaultdict
from datetime import datetime

import pandas as pd
import psutil
from scapy.interfaces import ifaces
from scapy.layers.inet import IP
from scapy.sendrecv import sniff

RUNNING = True
DELAY = 1

# https://thepythoncode.com/article/make-a-network-usage-monitor-in-python

"""
upload and download total bytes for each pid, accumulated every second
"""
PROCESS_TRAFFIC_MAP = defaultdict(lambda: [0, 0])

GLOBAL_DF = None  # global DataFrame to store traffic data, if needed ??????

"""
replaced with new current connections map, every second, connections are sensitive to the direction of traffic
used to get the corresponding process ID (PID) for each connection (connection is retrieved from the packet)
"""
CONNECTION_MAP = {}


def get_wifi_interface():
    net_path = "/sys/class/net/"
    for interface in os.listdir(net_path):
        if os.path.isdir(os.path.join(net_path, interface, "wireless")):
            return interface
    raise RuntimeError("No Wi-Fi interface found!")


WIFI_INTERFACE_NAME = get_wifi_interface()


def get_wifi_interface_ip():
    for iface in ifaces.values():
        if iface.name == WIFI_INTERFACE_NAME:
            return iface.ip
    raise RuntimeError("No Wi-Fi interface found!")


WIFI_IP = get_wifi_interface_ip()


def get_size(byte_size):
    for unit in ['', 'K', 'M', 'G', 'T', 'P']:
        if byte_size < 1024:
            return f"{byte_size:.2f}{unit}B"
        byte_size /= 1024
    return ValueError("Size too large to format")


def get_connections():
    global CONNECTION_MAP
    new_map = {}
    for conn in psutil.net_connections():
        if conn.laddr and conn.raddr and conn.pid:
            local = f"{conn.laddr.ip}:{conn.laddr.port}"
            remote = f"{conn.raddr.ip}:{conn.raddr.port}"
            new_map[(local, remote)] = conn.pid
            new_map[(remote, local)] = conn.pid

    CONNECTION_MAP = new_map
    # os.system("clear")
    # for conn, pid in CONNECTION_MAP.items():
    #     print(f"Connection: {conn[0]} -> {conn[1]} | PID: {pid}")


def connection_scheduler():
    while RUNNING:
        get_connections()
        time.sleep(DELAY)


def process_packet(packet):
    global CONNECTION_MAP
    global PROCESS_TRAFFIC_MAP
    # print(packet.summary())

    if packet.haslayer(IP):
        connection = (f"{packet[IP].src}:{packet[IP].sport}", f"{packet[IP].dst}:{packet[IP].dport}")
        packet_pid = CONNECTION_MAP.get(connection)
        if packet_pid:
            packet_src_ip = packet[IP].src
            packet_dst_ip = packet[IP].dst
            print(f"packet_src_ip: {packet_src_ip}, packet_dst_ip: {packet_dst_ip}, packet_pid: {packet_pid}")
            if packet_dst_ip == WIFI_IP:
                PROCESS_TRAFFIC_MAP[packet_pid][0] += len(packet)
            elif packet_src_ip == WIFI_IP:
                # print("Packet is to the Wi-Fi interface, processing traffic...")
                PROCESS_TRAFFIC_MAP[packet_pid][1] += len(packet)
            else:
                print(f"Packet is not to/from the Wi-Fi interface: {packet_src_ip} -> {packet_dst_ip}")
    else:
        pass  # discard non-IP packets (for now)


def process_and_print_traffic():
    global GLOBAL_DF
    processes = get_detailed_process_list()
    df = pd.DataFrame(processes)
    try:
        df = df.set_index("pid")
        df.sort_values("Download", inplace=True, ascending=False)
    except KeyError:
        pass
    printing_df = df.copy()
    try:
        printing_df["Download"] = printing_df["Download"].apply(get_size)
        printing_df["Upload"] = printing_df["Upload"].apply(get_size)
        printing_df["Download Speed"] = printing_df["Download Speed"].apply(get_size).apply(lambda s: f"{s}/s")
        printing_df["Upload Speed"] = printing_df["Upload Speed"].apply(get_size).apply(lambda s: f"{s}/s")
    except KeyError:
        pass
    # os.system("clear")
    # print(printing_df.to_string())
    GLOBAL_DF = df


def get_detailed_process_list():
    global GLOBAL_DF
    global PROCESS_TRAFFIC_MAP

    processes = []
    for pid, [upload_traffic, download_traffic] in PROCESS_TRAFFIC_MAP.items():
        try:
            process = psutil.Process(pid)
        except psutil.NoSuchProcess:
            continue  # what happens if the process is gone?
        name = process.name()
        create_time = derive_process_create_time(process)
        process_details = {
            "pid": pid,
            "name": name,
            "create_time": create_time,
            "Upload": upload_traffic,
            "Download": download_traffic,
        }
        # print(f"Processing PID: {pid}, Name: {name}, Upload: {upload_traffic}, Download: {download_traffic}")
        try:
            process_details["Upload Speed"] = upload_traffic - GLOBAL_DF.at[pid, "Upload"]
            process_details["Download Speed"] = download_traffic - GLOBAL_DF.at[pid, "Download"]
        except (KeyError, AttributeError):
            process_details["Upload Speed"] = upload_traffic
            process_details["Download Speed"] = download_traffic
        processes.append(process_details)
    return processes


def derive_process_create_time(process):
    try:
        create_time = datetime.fromtimestamp(process.create_time())
    except OSError:
        create_time = datetime.fromtimestamp(psutil.boot_time())
    return create_time


def publication_scheduler():
    while RUNNING:
        process_and_print_traffic()
        time.sleep(DELAY)



if __name__ == "__main__":
    connection_thread = threading.Thread(target=connection_scheduler)
    connection_thread.start()

    printing_thread = threading.Thread(target=publication_scheduler)
    printing_thread.start()

    print("Started sniffing")
    sniff(iface=WIFI_INTERFACE_NAME, filter="tcp", prn=process_packet, store=False)
