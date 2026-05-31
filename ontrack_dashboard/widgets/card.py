"""Neumorphic card -- the visual chassis for every widget in the dashboard.

Paints a soft-extruded card: a rounded rectangle the same color as the
window with a dark drop-shadow at bottom-right and a soft highlight at
top-left, so each card looks gently lifted off the canvas.
"""

from __future__ import annotations

from PyQt6.QtCore import QRect, Qt
from PyQt6.QtGui import QColor, QLinearGradient, QPainter
from PyQt6.QtWidgets import QWidget

from ontrack_dashboard.theme import (
    BG_CARD,
    CARD_PADDING,
    CARD_RADIUS,
    CARD_SHADOW_BLUR,
    CARD_SHADOW_OFFSET,
    SHADOW_DARK,
    SHADOW_LIGHT,
)


class NeumorphCard(QWidget):
    """Base class for widgets that should look like a soft raised card.

    Subclasses paint their content inside `content_rect()` -- the area
    inside padding and shadow margins. Override `paint_content(painter)`
    to draw on top of the card; the base class handles the chassis.
    """

    def __init__(self, *, accent: QColor | None = None) -> None:
        super().__init__()
        self._accent = accent
        # Make sure background painting from styleSheet doesn't fight us.
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

    # --- public hooks for subclasses --------------------------------------

    def content_rect(self) -> QRect:
        """The drawable area inside padding + shadow allowance."""
        m = CARD_SHADOW_BLUR
        return self.rect().adjusted(
            m + CARD_PADDING,
            m + CARD_PADDING,
            -m - CARD_PADDING,
            -m - CARD_PADDING,
        )

    def card_rect(self) -> QRect:
        """The card chassis rect (no padding)."""
        m = CARD_SHADOW_BLUR
        return self.rect().adjusted(m, m, -m, -m)

    def paint_content(self, painter: QPainter) -> None:
        """Override in subclasses to paint inside the card."""

    # --- chassis paint ----------------------------------------------------

    def paintEvent(self, event) -> None:  # noqa: N802 (Qt API)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        chassis = self.card_rect()
        if chassis.width() <= 0 or chassis.height() <= 0:
            painter.end()
            return

        # Dark drop shadow (bottom-right). Stack a few rounded rects with
        # decreasing alpha to fake a Gaussian blur cheaply.
        for i in range(CARD_SHADOW_BLUR):
            alpha = int(SHADOW_DARK.alpha() * (1 - i / CARD_SHADOW_BLUR) ** 2)
            color = QColor(SHADOW_DARK)
            color.setAlpha(alpha)
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            off = CARD_SHADOW_OFFSET + i
            painter.drawRoundedRect(
                chassis.adjusted(off, off, off, off),
                CARD_RADIUS,
                CARD_RADIUS,
            )

        # Light highlight (top-left). Same technique, lower alpha.
        for i in range(CARD_SHADOW_BLUR):
            alpha = int(SHADOW_LIGHT.alpha() * (1 - i / CARD_SHADOW_BLUR) ** 2)
            color = QColor(SHADOW_LIGHT)
            color.setAlpha(alpha)
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            off = -(CARD_SHADOW_OFFSET + i)
            painter.drawRoundedRect(
                chassis.adjusted(off, off, off, off),
                CARD_RADIUS,
                CARD_RADIUS,
            )

        # Card surface itself. A subtle vertical gradient gives a hint of
        # depth without breaking the flat look.
        gradient = QLinearGradient(0, chassis.top(), 0, chassis.bottom())
        top = QColor(BG_CARD).lighter(108)
        bottom = QColor(BG_CARD).darker(108)
        gradient.setColorAt(0.0, top)
        gradient.setColorAt(1.0, bottom)
        painter.setBrush(gradient)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(chassis, CARD_RADIUS, CARD_RADIUS)

        # Optional accent stripe along the left edge.
        if self._accent is not None:
            accent = QColor(self._accent)
            stripe_w = 4
            stripe = QRect(
                chassis.left() + 6,
                chassis.top() + 18,
                stripe_w,
                chassis.height() - 36,
            )
            painter.setBrush(accent)
            painter.drawRoundedRect(stripe, 2, 2)

        # Let subclasses paint on top.
        self.paint_content(painter)

        painter.end()
