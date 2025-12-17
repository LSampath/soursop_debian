from datetime import date

import soursop.db.network_repository as repository
from soursop import util
from soursop.beans import Level, NetworkUsage


def cumulate_by_time_level(entries: list[NetworkUsage], level: Level) -> list[NetworkUsage]:
    groups: dict[str, NetworkUsage] = {}
    for entry in entries:
        time_range_str = util.derive_time_range(entry.date_str, entry.hour, level)
        key = time_range_str
        if key in groups:
            group = groups[key]
            group.incoming_bytes = int((group.incoming_bytes or 0) + (entry.incoming_bytes or 0))
            group.outgoing_bytes = int((group.outgoing_bytes or 0) + (entry.outgoing_bytes or 0))
        else:
            groups[key] = NetworkUsage(
                date_str=time_range_str,
                incoming_bytes=int(entry.incoming_bytes or 0),
                outgoing_bytes=int(entry.outgoing_bytes or 0),
            )
    return list(groups.values())


def print_grouped_result(entries: list[NetworkUsage]):
    sorted_list = sorted(entries, key=lambda x: x.date_str)  # sorting does not work, check this
    if not sorted_list:
        print("No data available.")
    else:
        print(f"{util.BOLD_START}{'PERIOD':<20} {'SEND':>15} {'RECEIVED':>15}{util.BOLD_END}")
        for entry in sorted_list:
            sent = util.convert_bytes_to_human_readable(entry.outgoing_bytes)
            received = util.convert_bytes_to_human_readable(entry.incoming_bytes)
            print(f"{entry.date_str:<20} {sent:>15} {received:>15}")


def handle_network_request(args):
    level = args.level if args.level else Level.HOUR
    from_date, to_date = util.derive_date_period(args)
    log_command(level, from_date, to_date)

    entries = repository.search(from_date, to_date)
    grouped = cumulate_by_time_level(entries, level or Level.HOUR)
    print_grouped_result(grouped)


def log_command(level: Level, from_date: date, to_date: date):
    message = f"Network usage logs from [{from_date}] to [{to_date}] cumulated by [{level}]\n"
    print(message)


def register_network_controller(subparsers):
    network_parser = subparsers.add_parser("network", help="Total usage of network adapter")

    network_parser.add_argument("-l", "--level", dest="level", type=util.parse_level,
                                required=False, help="Aggregation level: hour/h, day/d, week/w or month/m")

    network_parser.add_argument("-f", "--from", dest="from_date", type=util.parse_date,
                                required=False, help="Start date YYYY-MM-DD")
    network_parser.add_argument("-t", "--to", dest="to_date", type=util.parse_date,
                                required=False, help="End date YYYY-MM-DD")

    time_window_group = network_parser.add_mutually_exclusive_group(required=False)
    time_window_group.add_argument("-d", "--day", dest="day", type=int, help="Look back N days")
    time_window_group.add_argument("-w", "--week", dest="week", type=int, help="Look back N weeks")
    time_window_group.add_argument("-m", "--month", dest="month", type=int, help="Look back N months")

    network_parser.set_defaults(func=handle_network_request)
