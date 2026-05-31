"""Center middle: huge digital speed readout with a thin progress arc."""

from __future__ import annotations

import math

from PyQt6.QtCore import QRect, Qt
from PyQt6.QtGui import QPainter, QPen

from ontrack_dashboard.telemetry import TelemetryPacket
from ontrack_dashboard.theme import (
    ACCENT_CYAN,
    BG_SUNK,
    FG_MUTED,
    FG_PRIMARY,
    FONT_DISPLAY_HUGE,
    FONT_LABEL_CAPS,
    FONT_NUMERIC,
)
from ontrack_dashboard.widgets.card import NeumorphCard

_KMH_TO_MPH = 0.621371
_MAX_KMH = 320.0


class SpeedDisplay(NeumorphCard):
    """Big speed number with a unit suffix and an arc showing % of max."""

    def __init__(self) -> None:
        super().__init__(accent=ACCENT_CYAN)
        self._speed_kmh = 0.0
        self._unit = "kmh"
        self.setMinimumHeight(260)

    def set_speed_unit(self, unit: str) -> None:
        self._unit = unit
        self.update()

    def update_data(self, packet: TelemetryPacket) -> None:
        self._speed_kmh = packet.speed_kmh
        self.update()

    def paint_content(self, painter: QPainter) -> None:
        rect = self.content_rect()

        # Label
        painter.setFont(FONT_LABEL_CAPS.to_qfont())
        painter.setPen(FG_MUTED)
        painter.drawText(rect.left(), rect.top(), rect.width(), 14,
                         Qt.AlignmentFlag.AlignLeft, "SPEED")

        display = (
            self._speed_kmh if self._unit == "kmh"
            else self._speed_kmh * _KMH_TO_MPH
        )
        unit_text = "km/h" if self._unit == "kmh" else "mph"

        # Big number
        num_rect = QRect(rect.left(), rect.top() + 22,
                         rect.width(), rect.height() - 70)
        font = FONT_DISPLAY_HUGE.to_qfont()
        font.setPointSize(min(140, max(80, num_rect.height() - 20)))
        painter.setFont(font)
        painter.setPen(ACCENT_CYAN)
        painter.drawText(num_rect, Qt.AlignmentFlag.AlignCenter,
                         f"{display:.0f}")

        # Unit
        painter.setFont(FONT_NUMERIC.to_qfont())
        painter.setPen(FG_PRIMARY)
        painter.drawText(rect.left(), rect.bottom() - 36, rect.width(), 24,
                         Qt.AlignmentFlag.AlignCenter, unit_text)

        # Bottom arc showing % of max speed
        self._draw_progress_arc(painter, rect)

    def _draw_progress_arc(self, painter: QPainter, rect: QRect) -> None:
        ratio = min(1.0, self._speed_kmh / _MAX_KMH)

        # Position the arc just below the number
        arc_w = int(rect.width() * 0.7)
        arc_h = 40
        arc_x = rect.left() + (rect.width() - arc_w) // 2
        arc_y = rect.bottom() - arc_h
        arc_rect = QRect(arc_x, arc_y, arc_w, arc_h)

        # Track
        pen = QPen(BG_SUNK)
        pen.setWidth(4)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawArc(arc_rect, 0, 180 * 16)

        # Filled portion
        pen.setColor(ACCENT_CYAN)
        painter.setPen(pen)
        # Qt arc angles: start at 3 o'clock, counter-clockwise positive.
        # We want left-to-right along the top arc, so start at 180 and
        # sweep -180*ratio.
        span = int(-180 * ratio * 16)
        painter.drawArc(arc_rect, 180 * 16, span)

        # Tick at the current point so it reads like a needle
        if ratio > 0:
            cx = arc_rect.center().x()
            cy = arc_rect.center().y()
            angle = math.pi - math.pi * ratio  # left to right
            r = arc_w // 2
            tip_x = int(cx + r * math.cos(angle))
            tip_y = int(cy - r * math.sin(angle))
            painter.setBrush(ACCENT_CYAN)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(tip_x - 6, tip_y - 6, 12, 12)
