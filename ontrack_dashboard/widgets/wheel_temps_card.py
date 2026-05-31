"""Wheel-temperature placeholder card.

AC's RTCarInfo (the UDP packet we consume) does NOT carry tire
temperatures -- those live only in AC's Windows shared-memory interface.
This widget renders the 2x2 wheel layout so the dashboard reads
correctly, with a clear "N/A via UDP" caption. When a shared-memory
bridge is added, swap in real temperatures via update_data(packet).
"""

from __future__ import annotations

from PyQt6.QtCore import QRect, Qt
from PyQt6.QtGui import QColor, QPainter, QPen

from ontrack_dashboard.telemetry import TelemetryPacket
from ontrack_dashboard.theme import (
    ACCENT_PURPLE,
    BG_SUNK,
    FG_MUTED,
    FG_PRIMARY,
    FG_SUBTLE,
    FONT_BODY_BOLD,
    FONT_LABEL_CAPS,
    FONT_NUMERIC,
    FONT_NUMERIC_SMALL,
)
from ontrack_dashboard.widgets.card import NeumorphCard


class WheelTempsCard(NeumorphCard):
    """2x2 grid of FL/FR/RL/RR corners with temperatures."""

    def __init__(self) -> None:
        super().__init__(accent=ACCENT_PURPLE)
        self._temps = (0.0, 0.0, 0.0, 0.0)
        self._available = False
        self.setMinimumHeight(220)

    def update_data(self, packet: TelemetryPacket) -> None:
        self._temps = packet.tyre_temps_c
        self._available = any(t > 0.001 for t in self._temps)
        self.update()

    def paint_content(self, painter: QPainter) -> None:
        rect = self.content_rect()

        # Header
        title = FONT_BODY_BOLD.to_qfont()
        title.setPointSize(12)
        painter.setFont(title)
        painter.setPen(FG_PRIMARY)
        painter.drawText(rect.left(), rect.top(), rect.width(), 18,
                         Qt.AlignmentFlag.AlignLeft, "TYRE TEMPS")

        painter.setFont(FONT_LABEL_CAPS.to_qfont())
        painter.setPen(FG_MUTED)
        status = "LIVE" if self._available else "N/A via UDP"
        painter.drawText(rect.left(), rect.top(), rect.width(), 18,
                         Qt.AlignmentFlag.AlignRight, status)

        body = QRect(rect.left(), rect.top() + 26,
                     rect.width(), rect.height() - 26)

        cell_gap = 12
        cell_w = (body.width() - cell_gap) // 2
        cell_h = (body.height() - cell_gap) // 2

        positions = [
            (body.left(),                       body.top(),                       "FL", 0),
            (body.left() + cell_w + cell_gap,   body.top(),                       "FR", 1),
            (body.left(),                       body.top() + cell_h + cell_gap,   "RL", 2),
            (body.left() + cell_w + cell_gap,   body.top() + cell_h + cell_gap,   "RR", 3),
        ]

        for x, y, label, idx in positions:
            self._draw_cell(painter, QRect(x, y, cell_w, cell_h), label, self._temps[idx])

    def _draw_cell(
        self, painter: QPainter, rect: QRect, label: str, temp: float
    ) -> None:
        # Background
        painter.setBrush(BG_SUNK)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(rect, 12, 12)

        # Temperature gradient if data available; otherwise dashed border
        if self._available:
            color = _temp_to_color(temp)
            painter.setBrush(color)
            painter.drawRoundedRect(rect, 12, 12)
            value_color = QColor(255, 255, 255, 230)
            label_color = QColor(255, 255, 255, 200)
            value_text = f"{temp:.0f}°"
        else:
            pen = QPen(FG_SUBTLE)
            pen.setStyle(Qt.PenStyle.DashLine)
            pen.setWidth(1)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(rect.adjusted(2, 2, -2, -2), 10, 10)
            value_color = FG_SUBTLE
            label_color = FG_MUTED
            value_text = "—"

        # Corner label (top-left)
        painter.setFont(FONT_LABEL_CAPS.to_qfont())
        painter.setPen(label_color)
        painter.drawText(rect.adjusted(10, 8, -10, -10),
                         Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft,
                         label)

        # Big temperature reading
        font = FONT_NUMERIC.to_qfont()
        font.setPointSize(24)
        painter.setFont(font)
        painter.setPen(value_color)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, value_text)

        # Footnote when N/A
        if not self._available:
            painter.setFont(FONT_NUMERIC_SMALL.to_qfont())
            painter.setPen(FG_MUTED)
            painter.drawText(
                rect.adjusted(0, 0, 0, -8),
                Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
                "shared mem",
            )


def _temp_to_color(temp_c: float) -> QColor:
    """Blue → green → red gradient. Optimal window: 75–95 °C."""
    if temp_c <= 0:
        return QColor(70, 80, 100)
    if temp_c < 60:
        return QColor.fromHsv(220, 180, 180)
    if temp_c < 75:
        f = (temp_c - 60) / 15.0
        return QColor.fromHsv(int(220 - f * 100), 200, 200)
    if temp_c <= 95:
        return QColor.fromHsv(120, 200, 200)
    if temp_c < 110:
        f = (temp_c - 95) / 15.0
        return QColor.fromHsv(int(120 - f * 120), 220, 220)
    return QColor.fromHsv(0, 240, 220)
