"""Console-only logging setup for the Billing CLI.

All output is written to stderr/stdout via the standard `logging` module.
No log files are created, and no network handlers are attached, in
keeping with the offline-only constraint.
"""

import logging
import sys

_LOG_FORMAT = "%(levelname)s: %(message)s"


def get_logger(name: str = "billing_cli") -> logging.Logger:
    """Return a configured logger that writes to the console only.

    Subsequent calls with the same `name` return the same logger instance
    without adding duplicate handlers.
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(stream=sys.stderr)
        handler.setFormatter(logging.Formatter(_LOG_FORMAT))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False

    return logger
