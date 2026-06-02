# src/utils/logger.py
import logging
import os

def setup_logger(log_file: str = "academyops.log") -> logging.Logger:
    """Configures a standardized application logger for AcademyOps."""
    logger = logging.getLogger("AcademyOps")
    
    # Avoid adding duplicate handlers if re-imported
    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.INFO)

    # High-clarity production log structure showing timestamp, level, and line location
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 1. Mandatory File Log Handler
    log_dir = os.path.dirname(log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
        
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)

    # 2. Local Terminal Debugging Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)

    return logger

# Single instance to export everywhere
logger = setup_logger()