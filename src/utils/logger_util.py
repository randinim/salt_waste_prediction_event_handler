import logging
import sys

class ColoredFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': '\033[94m',    # Blue
        'INFO': '\033[92m',     # Green
        'WARNING': '\033[93m',  # Yellow
        'ERROR': '\033[91m',    # Red
        'CRITICAL': '\033[95m', # Magenta
    }
    RESET = '\033[0m'

    def format(self, record):
        color = self.COLORS.get(record.levelname, self.RESET)
        # Save the original levelname
        original_levelname = record.levelname
        # Colorize only the levelname
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        message = super().format(record)
        # Restore the original levelname
        record.levelname = original_levelname
        return message


def get_logger(name=__name__, log_file=None, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    if not logger.handlers:
        # Console handler with color
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(level)
        ch.setFormatter(ColoredFormatter('%(asctime)s|%(levelname)s|%(message)s', '%Y-%m-%d %H:%M:%S'))
        logger.addHandler(ch)

        # Optional file handler (no color)
        if log_file:
            fh = logging.FileHandler(log_file)
            fh.setLevel(level)
            fh.setFormatter(logging.Formatter('%(asctime)s|%(levelname)s|%(message)s', '%Y-%m-%d %H:%M:%S'))
            logger.addHandler(fh)

    return logger

logger = get_logger(__name__)