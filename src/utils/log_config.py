"""Logging config setup"""

import logging, sys

# returns logger with two-destination observability
def setup_logging():
    # set debug
    logger = logging.getLogger("session")
    logger.setLevel(logging.DEBUG)

    # format logs for readability
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    # set console for info logging and above
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(fmt=fmt)

    # set file for debug and above
    file = logging.FileHandler("session.log")
    file.setLevel(logging.DEBUG)
    file.setFormatter(fmt=fmt)

    # add handlers to session logger
    logger.addHandler(console)
    logger.addHandler(file)

    return logger