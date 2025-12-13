from datetime import datetime

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


def format_date(date):
    return date.strftime('%A, %B %d, %Y')


def format_date_string(date_str):
    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
    return format_date(date_obj)
