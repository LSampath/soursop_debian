import sys
from datetime import datetime

from soursop.db_handler import init_db, get_counter


def count():
    print(f"Current count: {get_counter()}")


def timenow():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"Current time is: {now}")


def main():
    init_db()
    if len(sys.argv) != 2:
        print("Usage: soursop [timenow|count]")
        return

    cmd = sys.argv[1]
    if cmd == "timenow":
        timenow()
    elif cmd == "count":
        count()
    else:
        print(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()
