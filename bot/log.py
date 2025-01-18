import logging
from datetime import datetime as dt
from glob import glob as find

def _to_ansi(x: int) -> str:
    return f"\x1b[38;2;{x >> 16};{x >> 8 & 255};{x & 255}m"

white = "\x1b[37m"

grey = _to_ansi(0x424a54)
module_colour = _to_ansi(0x9100e6)

class _Formatter(logging.Formatter):
    COLOURS = {
        logging.DEBUG:    0x001be6,
        logging.INFO:     0x2ed5ff,
        logging.WARNING:  0xcdf723,
        logging.ERROR:    0xe32b2b,
        logging.CRITICAL: 0xf72323
    }

    FORMATS = {
        level: logging.Formatter(
            "\x1b[1m%s{asctime}  %s{levelname:<9}\x1b[0m %s{name}  %s{message}" % (
                grey, _to_ansi(_hex), module_colour, white
            ),
            "%d/%m/%Y %H:%M:%S",
            style = "{"
        )
        for level, _hex in COLOURS.items()
    }

    def __init__(self) -> None: ...

    def format(self, record: logging.LogRecord) -> str:
        formatter = self.FORMATS.get(record.levelno) or self.FORMATS[logging.DEBUG]

        if record.exc_info:
            exc_ansi = _to_ansi(0xff4545)
            
            text = formatter.formatException(record.exc_info)

            record.exc_text = f"{exc_ansi}{text}{white}"
        
        output = formatter.format(record)

        record.exc_info = None

        return output

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

    handler = logging.FileHandler(new_path)
    handler.setFormatter(_Formatter())

    return handler