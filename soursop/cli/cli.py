import argparse

from soursop.cli.network_controller import register_network_controller
from soursop.cli.process_controller import register_process_controller


def init_arg_parser():
    parser = argparse.ArgumentParser(prog="soursop", description="A network analysis tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    register_network_controller(subparsers)
    register_process_controller(subparsers)

    args = parser.parse_args()
    args.func(args)


def main():
    init_arg_parser()


if __name__ == "__main__":
    main()
