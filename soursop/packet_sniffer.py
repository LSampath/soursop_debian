import threading

from scapy.sendrecv import sniff

from soursop import config


def process_packet(packet):
    print(packet)


def sniff_packets():
    print("started sniffing.....")
    sniff(prn=process_packet, store=False, stop_filter=lambda _: not config.RUNNING_FLAG)
    print("Stopped sniffing...")


def start_packet_sniffing():
    sniff_thread = threading.Thread(target=sniff_packets, daemon=True)
    sniff_thread.start()
