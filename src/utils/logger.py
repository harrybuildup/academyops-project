# src/utils/logger.py
#
# Dual logging: stdout (for Docker/container runtimes) + file (academyops.log)
# for post-incident diagnosis as required by WP-01 FR-7.

import logging
import os
from pathlib import Path

LOG_FORMAT = "[%(asctime)s] %(levelname)s %(name)s - %(message)s"
LOG_DATEFMT = "%Y-%m-%d %H:%M:%S"

# Log file lives at the project root (next to main.py / pyproject.toml).
_LOG_FILE = Path(__file__).resolve().parent.parent.parent / "academyops.log"


def _build_logger() -> logging.Logger:
    logger = logging.getLogger("AcademyOps")
    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATEFMT)

    # ── Console handler (always active) ──────────────────────────────────
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # ── File handler (best-effort — skipped in read-only environments) ───
    try:
        file_handler = logging.FileHandler(_LOG_FILE, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except OSError:
        # Read-only filesystem (e.g. some Docker setups) — stdout is enough.
        logger.debug("Could not open log file %s; falling back to console only.", _LOG_FILE)

    return logger


logger = _build_logger()
