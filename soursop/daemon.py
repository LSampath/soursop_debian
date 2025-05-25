import time

from soursop.db_handler import init_db, set_counter, get_counter


def main():
    init_db()
    while True:
        count = get_counter() + 1
        set_counter(count)
        time.sleep(5)


if __name__ == "__main__":
    main()
