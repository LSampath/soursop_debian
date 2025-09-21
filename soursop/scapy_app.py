# https://thepythoncode.com/article/make-a-network-usage-monitor-in-python
from scapy.sendrecv import sniff

from soursop import util


def process_packet(packet):
    print(packet)

def start_test_app():
    print("started sniffing thread.....")
    sniff(prn=process_packet, store=False, stop_filter=lambda _: not config.RUNNING_FLAG)
    print("Stopped sniffing...")
