import psutil


def this_is_something():
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            conns = proc.net_connections(kind='inet')
            if conns:
                print(f"{proc.info['name']} ({proc.info['pid']}) has connections:")
                for c in conns:
                    print(f"  {c.laddr} -> {c.raddr} status: {c.status}")
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            continue


def get_active_processes():
    """
    Get a list of active processes with their network connections.
    """
    active_processes = []
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            conns = proc.net_connections(kind='inet')
            if conns:
                active_processes.append((proc.info['pid'], proc.info['name']))
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            continue
    return active_processes


def get_processes_with_connections():
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            connections = proc.connections(kind='inet')
            if connections:
                print(f"\n🔌 PID: {proc.pid} | Name: {proc.name()}")
                for conn in connections:
                    laddr = f"{conn.laddr.ip}:{conn.laddr.port}"
                    raddr = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "N/A"
                    print(f"    {laddr} -> {raddr} [{conn.status}]")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue


# this_is_something()
get_processes_with_connections()


# if __name__ == "__main__":
#     for pid, name in get_active_processes():
#         print(f"PID: {pid:<7} Name: {name}")
