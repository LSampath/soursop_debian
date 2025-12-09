import argparse
import datetime

from soursop.db_handler import get_network_usage_by_date, get_network_usage_by_date_range
from soursop.util import convert_bytes_to_human_readable, format_date, format_date_string


def usage_today():
    """
    Display today's network usage.
    """
    today_date = datetime.date.today()
    today_str = today_date.isoformat()

    today_recv, today_sent = get_network_usage_by_date(today_str)
    today_recv = convert_bytes_to_human_readable(today_recv)
    today_sent = convert_bytes_to_human_readable(today_sent)

    print(f"Date: {format_date(today_date)}\nSent: {today_sent} | Received: {today_recv}")


def network_usage():
    """
    Display daily network usage for the last 7 days, including today.
    """
    end_date = datetime.date.today()
    end_date_str = end_date.isoformat()
    start_date = end_date - datetime.timedelta(days=6)
    start_date_str = start_date.isoformat()

    result = get_network_usage_by_date_range(start_date_str, end_date_str)
    if not result:
        print("No data available for the last 7 days.")
    else:
        print(f"{'Date':<25} {'Sent':>20} {'Received':>20}")
        print("-" * 70)
        for date, received, sent in result:
            sent = convert_bytes_to_human_readable(sent)
            received = convert_bytes_to_human_readable(received)
            print(f"{format_date_string(date):<25} {sent:>20} {received:>20}")


def init_arg_parser():
    parser = argparse.ArgumentParser(prog="soursop", description="A network analysis tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    parser_today = subparsers.add_parser("today", help="Show today's network usage")
    parser_today.set_defaults(func=usage_today)

    parser_week = subparsers.add_parser("daily", help="Show last 7 days network usage")
    parser_week.set_defaults(func=network_usage)

    args = parser.parse_args()
    args.func()


def main():
    init_arg_parser()


if __name__ == "__main__":
    main()
