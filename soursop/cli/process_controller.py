from datetime import date, datetime
from typing import Optional

import soursop.db.process_repository as repository
from soursop import util
from soursop.beans import ProcessUsage, Level


def cumulate_by_time_level(entries: list[ProcessUsage], level: Level) -> list[ProcessUsage]:
    groups: dict[tuple[str, str, str], ProcessUsage] = {}
    for entry in entries:
        time_range_str = util.derive_time_range(entry.date_str, entry.hour, level)
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
    sorted_list = sorted(entries, key=lambda x: (x.date_str, x.name, x.path))  # sorting does not work, check this
    if not sorted_list:
        print("No data available.")
    else:
        print(f"{util.BOLD_START}{'PERIOD':<20} {'SEND':>15} {'RECEIVED':>15} {'':>5} NAME (ADDRESS) {util.BOLD_END}")
        for entry in sorted_list:
            sent = util.convert_bytes_to_human_readable(entry.outgoing_bytes)
            received = util.convert_bytes_to_human_readable(entry.incoming_bytes)
            print(f"{entry.date_str:<20} {sent:>15} {received:>15} {'':>5} {entry.name} ({entry.path})")


def log_command(level: Level, from_date: date, to_date: date, name: Optional[str]):
    message = "Process usage logs"
    if name:
        message += f" for [{name}]"
    message += f" from [{from_date}] to [{to_date}] cumulated by [{level}]\n"
    print(message)


def handle_process_request(args):
    level = args.level if args.level else Level.HOUR
    from_date, to_date = util.derive_date_period(args)
    name = args.name if args.name else None
    log_command(level, from_date, to_date, name)

    entries = repository.search(from_date, to_date, name)
    grouped = cumulate_by_time_level(entries, level or Level.HOUR)
    print_grouped_result(grouped)


def register_process_controller(subparsers):
    process_parser = subparsers.add_parser("process", help="Total usage of each process")

    process_parser.add_argument("-l", "--level", dest="level", type=util.parse_level,
                                required=False, help="Aggregation level: day/d, week/w or month/m")

    process_parser.add_argument("-n", "--name", dest="name", type=str, required=False, help="Process name")

    process_parser.add_argument("-f", "--from", dest="from_date", type=util.parse_date,
                                required=False, help="Start date YYYY-MM-DD")
    process_parser.add_argument("-t", "--to", dest="to_date", type=util.parse_date,
                                required=False, help="End date YYYY-MM-DD")

    time_window_group = process_parser.add_mutually_exclusive_group(required=False)
    time_window_group.add_argument("-d", "--day", dest="day", type=int, help="Look back N days")
    time_window_group.add_argument("-w", "--week", dest="week", type=int, help="Look back N weeks")
    time_window_group.add_argument("-m", "--month", dest="month", type=int, help="Look back N months")

    process_parser.set_defaults(func=handle_process_request)
