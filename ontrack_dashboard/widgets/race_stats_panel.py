"""Right panel: lap counter + current / best / last lap times with delta."""

from __future__ import annotations

from PyQt6.QtCore import QRect, Qt
from PyQt6.QtGui import QPainter

from ontrack_dashboard.telemetry import TelemetryPacket
from ontrack_dashboard.theme import (
    ACCENT_AMBER,
    ACCENT_CYAN,
    ACCENT_LIME,
    ACCENT_RED,
    FG_MUTED,
    FG_PRIMARY,
    FG_SUBTLE,
    FONT_BODY_BOLD,
    FONT_DISPLAY_LARGE,
    FONT_LABEL_CAPS,
    FONT_NUMERIC,
)
from ontrack_dashboard.widgets.card import NeumorphCard


def _format_ms(ms: int) -> str:
    if ms <= 0:
        return "—:——.———"
    s = ms / 1000.0
    mins = int(s) // 60
    secs = s - mins * 60
    return f"{mins:d}:{secs:06.3f}"


class RaceStatsPanel(NeumorphCard):
    """Stack of: LAP counter (big), CURRENT, BEST, LAST, DELTA-vs-best."""

    def __init__(self) -> None:
        super().__init__(accent=ACCENT_AMBER)
        self._lap = 0
        self._current_ms = 0
        self._best_ms = 0
        self._last_ms = 0
        self.setMinimumWidth(280)

    def update_data(self, packet: TelemetryPacket) -> None:
        self._lap = packet.lap
        self._current_ms = packet.lap_time_ms
        self._best_ms = packet.best_lap_ms
        self._last_ms = packet.last_lap_ms
        self.update()

    def paint_content(self, painter: QPainter) -> None:
        rect = self.content_rect()
        x = rect.left()
        y = rect.top()
        w = rect.width()

        # Title row
        title_font = FONT_BODY_BOLD.to_qfont()
        title_font.setPointSize(14)
        painter.setFont(title_font)
        painter.setPen(FG_PRIMARY)
        painter.drawText(x, y, w, 22, Qt.AlignmentFlag.AlignLeft, "RACE STATS")

        # Lap counter (large number, label)
        y += 36
        lap_label_h = 14
        painter.setFont(FONT_LABEL_CAPS.to_qfont())
        painter.setPen(FG_MUTED)
        painter.drawText(x, y, w, lap_label_h,
                         Qt.AlignmentFlag.AlignLeft, "LAP")

        font_lap = FONT_DISPLAY_LARGE.to_qfont()
        font_lap.setPointSize(54)
        painter.setFont(font_lap)
        painter.setPen(ACCENT_CYAN)
        painter.drawText(QRect(x, y + 4, w, 70),
                         Qt.AlignmentFlag.AlignLeft, str(self._lap))

        # Separator
        y += 86
        painter.setPen(FG_SUBTLE)
        painter.drawLine(x, y, x + w, y)

        # Time rows
        y += 16
        row_h = 50

        self._draw_time_row(painter, x, y, w, "CURRENT",
                            _format_ms(self._current_ms), FG_PRIMARY)
        y += row_h
        self._draw_time_row(painter, x, y, w, "BEST",
                            _format_ms(self._best_ms), ACCENT_AMBER)
        y += row_h
        self._draw_time_row(painter, x, y, w, "LAST",
                            _format_ms(self._last_ms), FG_PRIMARY)
        y += row_h

        # Delta vs best
        y += 8
        painter.setPen(FG_SUBTLE)
        painter.drawLine(x, y, x + w, y)
        y += 14

        if self._last_ms > 0 and self._best_ms > 0:
            delta_ms = self._last_ms - self._best_ms
            color = ACCENT_LIME if delta_ms < 0 else ACCENT_RED
            sign = "" if delta_ms < 0 else "+"
            delta_text = f"{sign}{delta_ms / 1000.0:.3f}"
        else:
            color = FG_SUBTLE
            delta_text = "—"

        painter.setFont(FONT_LABEL_CAPS.to_qfont())
        painter.setPen(FG_MUTED)
        painter.drawText(x, y, w, 14,
                         Qt.AlignmentFlag.AlignLeft, "DELTA vs BEST")

        font_delta = FONT_DISPLAY_LARGE.to_qfont()
        font_delta.setPointSize(34)
        painter.setFont(font_delta)
        painter.setPen(color)
        painter.drawText(QRect(x, y + 18, w, 50),
                         Qt.AlignmentFlag.AlignLeft, delta_text)

    def _draw_time_row(
        self, painter: QPainter, x: int, y: int, w: int,
        label: str, value: str, value_color,
    ) -> None:
        painter.setFont(FONT_LABEL_CAPS.to_qfont())
        painter.setPen(FG_MUTED)
        painter.drawText(x, y, w, 14, Qt.AlignmentFlag.AlignLeft, label)

        painter.setFont(FONT_NUMERIC.to_qfont())
        painter.setPen(value_color)
        painter.drawText(x, y + 14, w, 28,
                         Qt.AlignmentFlag.AlignLeft, value)
