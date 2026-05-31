"""Center top: RPM bar with shift LEDs + the gear character.

Reads RPM and gear from the telemetry packet. The LED strip lights up
left-to-right with the RPM ratio; the rightmost LEDs flash white when
above the redline threshold to mimic a real sim cockpit shift light.
"""

from __future__ import annotations

from PyQt6.QtCore import QRect, Qt
from PyQt6.QtGui import QColor, QPainter

from ontrack_dashboard.telemetry import TelemetryPacket
from ontrack_dashboard.theme import (
    ACCENT_AMBER,
    ACCENT_LIME,
    ACCENT_RED,
    BG_SUNK,
    FG_MUTED,
    FG_PRIMARY,
    FONT_DISPLAY_HUGE,
    FONT_LABEL_CAPS,
)
from ontrack_dashboard.widgets.card import NeumorphCard

_LED_COUNT = 18
_LED_REDLINE_START = 12   # index at which LEDs turn red
_LED_AMBER_START = 8      # index at which LEDs turn amber
_SHIFT_FLASH_THRESHOLD = 0.96


class ShiftIndicator(NeumorphCard):
    """RPM LED strip + big gear number."""

    def __init__(self) -> None:
        super().__init__(accent=ACCENT_LIME)
        self._rpm = 0
        self._max_rpm = 8000
        self._gear = 1
        self._flash_phase = 0
        self.setMinimumHeight(180)

    def set_max_rpm(self, max_rpm: int) -> None:
        self._max_rpm = max(1, max_rpm)
        self.update()

    def update_data(self, packet: TelemetryPacket) -> None:
        self._rpm = packet.rpm
        self._gear = packet.gear
        # Toggle flash phase so the shift light blinks while we are above
        # the threshold without needing a timer.
        self._flash_phase = (self._flash_phase + 1) % 2
        self.update()

    def paint_content(self, painter: QPainter) -> None:
        rect = self.content_rect()

        # Header row
        painter.setFont(FONT_LABEL_CAPS.to_qfont())
        painter.setPen(FG_MUTED)
        painter.drawText(rect.left(), rect.top(), rect.width(), 14,
                         Qt.AlignmentFlag.AlignLeft, "SHIFT")
        painter.drawText(rect.left(), rect.top(), rect.width(), 14,
                         Qt.AlignmentFlag.AlignRight,
                         f"{self._rpm} / {self._max_rpm} RPM")

        # Gear character + LED strip share the body row
        body_top = rect.top() + 30
        body_h = rect.height() - 30

        # Gear character on the left (takes ~40% width)
        gear_w = int(rect.width() * 0.32)
        self._draw_gear(painter, QRect(rect.left(), body_top, gear_w, body_h))

        # LED strip on the right
        led_rect = QRect(
            rect.left() + gear_w + 12,
            body_top + body_h // 2 - 24,
            rect.width() - gear_w - 12,
            48,
        )
        self._draw_leds(painter, led_rect)

    def _draw_gear(self, painter: QPainter, rect: QRect) -> None:
        label = self._gear_label()
        color = self._gear_color()

        font = FONT_DISPLAY_HUGE.to_qfont()
        # Scale down if rect is small
        font.setPointSize(min(140, max(60, rect.height())))
        painter.setFont(font)
        painter.setPen(color)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, label)

    def _gear_label(self) -> str:
        if self._gear == 0:
            return "R"
        if self._gear == 1:
            return "N"
        return str(self._gear - 1)

    def _gear_color(self) -> QColor:
        if self._gear == 0:
            return ACCENT_AMBER
        if self._gear == 1:
            return FG_MUTED
        return FG_PRIMARY

    def _draw_leds(self, painter: QPainter, rect: QRect) -> None:
        ratio = min(1.0, self._rpm / float(self._max_rpm))
        active_count = int(ratio * _LED_COUNT + 0.5)
        flashing = ratio >= _SHIFT_FLASH_THRESHOLD

        gap = 6
        led_w = (rect.width() - gap * (_LED_COUNT - 1)) // _LED_COUNT
        led_h = rect.height()

        painter.setPen(Qt.PenStyle.NoPen)

        for i in range(_LED_COUNT):
            x = rect.left() + i * (led_w + gap)
            y = rect.top()

            if i < active_count:
                if flashing and self._flash_phase == 0:
                    color = QColor(255, 255, 255)
                elif i >= _LED_REDLINE_START:
                    color = ACCENT_RED
                elif i >= _LED_AMBER_START:
                    color = ACCENT_AMBER
                else:
                    color = ACCENT_LIME
            else:
                color = BG_SUNK

            painter.setBrush(color)
            painter.drawRoundedRect(x, y, led_w, led_h, 4, 4)
