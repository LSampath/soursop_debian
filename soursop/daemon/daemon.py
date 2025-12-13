import logging
import signal
from pathlib import Path

from soursop import util
from soursop.daemon.network_tracker import start_network_tracking
from soursop.daemon.process_tracker import start_process_tracking
from soursop.daemon.utility_monitor import start_utility_monitor
from soursop.db.connection import init_db


def configure_logging():
    handlers = [logging.StreamHandler()]
    log_file = Path("/var/log/soursop/soursop.log")
    log_file.parent.mkdir(parents=True, exist_ok=True)
    handlers.append(logging.FileHandler(log_file))

    logging.root.handlers.clear()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=handlers,
    )
    logging.info("Logging configuration successful.")


def shutdown_handler(sig, frame):
    util.RUNNING_FLAG = False
    logging.info("Shutting down gracefully...")


if __name__ == "__main__":
    configure_logging()
    logging.info("Starting Soursop 1.0 daemon...")

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    init_db()
    start_utility_monitor()

    start_process_tracking()
    start_network_tracking()

# need to write a cleaner scheduler for both calculators
