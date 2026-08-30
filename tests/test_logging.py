from __future__ import annotations

import logging

from utils import logger_manager


def test_default_logging_has_no_console_stream_handler(monkeypatch) -> None:
    monkeypatch.delenv("WPI_LOG_TO_FILE", raising=False)
    logger_manager._configured = False

    logger_manager.configure_logging()

    handlers = logging.getLogger().handlers
    assert len(handlers) == 1
    assert type(handlers[0]) is logging.NullHandler
