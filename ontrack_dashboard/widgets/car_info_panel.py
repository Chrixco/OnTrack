"""Left panel: car + driver + track identification."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFontMetrics, QPainter

from ontrack_dashboard.telemetry import SessionInfo
from ontrack_dashboard.theme import (
    ACCENT_CYAN,
    FG_MUTED,
    FG_PRIMARY,
    FG_SUBTLE,
    FONT_BODY_BOLD,
    FONT_LABEL_CAPS,
    FONT_NUMERIC_SMALL,
)
from ontrack_dashboard.widgets.card import NeumorphCard


class CarInfoPanel(NeumorphCard):
    """Static session metadata: car, driver, track. Updated on each handshake."""

    def __init__(self) -> None:
        super().__init__(accent=ACCENT_CYAN)
        self._session = SessionInfo()
        self._connected = False
        self.setMinimumWidth(260)

    def set_session(self, session: SessionInfo) -> None:
        self._session = session
        self.update()

    def set_connected(self, connected: bool) -> None:
        self._connected = connected
        self.update()

    def paint_content(self, painter: QPainter) -> None:
        rect = self.content_rect()
        x = rect.left()
        y = rect.top()
        w = rect.width()

        # Title
        title_font = FONT_BODY_BOLD.to_qfont()
        title_font.setPointSize(14)
        painter.setFont(title_font)
        painter.setPen(FG_PRIMARY)
        painter.drawText(x, y, w, 22, Qt.AlignmentFlag.AlignLeft, "CAR INFO")

        # Connection chip
        chip_font = FONT_LABEL_CAPS.to_qfont()
        painter.setFont(chip_font)
        chip_text = "LIVE" if self._connected else "WAITING"
        chip_color = ACCENT_CYAN if self._connected else FG_SUBTLE
        chip_fm = QFontMetrics(chip_font)
        chip_w = chip_fm.horizontalAdvance(chip_text) + 16
        chip_h = 18
        from PyQt6.QtCore import QRect

        chip_rect = QRect(x + w - chip_w, y + 2, chip_w, chip_h)
        painter.setBrush(chip_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(chip_rect, 9, 9)
        painter.setPen(Qt.GlobalColor.black if self._connected else FG_MUTED)
        painter.drawText(chip_rect, Qt.AlignmentFlag.AlignCenter, chip_text)

        y += 50

        # Field rows
        self._draw_field(painter, x, y, w, "CAR", self._session.car_name or "—")
        y += 60
        self._draw_field(painter, x, y, w, "DRIVER", self._session.driver_name or "—")
        y += 60
        self._draw_field(painter, x, y, w, "TRACK", self._session.track_name or "—")
        y += 60
        if self._session.track_config:
            self._draw_field(painter, x, y, w, "CONFIG", self._session.track_config)

    def _draw_field(
        self,
        painter: QPainter,
        x: int,
        y: int,
        w: int,
        label: str,
        value: str,
    ) -> None:
        painter.setFont(FONT_LABEL_CAPS.to_qfont())
        painter.setPen(FG_MUTED)
        painter.drawText(x, y, w, 14, Qt.AlignmentFlag.AlignLeft, label)

        value_font = FONT_NUMERIC_SMALL.to_qfont()
        painter.setFont(value_font)
        painter.setPen(FG_PRIMARY)
        # Truncate to fit
        fm = QFontMetrics(value_font)
        display = fm.elidedText(value, Qt.TextElideMode.ElideRight, w)
        painter.drawText(x, y + 20, w, 32, Qt.AlignmentFlag.AlignLeft, display)
