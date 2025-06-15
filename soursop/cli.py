import argparse
import datetime

from soursop.db_handler import init_db, get_usage_by_date, get_usage_by_date_range


def convert_bytes_to_human_readable(bytes_count):
    if bytes_count < 1024:
        return f"{bytes_count} B"
    elif bytes_count < 1024 ** 2:
        return f"{bytes_count / 1024:.2f} KB"
    elif bytes_count < 1024 ** 3:
        return f"{bytes_count / (1024 ** 2):.2f} MB"
    else:
        return f"{bytes_count / (1024 ** 3):.2f} GB"


def usage_today():
    """
    Display today's network usage.
    """
    today_date = datetime.date.today()
    today_str = today_date.isoformat()

    today_recv, today_sent = get_usage_by_date(today_str)
    today_recv = convert_bytes_to_human_readable(today_recv)
    today_sent = convert_bytes_to_human_readable(today_sent)

    print(f"Date: {today_date.strftime('%A, %B %d, %Y')}\nSent: {today_sent} | Received: {today_recv}")


def usage_this_week():
    """
    Display network usage for the last 7 days, including today.
    """
    end_date = datetime.date.today()
    end_date_str = end_date.isoformat()
    start_date = end_date - datetime.timedelta(days=6)
    start_date_str = start_date.isoformat()

    result = get_usage_by_date_range(start_date_str, end_date_str)
    print(f"{'Date':<12} {'Sent':>15} {'Received':>18}")
    print("-" * 45)
    for date, received, sent in result:
        sent = convert_bytes_to_human_readable(sent)
        received = convert_bytes_to_human_readable(received)
        print(f"{date:<12} {sent:>15} {received:>18}")


def init_arg_parser():
    parser = argparse.ArgumentParser(prog="soursop", description="A network analysis tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    parser_today = subparsers.add_parser("today", help="Show today's network usage")
    parser_today.set_defaults(func=usage_today)

    parser_week = subparsers.add_parser("week", help="Show last 7 days network usage")
    parser_week.set_defaults(func=usage_this_week)

    args = parser.parse_args()
    args.func()


def main():
    init_db()
    init_arg_parser()


if __name__ == "__main__":
    main()
