import os


def get_physical_interfaces():
    net_path = "/sys/class/net/"
    return [
        iface for iface in os.listdir(net_path)
        if os.path.exists(os.path.join(net_path, iface, "device"))
    ]


if __name__ == "__main__":
    interfaces = get_physical_interfaces()
    for face in interfaces:
        print(face, type(face))
