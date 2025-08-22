# https://thepythoncode.com/article/make-a-network-usage-monitor-in-python
from scapy.sendrecv import sniff


def process_packet(packet):
    print(packet)


def start_test_app():
    print("started sniffing.....")
    sniff(prn=process_packet, store=False)
