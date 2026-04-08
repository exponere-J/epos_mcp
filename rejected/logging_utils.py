from __future__ import annotations

import logging
from pathlib import Path

_LOGGER_CACHE: dict[str, logging.Logger] = {}


def get_logger(name: str = "next_steps") -> logging.Logger:
    """Return a logger that logs to console and logs/next_steps.log."""
    if name in _LOGGER_CACHE:
        return _LOGGER_CACHE[name]

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if logger.handlers:
        _LOGGER_CACHE[name] = logger
        return logger

    logs_dir = Path("logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = logs_dir / "next_steps.log"

    fmt = logging.Formatter(
        "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
        "%Y-%m-%d %H:%M:%S",
    )

    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(fmt)

    ch = logging.StreamHandler()
    ch.setFormatter(fmt)

    logger.addHandler(fh)
    logger.addHandler(ch)

    _LOGGER_CACHE[name] = logger
    return logger
