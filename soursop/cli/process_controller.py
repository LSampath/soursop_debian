from argparse import ArgumentTypeError
from datetime import date, datetime, timedelta
from typing import Optional

import soursop.db.process_repository as repository
from soursop.beans import ProcessUsage, Level
from soursop.util import convert_bytes_to_human_readable, BOLD_START, BOLD_END


def parse_level(argument: str) -> Level:
    mapping = {
        "day": Level.DAY, "d": Level.DAY,
        "week": Level.WEEK, "w": Level.WEEK,
        "month": Level.MONTH, "m": Level.MONTH,
        "hour": Level.HOUR, "h": Level.HOUR,
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


def derive_time_range(date_str: str, hour: int, level: Level) -> str:
    date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
    formatted_date = date_obj.strftime("%d %b %Y")

    if level == Level.HOUR:
        return f"{formatted_date} {hour:02d}:00"
    elif level == Level.DAY:
        return formatted_date
    elif level == Level.MONTH:
        return date_obj.strftime("%B")
    else:
        week_num = date_obj.isocalendar().week
        return f"{week_num:02d}"


def cumulate_by_time_level(entries: list[ProcessUsage], level: Level) -> list[ProcessUsage]:
    groups: dict[tuple[str, str, str], ProcessUsage] = {}
    for entry in entries:
        time_range_str = derive_time_range(entry.date_str, entry.hour, level)
        key = (entry.name, entry.path, time_range_str)
        if key in groups:
            group = groups[key]
            group.incoming_bytes = int((group.incoming_bytes or 0) + (entry.incoming_bytes or 0))
            group.outgoing_bytes = int((group.outgoing_bytes or 0) + (entry.outgoing_bytes or 0))
        else:
            groups[key] = ProcessUsage(
                hour=0, pid=0,
                name=entry.name,
                path=entry.path or "",
                date_str=time_range_str,
                incoming_bytes=int(entry.incoming_bytes or 0),
                outgoing_bytes=int(entry.outgoing_bytes or 0),
            )
    return list(groups.values())


def print_grouped_result(entries: list[ProcessUsage]):
    sorted_list = sorted(entries, key=lambda x: (x.date_str, x.name, x.path)) # sorting does not work, check this
    if not sorted_list:
        print("No data available.")
    else:
        print(f"{BOLD_START}{'PERIOD':<20} {'SEND':>15} {'RECEIVED':>15} {'':>5} NAME (ADDRESS) {BOLD_END}")
        for entry in sorted_list:
            sent = convert_bytes_to_human_readable(entry.outgoing_bytes)
            received = convert_bytes_to_human_readable(entry.incoming_bytes)
            print(f"{entry.date_str:<20} {sent:>15} {received:>15} {'':>5} {entry.name} ({entry.path})")


def log_command(level: Level, from_date: date, to_date: date, name: Optional[str]):
    message = "Process usage logs"
    if name:
        message += f" for [{name}]"
    message += f" from [{from_date}] to [{to_date}] cumulated by [{level}]\n"
    print(message)


def handle_process_request(args):
    level = args.level if args.level else Level.HOUR
    from_date, to_date = derive_date_period(args)
    name = args.name if args.name else None
    log_command(level, from_date, to_date, name)

    entries = repository.search(from_date, to_date, name)
    grouped = cumulate_by_time_level(entries, level or Level.HOUR)
    print_grouped_result(grouped)


def register_process_controller(subparsers):
    process_parser = subparsers.add_parser("process", help="Total usage of each process")

    process_parser.add_argument("-l", "--level", dest="level", type=parse_level,
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
