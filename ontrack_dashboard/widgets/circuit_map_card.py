"""Circuit map -- learns the track outline as the player drives.

AC doesn't ship pre-baked track outlines. We harvest (X, Z) world
coordinates from each RTCarInfo packet, auto-scale them to fit the card
and draw the resulting polyline. The first lap teaches the shape; the
trace gets denser as more samples come in, and a lime dot marks the
current car position.

Resets the trace when the session's track changes so a Brands Hatch
session doesn't leave a polyline of Mugello on screen.
"""

from __future__ import annotations

from collections import deque

from PyQt6.QtCore import QPointF, QRect, Qt
from PyQt6.QtGui import QColor, QFontMetrics, QPainter, QPen

from ontrack_dashboard.telemetry import SessionInfo, TelemetryPacket
from ontrack_dashboard.theme import (
    ACCENT_CYAN,
    ACCENT_LIME,
    BG_SUNK,
    FG_MUTED,
    FG_PRIMARY,
    FG_SUBTLE,
    FONT_BODY_BOLD,
    FONT_LABEL_CAPS,
)
from ontrack_dashboard.widgets.card import NeumorphCard

# Keep up to ~3 laps of samples so the trace looks complete on long tracks
# without growing unbounded over the session.
_MAX_SAMPLES = 6000
# Minimum world distance between consecutive recorded samples (metres^2).
# AC streams at ~30Hz so consecutive frames at racing speed are 2-4 m
# apart; this filter keeps idle pit/garage samples from clustering.
_MIN_DELTA_SQ = 1.0
# Reset the trace if the car teleports more than this between samples
# (replay seek, "reset to pits", etc.) -- arbitrary 200 m^2 = 14 m jump.
_TELEPORT_SQ = 200.0


class CircuitMapCard(NeumorphCard):
    def __init__(self) -> None:
        super().__init__(accent=ACCENT_CYAN)
        self._samples: deque[tuple[float, float]] = deque(maxlen=_MAX_SAMPLES)
        self._current: tuple[float, float] | None = None
        self._track_name: str = ""
        self._track_config: str = ""
        self.setMinimumHeight(220)

    # --- public API --------------------------------------------------------

    def update_data(self, packet: TelemetryPacket) -> None:
        x, z = packet.car_x, packet.car_z

        # AC sends (0, 0, 0) before physics initialises -- skip those.
        if x == 0.0 and z == 0.0:
            return

        if self._samples:
            last_x, last_z = self._samples[-1]
            dsq = (x - last_x) ** 2 + (z - last_z) ** 2
            if dsq < _MIN_DELTA_SQ:
                # Same place; just update the current dot and bail.
                self._current = (x, z)
                self.update()
                return
            if dsq > _TELEPORT_SQ * 10000:
                # Massive jump (replay seek). Drop the breadcrumb so we
                # don't draw a line across the page.
                self._samples.clear()

        self._samples.append((x, z))
        self._current = (x, z)
        self.update()

    def set_session(self, session: SessionInfo) -> None:
        # Reset the trace on track change so we don't draw Mugello over Spa.
        key = (session.track_name, session.track_config)
        if (self._track_name, self._track_config) != key:
            self._samples.clear()
            self._current = None
        self._track_name = session.track_name
        self._track_config = session.track_config
        self.update()

    # --- paint -------------------------------------------------------------

    def paint_content(self, painter: QPainter) -> None:
        rect = self.content_rect()

        # Title
        title_font = FONT_BODY_BOLD.to_qfont()
        title_font.setPointSize(12)
        painter.setFont(title_font)
        painter.setPen(FG_PRIMARY)
        painter.drawText(rect.left(), rect.top(), rect.width(), 18,
                         Qt.AlignmentFlag.AlignLeft, "CIRCUIT")

        # Subtitle: track name (right aligned, elided)
        if self._track_name:
            sub = self._track_name
            if self._track_config:
                sub = f"{sub} / {self._track_config}"
        else:
            sub = "—"
        painter.setFont(FONT_LABEL_CAPS.to_qfont())
        painter.setPen(FG_MUTED)
        fm = QFontMetrics(FONT_LABEL_CAPS.to_qfont())
        elided = fm.elidedText(sub, Qt.TextElideMode.ElideRight,
                               rect.width() - 100)
        painter.drawText(rect.left() + 100, rect.top(),
                         rect.width() - 100, 18,
                         Qt.AlignmentFlag.AlignRight, elided)

        map_rect = QRect(rect.left(), rect.top() + 28,
                         rect.width(), rect.height() - 28)
        self._draw_plot(painter, map_rect)

    def _draw_plot(self, painter: QPainter, rect: QRect) -> None:
        # Plot area background
        painter.setBrush(BG_SUNK)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(rect, 10, 10)

        if len(self._samples) < 4:
            self._draw_placeholder(painter, rect)
            return

        xs = [s[0] for s in self._samples]
        zs = [s[1] for s in self._samples]
        min_x, max_x = min(xs), max(xs)
        min_z, max_z = min(zs), max(zs)
        span_x = max(1.0, max_x - min_x)
        span_z = max(1.0, max_z - min_z)

        pad = 14
        inner = rect.adjusted(pad, pad, -pad, -pad)
        scale = min(inner.width() / span_x, inner.height() / span_z)

        # Centre the trace in the inner box.
        cx = inner.center().x()
        cy = inner.center().y()
        midx = (min_x + max_x) / 2.0
        midz = (min_z + max_z) / 2.0

        def project(wx: float, wz: float) -> QPointF:
            # AC's +Z is "north"; rendering Z-as-Y has it pointing down,
            # which is the conventional bird's-eye orientation.
            return QPointF(
                cx + (wx - midx) * scale,
                cy + (wz - midz) * scale,
            )

        # Track trace
        pen = QPen(ACCENT_CYAN)
        pen.setWidth(2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        points = [project(x, z) for x, z in zip(xs, zs, strict=True)]
        for i in range(len(points) - 1):
            painter.drawLine(points[i], points[i + 1])

        # Current position dot
        if self._current is not None:
            here = project(self._current[0], self._current[1])
            glow = QColor(ACCENT_LIME)
            glow.setAlpha(80)
            painter.setBrush(glow)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(here, 12, 12)
            painter.setBrush(ACCENT_LIME)
            painter.drawEllipse(here, 6, 6)

        # Sample count footer
        painter.setFont(FONT_LABEL_CAPS.to_qfont())
        painter.setPen(FG_SUBTLE)
        painter.drawText(
            rect.adjusted(8, 0, -8, -6),
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight,
            f"{len(self._samples)} samples",
        )

    def _draw_placeholder(self, painter: QPainter, rect: QRect) -> None:
        painter.setFont(FONT_LABEL_CAPS.to_qfont())
        painter.setPen(FG_MUTED)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter,
                         "learning track…  drive a lap")
