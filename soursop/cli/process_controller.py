from argparse import ArgumentTypeError
from datetime import date, datetime, timedelta
from typing import Optional

import soursop.db.process_repository as repository
from soursop.beans import ProcessUsage


def normalize_level(argument: str) -> str:
    mapping = {
        "day": "day", "d": "day",
        "week": "week", "w": "week",
        "month": "month", "m": "month",
        "hour": "hour", "h": "hour",
    }
    key = argument.lower()
    if key in mapping:
        return mapping[key]
    raise ArgumentTypeError(f"invalid --level value: {argument!r}. Allowed: day/d, week/w, month/m, hour/h")


def parse_date(s: str) -> date:
    date_format = "%Y-%m-%d"
    try:
        return datetime.strptime(s, date_format).date()
    except ValueError:
        raise ArgumentTypeError(f"Invalid date {s!r}, expected YYYY-MM-DD")


def compute_range_from_window(days: Optional[int] = None,
                              weeks: Optional[int] = None,
                              months: Optional[int] = None) -> tuple[date, date]:
    today = date.today()
    if days is not None:
        start = today - timedelta(days=days - 1)
        end = today
    elif weeks is not None:
        start = today - timedelta(weeks=weeks) + timedelta(days=1)  # adjust to include today
        end = today
    elif months is not None:
        # crude month handling: approximate by 30 days (or implement proper month arithmetic)
        start = today - timedelta(days=30 * months - 1)
        end = today
    else:
        raise ArgumentTypeError("No window specified")
    return start, end


def derive_date_period(args) -> tuple[date, date]:
    """Return (start_date, end_date). Enforce either one window OR a date range."""
    window_used = any(getattr(args, name) is not None for name in ("day", "week", "month"))
    range_used = (args.from_date is not None) or (args.to_date is not None)

    if window_used and range_used:
        raise ArgumentTypeError(
            "Error: provide either a window (--day/--week/--month) OR a date range (--from/--to), not both.")
    if window_used:
        return compute_range_from_window(days=args.day, weeks=args.week, months=args.month)

    if range_used:
        if args.from_date is None or args.to_date is None:
            raise ArgumentTypeError("Error: both --from and --to must be provided for a date range.")
        if args.from_date > args.to_date:
            raise ArgumentTypeError("Error: --from must be <= --to.")
        return args.from_date, args.to_date
    return compute_range_from_window(days=1)


def group_by_level(entries: list[ProcessUsage], level: Optional[str]) -> list[ProcessUsage]:
    # implement this


def handle_process_request(args):
    level = args.level if args.level else "hour"
    start_date, to_date = derive_date_period(args)
    name = args.name if args.name else None
    print(f"log level - {level}, name - {name} start_date - {start_date}, end_date - {to_date}")

    entries = repository.search(start_date, to_date, name)
    grouped = group_by_level(entries, level)
    print_result(grouped)


def register_process_controller(subparsers):
    process_parser = subparsers.add_parser("process", help="Total usage of each process")

    process_parser.add_argument("-l", "--level", dest="level",
                                type=normalize_level, choices=["day", "week", "month", "hour"],
                                required=False, help="Aggregation level: day/d, week/w or month/m")

    process_parser.add_argument("-n", "--name", dest="name", type=str, required=False, help="Process name")

    process_parser.add_argument("-f", "--from", dest="from_date", type=parse_date,
                                required=False, help="Start date YYYY-MM-DD")
    process_parser.add_argument("-t", "--to", dest="to_date", type=parse_date,
                                required=False, help="End date YYYY-MM-DD")

    time_window_group = process_parser.add_mutually_exclusive_group(required=False)
    time_window_group.add_argument("-d", "--day", dest="day", type=int, help="Look back N days")
    time_window_group.add_argument("-w", "--week", dest="week", type=int, help="Look back N weeks")
    time_window_group.add_argument("-m", "--month", dest="month", type=int, help="Look back N months")

    process_parser.set_defaults(func=handle_process_request)
