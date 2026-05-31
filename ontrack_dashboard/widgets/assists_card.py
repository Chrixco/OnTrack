"""ABS + TC indicator card (center bottom row).

Each assist has two states: ENABLED (the car has it) and ACTIVE (it's
intervening right now). ENABLED renders a dim pill; ACTIVE renders a
saturated pill in the assist's accent color. When both flags are false,
the pill stays in its "off" idle look.
"""

from __future__ import annotations

from PyQt6.QtCore import QRect, Qt
from PyQt6.QtGui import QColor, QPainter

from ontrack_dashboard.telemetry import TelemetryPacket
from ontrack_dashboard.theme import (
    ACCENT_AMBER,
    ACCENT_CYAN,
    BG_SUNK,
    FG_MUTED,
    FG_PRIMARY,
    FG_SUBTLE,
    FONT_BODY_BOLD,
    FONT_LABEL_CAPS,
)
from ontrack_dashboard.widgets.card import NeumorphCard


class AssistsCard(NeumorphCard):
    def __init__(self) -> None:
        super().__init__(accent=ACCENT_AMBER)
        self._abs_enabled = False
        self._abs_active = False
        self._tc_enabled = False
        self._tc_active = False
        self.setMinimumSize(180, 220)

    def update_data(self, packet: TelemetryPacket) -> None:
        self._abs_enabled = packet.abs_enabled
        self._abs_active = packet.abs_in_action
        self._tc_enabled = packet.tc_enabled
        self._tc_active = packet.tc_in_action
        self.update()

    def paint_content(self, painter: QPainter) -> None:
        rect = self.content_rect()

        # Label
        painter.setFont(FONT_LABEL_CAPS.to_qfont())
        painter.setPen(FG_MUTED)
        painter.drawText(rect.left(), rect.top(), rect.width(), 14,
                         Qt.AlignmentFlag.AlignLeft, "ASSISTS")

        body_top = rect.top() + 28
        body_h = rect.height() - 28
        pill_gap = 10
        pill_h = (body_h - pill_gap) // 2

        self._draw_pill(
            painter,
            QRect(rect.left(), body_top, rect.width(), pill_h),
            "ABS", self._abs_enabled, self._abs_active, ACCENT_CYAN,
        )
        self._draw_pill(
            painter,
            QRect(rect.left(), body_top + pill_h + pill_gap, rect.width(), pill_h),
            "TC", self._tc_enabled, self._tc_active, ACCENT_AMBER,
        )

    def _draw_pill(
        self,
        painter: QPainter,
        rect: QRect,
        label: str,
        enabled: bool,
        active: bool,
        accent: QColor,
    ) -> None:
        # Background ring
        if active:
            bg = QColor(accent)
        elif enabled:
            bg_color = QColor(accent)
            bg_color.setAlpha(70)
            bg = bg_color
        else:
            bg = BG_SUNK

        painter.setBrush(bg)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(rect, rect.height() // 2, rect.height() // 2)

        # Glow when active
        if active:
            glow = QColor(accent)
            glow.setAlpha(80)
            painter.setBrush(glow)
            painter.drawRoundedRect(rect.adjusted(-4, -4, 4, 4),
                                    rect.height() // 2 + 4,
                                    rect.height() // 2 + 4)
            # Redraw the solid pill on top of the glow
            painter.setBrush(accent)
            painter.drawRoundedRect(rect, rect.height() // 2, rect.height() // 2)

        # Label (left)
        font_label = FONT_BODY_BOLD.to_qfont()
        font_label.setPointSize(22)
        painter.setFont(font_label)
        if active:
            painter.setPen(Qt.GlobalColor.black)
        elif enabled:
            painter.setPen(FG_PRIMARY)
        else:
            painter.setPen(FG_SUBTLE)

        painter.drawText(rect.adjusted(20, 0, -10, 0),
                         Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                         label)

        # Status (right)
        font_status = FONT_LABEL_CAPS.to_qfont()
        painter.setFont(font_status)
        if active:
            status = "ACTIVE"
        elif enabled:
            status = "ON"
        else:
            status = "OFF"
        painter.drawText(rect.adjusted(10, 0, -20, 0),
                         Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
                         status)
