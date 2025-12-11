from argparse import ArgumentTypeError


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


def handle_network_request(args):
    print(args)


def register_network_controller(subparsers):
    network_parser = subparsers.add_parser("network", help="Total usage of network adapter")

    network_parser.add_argument("-l", "--level",
                                type=normalize_level,
                                choices=["day", "week", "month", "hour"],
                                required=False,
                                help="Aggregation level: day/d, week/w, month/m or hour/h")

    group = network_parser.add_mutually_exclusive_group(required=False)
    group.add_argument("-d", "--day", type=int, help="Look back N days")
    # group.add_argument("-w", "--week", type=int, help="Look back N weeks")
    # group.add_argument("-m", "--month", type=int, help="Look back N months")

    network_parser.set_defaults(func=handle_network_request)
