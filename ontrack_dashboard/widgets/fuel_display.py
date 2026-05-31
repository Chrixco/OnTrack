"""Center bottom-right: fuel level.

AC's RTCarInfo does not carry fuel -- the field is reserved for a future
shared-memory bridge. Until that lands the widget renders the placeholder
"N/A via UDP" so the layout still reads correctly.
"""

from __future__ import annotations

from PyQt6.QtCore import QRect, Qt
from PyQt6.QtGui import QColor, QLinearGradient, QPainter

from ontrack_dashboard.telemetry import TelemetryPacket
from ontrack_dashboard.theme import (
    ACCENT_AMBER,
    ACCENT_LIME,
    ACCENT_RED,
    BG_SUNK,
    FG_MUTED,
    FG_PRIMARY,
    FG_SUBTLE,
    FONT_DISPLAY_MEDIUM,
    FONT_LABEL_CAPS,
)
from ontrack_dashboard.widgets.card import NeumorphCard

_TANK_CAPACITY_L = 80.0  # used only to scale the bar visually


class FuelDisplay(NeumorphCard):
    def __init__(self) -> None:
        super().__init__(accent=ACCENT_AMBER)
        self._fuel_l = 0.0
        self._available = False
        self.setMinimumSize(220, 220)

    def update_data(self, packet: TelemetryPacket) -> None:
        self._fuel_l = packet.fuel
        self._available = packet.fuel > 0.001
        self.update()

    def paint_content(self, painter: QPainter) -> None:
        rect = self.content_rect()

        # Label
        painter.setFont(FONT_LABEL_CAPS.to_qfont())
        painter.setPen(FG_MUTED)
        painter.drawText(rect.left(), rect.top(), rect.width(), 14,
                         Qt.AlignmentFlag.AlignLeft, "FUEL")

        if not self._available:
            painter.drawText(rect.left(), rect.top(), rect.width(), 14,
                             Qt.AlignmentFlag.AlignRight, "N/A via UDP")

        body_top = rect.top() + 30
        body_h = rect.height() - 30

        # Big numeric value (or dash)
        num_rect = QRect(rect.left(), body_top, rect.width(), body_h // 2)
        font = FONT_DISPLAY_MEDIUM.to_qfont()
        font.setPointSize(min(48, max(28, num_rect.height() - 20)))
        painter.setFont(font)
        painter.setPen(ACCENT_AMBER if self._available else FG_SUBTLE)
        value_text = f"{self._fuel_l:.1f}" if self._available else "—"
        painter.drawText(num_rect, Qt.AlignmentFlag.AlignCenter, value_text)

        # Liters caption
        painter.setFont(FONT_LABEL_CAPS.to_qfont())
        painter.setPen(FG_MUTED)
        painter.drawText(num_rect.left(),
                         num_rect.bottom() - 6,
                         num_rect.width(), 14,
                         Qt.AlignmentFlag.AlignCenter, "LITERS")

        # Horizontal bar
        bar_w = int(rect.width() * 0.85)
        bar_h = 14
        bar_x = rect.left() + (rect.width() - bar_w) // 2
        bar_y = rect.bottom() - bar_h - 6
        bar_rect = QRect(bar_x, bar_y, bar_w, bar_h)

        # Track
        painter.setBrush(BG_SUNK)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(bar_rect, 7, 7)

        # Fill
        if self._available:
            ratio = min(1.0, self._fuel_l / _TANK_CAPACITY_L)
            fill_w = int(bar_w * ratio)
            if fill_w > 0:
                fill_rect = QRect(bar_x, bar_y, fill_w, bar_h)
                gradient = QLinearGradient(bar_x, 0, bar_x + bar_w, 0)
                if ratio < 0.15:
                    gradient.setColorAt(0.0, ACCENT_RED)
                    gradient.setColorAt(1.0, ACCENT_AMBER)
                elif ratio < 0.35:
                    gradient.setColorAt(0.0, ACCENT_AMBER)
                    gradient.setColorAt(1.0, ACCENT_LIME)
                else:
                    gradient.setColorAt(0.0, ACCENT_LIME)
                    gradient.setColorAt(1.0, QColor(ACCENT_LIME).darker(120))
                painter.setBrush(gradient)
                painter.drawRoundedRect(fill_rect, 7, 7)
        else:
            # Subtle stripe so the slot doesn't feel dead.
            for i in range(0, bar_w, 16):
                stripe = QRect(bar_x + i, bar_y, 6, bar_h)
                painter.setBrush(QColor(FG_SUBTLE).darker(140))
                painter.drawRoundedRect(stripe, 3, 3)

        # Bar foreground text
        painter.setFont(FONT_LABEL_CAPS.to_qfont())
        painter.setPen(FG_PRIMARY if self._available else FG_SUBTLE)
        cap_text = f"0 / {int(_TANK_CAPACITY_L)} L"
        painter.drawText(bar_x, bar_y - 18, bar_w, 14,
                         Qt.AlignmentFlag.AlignLeft, "EMPTY")
        painter.drawText(bar_x, bar_y - 18, bar_w, 14,
                         Qt.AlignmentFlag.AlignRight, cap_text)
