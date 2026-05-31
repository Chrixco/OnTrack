"""Rolling time-series graph of throttle and brake inputs.

Keeps the most recent ~7 seconds of telemetry in a deque and draws two
filled curves so the driver can see overlap (trail braking, throttle
modulation, etc.). New samples slide in from the right.
"""

from __future__ import annotations

from collections import deque

from PyQt6.QtCore import QPointF, QRect, Qt
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen

from ontrack_dashboard.telemetry import TelemetryPacket
from ontrack_dashboard.theme import (
    ACCENT_LIME,
    ACCENT_RED,
    BG_SUNK,
    FG_MUTED,
    FG_PRIMARY,
    FG_SUBTLE,
    FONT_BODY_BOLD,
    FONT_LABEL_CAPS,
)
from ontrack_dashboard.widgets.card import NeumorphCard

_HISTORY = 220  # roughly 7 s at ~30 Hz


class InputGraph(NeumorphCard):
    def __init__(self) -> None:
        super().__init__(accent=ACCENT_LIME)
        self._throttle: deque[float] = deque(maxlen=_HISTORY)
        self._brake: deque[float] = deque(maxlen=_HISTORY)
        self.setMinimumHeight(180)

    def update_data(self, packet: TelemetryPacket) -> None:
        self._throttle.append(max(0.0, min(1.0, packet.throttle)))
        self._brake.append(max(0.0, min(1.0, packet.brake)))
        self.update()

    def paint_content(self, painter: QPainter) -> None:
        rect = self.content_rect()

        # Title
        title = FONT_BODY_BOLD.to_qfont()
        title.setPointSize(12)
        painter.setFont(title)
        painter.setPen(FG_PRIMARY)
        painter.drawText(rect.left(), rect.top(), rect.width(), 18,
                         Qt.AlignmentFlag.AlignLeft, "INPUT TRACE")
        painter.setFont(FONT_LABEL_CAPS.to_qfont())
        painter.setPen(FG_MUTED)
        painter.drawText(rect.left(), rect.top(), rect.width(), 18,
                         Qt.AlignmentFlag.AlignRight, "LAST 7 s")

        body = QRect(rect.left(), rect.top() + 26,
                     rect.width(), rect.height() - 30)

        # Plot area background
        painter.setBrush(BG_SUNK)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(body, 10, 10)

        # Horizontal gridlines at 0/50/100%
        pen = QPen(QColor(FG_SUBTLE))
        pen.setWidth(1)
        pen.setStyle(Qt.PenStyle.DotLine)
        painter.setPen(pen)
        for pct in (0.0, 0.5, 1.0):
            y = int(body.bottom() - pct * (body.height() - 4) - 2)
            painter.drawLine(body.left() + 6, y,
                             body.right() - 6, y)

        # Curves
        self._draw_curve(painter, body, list(self._throttle), ACCENT_LIME, 70)
        self._draw_curve(painter, body, list(self._brake), ACCENT_RED, 70)

        # Legend dots
        painter.setPen(Qt.PenStyle.NoPen)
        legend_y = rect.top() + 6
        painter.setBrush(ACCENT_LIME)
        painter.drawEllipse(rect.left() + 90, legend_y, 8, 8)
        painter.setPen(FG_MUTED)
        painter.setFont(FONT_LABEL_CAPS.to_qfont())
        painter.drawText(rect.left() + 102, rect.top(),
                         60, 18, Qt.AlignmentFlag.AlignLeft, "THR")
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(ACCENT_RED)
        painter.drawEllipse(rect.left() + 148, legend_y, 8, 8)
        painter.setPen(FG_MUTED)
        painter.drawText(rect.left() + 160, rect.top(),
                         60, 18, Qt.AlignmentFlag.AlignLeft, "BRK")

    def _draw_curve(
        self,
        painter: QPainter,
        body: QRect,
        samples: list[float],
        color: QColor,
        fill_alpha: int,
    ) -> None:
        if len(samples) < 2:
            return

        n = len(samples)
        pad_x = 8
        plot_w = body.width() - 2 * pad_x
        plot_h = body.height() - 8
        x0 = body.left() + pad_x
        y_baseline = body.bottom() - 4

        # Build the polyline; if we have fewer samples than capacity, the
        # curve aligns to the right edge as new data arrives.
        offset = (_HISTORY - n) / float(_HISTORY)
        points = []
        for i, v in enumerate(samples):
            x = x0 + (offset + i / float(_HISTORY)) * plot_w
            y = y_baseline - v * plot_h
            points.append(QPointF(x, y))

        # Filled area under the curve
        path = QPainterPath()
        path.moveTo(points[0].x(), y_baseline)
        for pt in points:
            path.lineTo(pt)
        path.lineTo(points[-1].x(), y_baseline)
        path.closeSubpath()

        fill = QColor(color)
        fill.setAlpha(fill_alpha)
        painter.setBrush(fill)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPath(path)

        # Curve stroke
        pen = QPen(color)
        pen.setWidth(2)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for i in range(len(points) - 1):
            painter.drawLine(points[i], points[i + 1])
