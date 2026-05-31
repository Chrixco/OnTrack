"""Bridge between Python's `logging` and a Qt signal/buffer.

Installs a logging.Handler at the root logger that:
  * keeps the most recent N records in a ring buffer (so a console
    window can replay history when it's opened mid-session), and
  * emits a Qt signal for every new record (so a live console can
    append in real time).

The handler is global; the console window subscribes/unsubscribes as it
opens and closes, but the buffer keeps filling either way.
"""

from __future__ import annotations

import logging
from collections import deque

from PyQt6.QtCore import QObject, pyqtSignal

_MAX_BUFFER_RECORDS = 5000


class LogBus(QObject):
    """Module-level singleton that holds the log buffer + Qt signal."""

    message_emitted = pyqtSignal(object)  # logging.LogRecord

    _instance: LogBus | None = None

    def __init__(self) -> None:
        super().__init__()
        self.buffer: deque[logging.LogRecord] = deque(maxlen=_MAX_BUFFER_RECORDS)

    @classmethod
    def instance(cls) -> LogBus:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


class _QtLogHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            bus = LogBus.instance()
            bus.buffer.append(record)
            bus.message_emitted.emit(record)
        except Exception:  # pragma: no cover - defensive
            self.handleError(record)


_installed = False


def install_qt_log_handler(level: int = logging.DEBUG) -> None:
    """Attach the bridge to the root logger. Safe to call multiple times."""
    global _installed
    if _installed:
        return
    handler = _QtLogHandler()
    handler.setLevel(level)
    logging.getLogger().addHandler(handler)
    # The root logger's level is what gates whether records reach handlers.
    # We want DEBUG to be capturable for the live console even if the
    # default stream handler stays at INFO.
    if logging.getLogger().level == 0 or logging.getLogger().level > level:
        logging.getLogger().setLevel(level)
    _installed = True
