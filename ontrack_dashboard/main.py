#!/usr/bin/env python3
"""Entry point for the OnTrack dashboard."""

from __future__ import annotations

import logging
import sys

from PyQt6.QtWidgets import QApplication

from ontrack_dashboard.app import MainWindow
from ontrack_dashboard.logging_bridge import install_qt_log_handler


def configure_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    # Also capture into the Qt log bus so the in-app console can show
    # DEBUG records that the stream handler filters out.
    install_qt_log_handler(level=logging.DEBUG)


def main() -> int:
    configure_logging()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
