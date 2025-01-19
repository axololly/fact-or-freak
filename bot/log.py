import logging
from datetime import datetime as dt
from glob import glob as find

def get_handler() -> logging.FileHandler:
    "Returns a `FileHandler` pointing to the latest log file."

    previous_file_datetimes: list[dt] = [
        dt.strptime(path, r"logs\%d-%M-%Y.log")
        for path in find(r"logs\*.log")
    ]

    now = dt.now()

    if previous_file_datetimes:
        latest = max(previous_file_datetimes)

        if (now - latest).days >= 1:
            latest = dt.now()
    else:
        latest = dt.now()

    new_path = latest.strftime("logs/%d-%m-%Y.log")

    with open(new_path, 'w'): ...

    return logging.FileHandler(new_path)