"""Explicit, side-effect-free logging configuration."""

from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path


_configured = False


def configure_logging() -> None:
    global _configured
    if _configured:
        return
    level_name = os.environ.get("WPI_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    # Console output is produced explicitly by the application.  Logging must
    # not duplicate it with a StreamHandler, so a silent handler is the
    # default and an optional file handler is the only emitted log target.
    handlers: list[logging.Handler] = [logging.NullHandler()]
    log_to_file = os.environ.get("WPI_LOG_TO_FILE", "0").lower() in {
        "1",
        "true",
        "yes",
    }
    if log_to_file:
        log_dir = Path(os.environ.get("WPI_LOG_DIR", "logs"))
        log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        handlers = [
            logging.FileHandler(
                log_dir / f"app_{timestamp}.log",
                encoding="utf-8",
            )
        ]
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers,
        force=True,
    )
    _configured = True


def get_logger(name: str | None = None) -> logging.Logger:
    return logging.getLogger(name or __name__)


def clean_logs_directory(
    logs_dir: str = "logs",
    keep_latest: int = 10,
) -> int:
    path = Path(logs_dir)
    if not path.is_dir():
        return 0
    files = sorted(
        (item for item in path.glob("app_*.log") if item.is_file()),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )
    removed = 0
    for item in files[keep_latest:]:
        item.unlink()
        removed += 1
    return removed
