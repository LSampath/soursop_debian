import logging
from collections import defaultdict
from datetime import datetime
from threading import Thread
from time import sleep

from scapy.layers.inet import IP, TCP, UDP
from scapy.layers.inet6 import IPv6
from scapy.sendrecv import sniff

from soursop import util
from soursop.batch_deque import BatchDeque
from soursop.beans import ProcessInfo, ProcessUsage
from soursop.db_handler import get_process_usage_by_pid_name
from soursop.process_handler import get_process_info
from soursop.utility_monitor import get_wifi_ips, start_utility_monitor, get_connection_pid

# thread safe queue to temporarily hold process_usage entries
_USAGE_QUEUE = BatchDeque()


def get_packet_connection(packet) -> tuple | None:
    try:
        if IP in packet:
            ip_packet = packet[IP]
            src_ip, dst_ip = ip_packet.src, ip_packet.dst
        elif IPv6 in packet:
            ipv6_packet = packet[IPv6]
            src_ip, dst_ip = ipv6_packet.src, ipv6_packet.dst
        else:
            return None

        if TCP in packet:
            tcp_packet = packet[TCP]
            src_port, dst_port = tcp_packet.sport, tcp_packet.dport
        elif UDP in packet:
            udp_packet = packet[UDP]
            src_port, dst_port = udp_packet.sport, udp_packet.dport
        else:
            return None

        return src_port, dst_port, src_ip, dst_ip
    except (AttributeError, IndexError):
        return None


def process_packet(packet) -> None:
    """
    find destination and source ports of each packet to determine which connection this packet belongs
    and update the CONNECTION_PID_MAP
    """
    global _USAGE_QUEUE
    wifi_ip_set = get_wifi_ips()
    packet_connection_info = get_packet_connection(packet)

    if packet_connection_info:
        src_port, dst_port, src_ip, dst_ip = packet_connection_info
        packet_pid = get_connection_pid((src_port, dst_port))

        if packet_pid:
            process_info = get_process_info(packet_pid)
            if process_info:
                usage = get_process_usage(process_info)
                if src_ip and src_ip in wifi_ip_set:
                    usage.outgoing_bytes = len(packet)  # outgoing/upload
                elif dst_ip and dst_ip in wifi_ip_set:
                    usage.incoming_bytes = len(packet)  # incoming/download
                else:
                    return
                _USAGE_QUEUE.put(usage)


def get_process_usage(process_info: ProcessInfo) -> ProcessUsage:
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    return ProcessUsage(pid=process_info.pid, name=process_info.name, path=process_info.path,
                        date_str=date_str, hour=now.hour, network='wi-fi')


def sniff_packets() -> None:
    logging.info("started sniffing thread")
    sniff(prn=process_packet, store=False, filter="(ip or ip6) and (tcp or udp)",
          stop_filter=lambda _: not util.RUNNING_FLAG)
    logging.info("Stopped sniffing thread")


def group_by_pid_name(entries: list[ProcessUsage]) -> list[list[ProcessUsage]]:
    groups = defaultdict(list)
    for entry in entries:
        key = f"{entry.pid}_{entry.name}"
        groups[key].append(entry)
    return list(groups.values())


def cumulate_by_time(entries: list[ProcessUsage]) -> list[ProcessUsage]:
    cumulated_map = {}
    for entry in entries:
        key = f"{entry.date_str}_{entry.hour}"
        if key in cumulated_map:
            existing = cumulated_map[key]
            existing.incoming_bytes += entry.incoming_bytes
            existing.outgoing_bytes += entry.outgoing_bytes
            existing.packet_count += entry.packet_count
        else:
            cumulated_map[key] = entry
    return list(cumulated_map.values())


def merge_entries(old_entries: list[ProcessUsage],
                  new_entries: list[ProcessUsage]) -> list[ProcessUsage]:
    result = {f"{e.date_str}_{e.hour}": e for e in old_entries}
    for new in new_entries:
        key = f"{new.date_str}_{new.hour}"
        if key in result:
            old = result[key]
            old.incoming_bytes += new.incoming_bytes
            old.outgoing_bytes += new.outgoing_bytes
            old.packet_count += new.packet_count
        else:
            result[key] = new
    return list(result.values())


def handle_entries(all_entries: list[ProcessUsage]) -> None:
    pid_name_group_list = group_by_pid_name(all_entries)
    for pid_name_group in pid_name_group_list:
        if pid_name_group:
            pid, name = pid_name_group[0]
            old_db_entries = get_process_usage_by_pid_name(pid, name)
            time_cumulated_entries = cumulate_by_time(pid_name_group)
            merged_entries = merge_entries(old_db_entries, time_cumulated_entries)

    # append to each group
    # update them


def save_usages():
    logging.info("Started usage saving thread....")
    while util.RUNNING_FLAG:
        usage_entries = _USAGE_QUEUE.drain()
        handle_entries(usage_entries)
        sleep(util.ONE_MINUTE)
    logging.info("Stopped usage saving thread.....")


def start_packet_sniffing():
    sniff_thread = Thread(target=sniff_packets, daemon=False)  # why not daemon ????
    sniff_thread.start()

    save_usage_thread = Thread(target=save_usages, daemon=True)
    save_usage_thread.start()


# remove later
if __name__ == "__main__":
    print("Starting soursop daemon service..... using main method")
    start_utility_monitor()
    start_packet_sniffing()

# TODO list
# make sure this shutdown gracefully, when daemon is shutting down
# think about the usage frequency, may be calculation frequency is good enough, saving frequency can be slower
