"""Neumorphic dark theme.

Single source of truth for colors, typography, and spacing across the
dashboard. The look is dark neumorphism: a flat dark canvas, cards that
appear gently raised via a dark drop-shadow bottom-right and a soft
highlight top-left, electric-cyan accents for live values, warmer accents
(amber/red) for warning thresholds.
"""

from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtGui import QColor, QFont, QPalette

# --- Palette --------------------------------------------------------------

# Backgrounds (darkest -> lightest)
BG_BASE = QColor(20, 22, 28)        # window background
BG_SUNK = QColor(16, 18, 23)        # bottom-right "shadow" component
BG_CARD = QColor(28, 32, 40)        # card surface
BG_RAISE = QColor(38, 44, 54)       # raised inner element / highlight catch

# Foregrounds
FG_PRIMARY = QColor(220, 226, 236)
FG_MUTED = QColor(140, 148, 160)
FG_SUBTLE = QColor(90, 98, 110)

# Accents
ACCENT_CYAN = QColor(80, 220, 220)
ACCENT_TEAL = QColor(56, 178, 172)
ACCENT_LIME = QColor(132, 224, 132)
ACCENT_AMBER = QColor(255, 184, 76)
ACCENT_RED = QColor(255, 90, 90)
ACCENT_MAGENTA = QColor(220, 100, 200)
ACCENT_PURPLE = QColor(180, 140, 240)

# Shadow colors used by NeumorphCard
SHADOW_DARK = QColor(0, 0, 0, 140)
SHADOW_LIGHT = QColor(255, 255, 255, 18)


# --- Spacing / radii ------------------------------------------------------

CARD_RADIUS = 18
CARD_PADDING = 18
CARD_SHADOW_BLUR = 22
CARD_SHADOW_OFFSET = 6

GUTTER = 14


# --- Typography -----------------------------------------------------------


@dataclass(frozen=True)
class FontSpec:
    family: str = "Segoe UI"
    size: int = 11
    weight: int = QFont.Weight.Normal.value
    letter_spacing: float = 0.0

    def to_qfont(self) -> QFont:
        f = QFont(self.family, self.size, self.weight)
        if self.letter_spacing:
            f.setLetterSpacing(QFont.SpacingType.PercentageSpacing, self.letter_spacing)
        return f


# Display = huge numeric readouts (speed, gear)
FONT_DISPLAY_HUGE = FontSpec(size=130, weight=QFont.Weight.Black.value)
FONT_DISPLAY_LARGE = FontSpec(size=72, weight=QFont.Weight.Black.value)
FONT_DISPLAY_MEDIUM = FontSpec(size=44, weight=QFont.Weight.DemiBold.value)

# Numeric readouts (lap times, speeds smaller)
FONT_NUMERIC = FontSpec(size=20, weight=QFont.Weight.DemiBold.value)
FONT_NUMERIC_SMALL = FontSpec(size=14, weight=QFont.Weight.Medium.value)

# Labels
FONT_LABEL_CAPS = FontSpec(size=9, weight=QFont.Weight.Bold.value, letter_spacing=200.0)
FONT_LABEL = FontSpec(size=10, weight=QFont.Weight.Medium.value)
FONT_BODY = FontSpec(size=11, weight=QFont.Weight.Normal.value)
FONT_BODY_BOLD = FontSpec(size=11, weight=QFont.Weight.DemiBold.value)


# --- QPalette -------------------------------------------------------------


def build_app_palette() -> QPalette:
    p = QPalette()
    p.setColor(QPalette.ColorRole.Window, BG_BASE)
    p.setColor(QPalette.ColorRole.WindowText, FG_PRIMARY)
    p.setColor(QPalette.ColorRole.Base, BG_CARD)
    p.setColor(QPalette.ColorRole.AlternateBase, BG_RAISE)
    p.setColor(QPalette.ColorRole.ToolTipBase, BG_CARD)
    p.setColor(QPalette.ColorRole.ToolTipText, FG_PRIMARY)
    p.setColor(QPalette.ColorRole.Text, FG_PRIMARY)
    p.setColor(QPalette.ColorRole.Button, BG_RAISE)
    p.setColor(QPalette.ColorRole.ButtonText, FG_PRIMARY)
    p.setColor(QPalette.ColorRole.BrightText, ACCENT_CYAN)
    p.setColor(QPalette.ColorRole.Link, ACCENT_CYAN)
    p.setColor(QPalette.ColorRole.Highlight, ACCENT_TEAL)
    p.setColor(QPalette.ColorRole.HighlightedText, BG_BASE)
    return p


# --- Style sheet for menus / dialogs that aren't custom-painted ---------

GLOBAL_QSS = f"""
QMainWindow {{
    background: rgb({BG_BASE.red()}, {BG_BASE.green()}, {BG_BASE.blue()});
}}
QMenuBar {{
    background: transparent;
    color: rgb({FG_MUTED.red()}, {FG_MUTED.green()}, {FG_MUTED.blue()});
    padding: 4px 8px;
}}
QMenuBar::item:selected {{
    background: rgb({BG_RAISE.red()}, {BG_RAISE.green()}, {BG_RAISE.blue()});
    border-radius: 6px;
}}
QMenu {{
    background: rgb({BG_CARD.red()}, {BG_CARD.green()}, {BG_CARD.blue()});
    color: rgb({FG_PRIMARY.red()}, {FG_PRIMARY.green()}, {FG_PRIMARY.blue()});
    border: 1px solid rgba(255,255,255,12);
    border-radius: 10px;
    padding: 6px;
}}
QMenu::item {{
    padding: 6px 18px 6px 18px;
    border-radius: 6px;
}}
QMenu::item:selected {{
    background: rgba(80,220,220,40);
    color: rgb({ACCENT_CYAN.red()}, {ACCENT_CYAN.green()}, {ACCENT_CYAN.blue()});
}}
QDialog {{
    background: rgb({BG_BASE.red()}, {BG_BASE.green()}, {BG_BASE.blue()});
    color: rgb({FG_PRIMARY.red()}, {FG_PRIMARY.green()}, {FG_PRIMARY.blue()});
}}
QLineEdit, QSpinBox, QComboBox {{
    background: rgb({BG_CARD.red()}, {BG_CARD.green()}, {BG_CARD.blue()});
    color: rgb({FG_PRIMARY.red()}, {FG_PRIMARY.green()}, {FG_PRIMARY.blue()});
    border: 1px solid rgba(255,255,255,18);
    border-radius: 8px;
    padding: 6px 10px;
}}
QCheckBox {{
    color: rgb({FG_PRIMARY.red()}, {FG_PRIMARY.green()}, {FG_PRIMARY.blue()});
    spacing: 8px;
}}
QPushButton {{
    background: rgb({BG_RAISE.red()}, {BG_RAISE.green()}, {BG_RAISE.blue()});
    color: rgb({FG_PRIMARY.red()}, {FG_PRIMARY.green()}, {FG_PRIMARY.blue()});
    border: 1px solid rgba(255,255,255,20);
    border-radius: 10px;
    padding: 8px 22px;
    font-weight: 600;
}}
QPushButton:hover {{
    border: 1px solid rgb({ACCENT_CYAN.red()}, {ACCENT_CYAN.green()}, {ACCENT_CYAN.blue()});
    color: rgb({ACCENT_CYAN.red()}, {ACCENT_CYAN.green()}, {ACCENT_CYAN.blue()});
}}
QLabel {{
    color: rgb({FG_PRIMARY.red()}, {FG_PRIMARY.green()}, {FG_PRIMARY.blue()});
    background: transparent;
}}
"""
