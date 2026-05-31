"""Center bottom-left: G-force ball.

A circular field with a dot showing the live lateral (g_lat) and
longitudinal (g_long) acceleration vector. A thin compass-style ring is
labelled at the cardinal directions; the dot trails over the past few
frames for a sense of motion.
"""

from __future__ import annotations

import math
from collections import deque

from PyQt6.QtCore import QRect, Qt
from PyQt6.QtGui import QColor, QPainter, QPen

from ontrack_dashboard.telemetry import TelemetryPacket
from ontrack_dashboard.theme import (
    ACCENT_MAGENTA,
    BG_SUNK,
    FG_MUTED,
    FG_PRIMARY,
    FG_SUBTLE,
    FONT_LABEL_CAPS,
    FONT_NUMERIC_SMALL,
)
from ontrack_dashboard.widgets.card import NeumorphCard

_G_SCALE = 2.0  # +/- this many G fills the dial
_TRAIL_LEN = 14


class AccelerationDisplay(NeumorphCard):
    def __init__(self) -> None:
        super().__init__(accent=ACCENT_MAGENTA)
        self._g_lat = 0.0
        self._g_long = 0.0
        self._trail: deque[tuple[float, float]] = deque(maxlen=_TRAIL_LEN)
        self.setMinimumSize(220, 220)

    def update_data(self, packet: TelemetryPacket) -> None:
        self._g_lat = packet.g_lat
        self._g_long = packet.g_long
        self._trail.append((self._g_lat, self._g_long))
        self.update()

    def paint_content(self, painter: QPainter) -> None:
        rect = self.content_rect()

        # Label
        painter.setFont(FONT_LABEL_CAPS.to_qfont())
        painter.setPen(FG_MUTED)
        painter.drawText(rect.left(), rect.top(), rect.width(), 14,
                         Qt.AlignmentFlag.AlignLeft, "G-FORCE")

        magnitude = math.sqrt(self._g_lat ** 2 + self._g_long ** 2)
        painter.drawText(rect.left(), rect.top(), rect.width(), 14,
                         Qt.AlignmentFlag.AlignRight, f"{magnitude:.2f} G")

        body = QRect(rect.left(), rect.top() + 22,
                     rect.width(), rect.height() - 22)
        self._draw_dial(painter, body)

    def _draw_dial(self, painter: QPainter, rect: QRect) -> None:
        side = min(rect.width(), rect.height()) - 12
        cx = rect.center().x()
        cy = rect.center().y()
        radius = side // 2

        # Outer ring
        pen = QPen(BG_SUNK)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(cx - radius, cy - radius, side, side)

        # Inner rings
        pen.setColor(QColor(FG_SUBTLE))
        pen.setWidth(1)
        painter.setPen(pen)
        for f in (0.33, 0.66):
            r = int(radius * f)
            painter.drawEllipse(cx - r, cy - r, r * 2, r * 2)

        # Crosshair
        painter.drawLine(cx - radius, cy, cx + radius, cy)
        painter.drawLine(cx, cy - radius, cx, cy + radius)

        # Direction labels
        painter.setFont(FONT_LABEL_CAPS.to_qfont())
        painter.setPen(FG_SUBTLE)
        painter.drawText(cx - 10, cy - radius - 4, 20, 12,
                         Qt.AlignmentFlag.AlignCenter, "ACC")
        painter.drawText(cx - 14, cy + radius - 6, 28, 12,
                         Qt.AlignmentFlag.AlignCenter, "BRK")
        painter.drawText(cx + radius - 18, cy - 6, 16, 12,
                         Qt.AlignmentFlag.AlignCenter, "R")
        painter.drawText(cx - radius + 4, cy - 6, 16, 12,
                         Qt.AlignmentFlag.AlignCenter, "L")

        # Trail dots (older = more transparent)
        painter.setPen(Qt.PenStyle.NoPen)
        for i, (lat, lng) in enumerate(self._trail):
            alpha = int(180 * (i + 1) / len(self._trail))
            col = QColor(ACCENT_MAGENTA)
            col.setAlpha(alpha)
            painter.setBrush(col)
            x, y = self._project(lat, lng, cx, cy, radius)
            painter.drawEllipse(x - 3, y - 3, 6, 6)

        # Active dot
        x, y = self._project(self._g_lat, self._g_long, cx, cy, radius)
        painter.setBrush(FG_PRIMARY)
        painter.drawEllipse(x - 7, y - 7, 14, 14)

        # Live components
        painter.setFont(FONT_NUMERIC_SMALL.to_qfont())
        painter.setPen(FG_MUTED)
        painter.drawText(rect.left(), rect.bottom() - 18, rect.width(), 16,
                         Qt.AlignmentFlag.AlignCenter,
                         f"lat {self._g_lat:+.2f}   long {self._g_long:+.2f}")

    def _project(
        self, g_lat: float, g_long: float, cx: int, cy: int, radius: int
    ) -> tuple[int, int]:
        nx = max(-1.0, min(1.0, g_lat / _G_SCALE))
        ny = max(-1.0, min(1.0, g_long / _G_SCALE))
        # Convention: positive lateral = right, positive longitudinal =
        # forward acceleration (so we render upward). Brake = negative
        # long, downward.
        return cx + int(nx * radius), cy - int(ny * radius)
