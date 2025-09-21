from datetime import datetime

RUNNING_FLAG = True
INTERVAL = 10


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
