"""Throttle + brake input bars (left panel)."""

from __future__ import annotations

from PyQt6.QtCore import QRect, Qt
from PyQt6.QtGui import QColor, QLinearGradient, QPainter

from ontrack_dashboard.telemetry import TelemetryPacket
from ontrack_dashboard.theme import (
    ACCENT_LIME,
    ACCENT_RED,
    BG_SUNK,
    FG_MUTED,
    FG_PRIMARY,
    FONT_BODY_BOLD,
    FONT_LABEL_CAPS,
)
from ontrack_dashboard.widgets.card import NeumorphCard


class PedalsCard(NeumorphCard):
    """Two vertical bars side-by-side: throttle (lime) + brake (red)."""

    def __init__(self) -> None:
        super().__init__(accent=ACCENT_LIME)
        self._throttle = 0.0
        self._brake = 0.0
        self.setMinimumHeight(150)

    def update_data(self, packet: TelemetryPacket) -> None:
        self._throttle = max(0.0, min(1.0, packet.throttle))
        self._brake = max(0.0, min(1.0, packet.brake))
        self.update()

    def paint_content(self, painter: QPainter) -> None:
        rect = self.content_rect()

        # Title
        title_font = FONT_BODY_BOLD.to_qfont()
        title_font.setPointSize(12)
        painter.setFont(title_font)
        painter.setPen(FG_PRIMARY)
        painter.drawText(rect.left(), rect.top(), rect.width(), 18,
                         Qt.AlignmentFlag.AlignLeft, "INPUTS")

        body_top = rect.top() + 26
        body_h = rect.height() - 26

        bar_w = (rect.width() - 18) // 2
        bar_x_t = rect.left()
        bar_x_b = rect.left() + bar_w + 18
        bar_top = body_top
        bar_h = body_h - 22

        self._draw_bar(painter, bar_x_t, bar_top, bar_w, bar_h,
                       self._throttle, ACCENT_LIME, "THR")
        self._draw_bar(painter, bar_x_b, bar_top, bar_w, bar_h,
                       self._brake, ACCENT_RED, "BRK")

    def _draw_bar(
        self,
        painter: QPainter,
        x: int, y: int, w: int, h: int,
        value: float, color: QColor, label: str,
    ) -> None:
        # Track
        painter.setBrush(BG_SUNK)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(x, y, w, h, 8, 8)

        # Fill (bottom-up)
        fill_h = int(h * value)
        if fill_h > 0:
            gradient = QLinearGradient(0, y + h - fill_h, 0, y + h)
            top = QColor(color).lighter(110)
            bottom = QColor(color).darker(125)
            gradient.setColorAt(0.0, top)
            gradient.setColorAt(1.0, bottom)
            painter.setBrush(gradient)
            painter.drawRoundedRect(x, y + h - fill_h, w, fill_h, 8, 8)

        # Percentage in the bar (when > 5% so it doesn't clip)
        pct = int(value * 100)
        if pct > 5:
            font = FONT_BODY_BOLD.to_qfont()
            font.setPointSize(14)
            painter.setFont(font)
            painter.setPen(QColor(0, 0, 0, 220))
            painter.drawText(
                QRect(x, y + h - fill_h - 2, w, 22),
                Qt.AlignmentFlag.AlignCenter, f"{pct}%",
            )

        # Label beneath
        painter.setFont(FONT_LABEL_CAPS.to_qfont())
        painter.setPen(FG_MUTED)
        painter.drawText(
            QRect(x, y + h + 4, w, 16),
            Qt.AlignmentFlag.AlignCenter, label,
        )
