# src/utils/logger.py
#
# Logs to stdout only — Docker/container runtimes capture stdout automatically.
# No file handler; no filesystem dependency.

import logging


def _build_logger() -> logging.Logger:
    logger = logging.getLogger("AcademyOps")
    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "[%(asctime)s] %(levelname)s %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    logger.addHandler(handler)
    return logger


logger = _build_logger()
