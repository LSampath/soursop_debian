import datetime
import sys

from soursop.db_handler import init_db, get_usage


def bytes_today():
    start_date = datetime.date.today()
    start_date_str = start_date.isoformat()
    today_recv, today_sent = get_usage(start_date_str)
    print(f"Usage for today; sent: {today_sent}, received: {today_recv}")


def main():
    init_db()
    if len(sys.argv) != 2:
        bytes_today()
        print("Usage: soursop [timenow|count]")
        return

    cmd = sys.argv[1]
    if cmd == "today":
        bytes_today()
    else:
        print(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()
