from argparse import ArgumentTypeError
from datetime import datetime, date, timedelta
from typing import Optional

from soursop.beans import Level

RUNNING_FLAG = True
TEN_SECONDS = 10
FIVE_SECONDS = 5
FIFTEEN_SECONDS = 15
ONE_MINUTE = 60

BOLD_START = "\033[1m"
BOLD_END = "\033[0m"
DB_DATE_FORMAT = "%Y-%m-%d"
CONSOLE_DATE_FORMAT = "%d %b %Y"


def convert_bytes_to_human_readable(bytes_count):
    if bytes_count < 1024:
        return f"{bytes_count} B"
    elif bytes_count < 1024 ** 2:
        return f"{bytes_count / 1024:.2f} KB"
    elif bytes_count < 1024 ** 3:
        return f"{bytes_count / (1024 ** 2):.2f} MB"
    else:
        return f"{bytes_count / (1024 ** 3):.2f} GB"


def parse_level(argument: str) -> Level:
    mapping = {
        "hour": Level.HOUR, "h": Level.HOUR,
        "day": Level.DAY, "d": Level.DAY,
        "week": Level.WEEK, "w": Level.WEEK,
        "month": Level.MONTH, "m": Level.MONTH,
    }
    key = argument.lower()
    if key in mapping:
        return mapping[key]
    raise ArgumentTypeError(f"invalid --level value: {argument!r}. Allowed: hour/h, day/d, week/w, month/m")


def parse_date(s: str) -> date:
    try:
        return datetime.strptime(s, DB_DATE_FORMAT).date()
    except ValueError:
        raise ArgumentTypeError(f"Invalid date {s!r}, expected YYYY-MM-DD")


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


def derive_time_range(date_str: str, hour: int, level: Level) -> str:
    date_obj = datetime.strptime(date_str, DB_DATE_FORMAT).date()
    formatted_date = date_obj.strftime(CONSOLE_DATE_FORMAT)

    if level == Level.HOUR:
        return f"{formatted_date} {hour:02d}:00"
    elif level == Level.DAY:
        return formatted_date
    elif level == Level.MONTH:
        return date_obj.strftime("%B")
    else:
        week_num = date_obj.isocalendar().week
        return f"{week_num:02d}"
