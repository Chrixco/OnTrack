from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QFont, QColor
from PyQt6.QtCore import Qt

class GearDisplay(QWidget):
    def __init__(self):
        super().__init__()
        self._gear = 0
        self.setMinimumSize(120, 120)
        self.setStyleSheet("background-color: #1a1a1a; border-radius: 8px;")

    def update_data(self, data):
        """Update gear from telemetry dict."""
        self._gear = data.get('gear', 0)
        self.update()

    def gear_label(self):
        """Convert gear number to display label."""
        if self._gear == 0:
            return "R"
        elif self._gear == 1:
            return "N"
        else:
            return str(self._gear - 1)

    def gear_color(self):
        """Return color based on gear."""
        if self._gear == 0:
            return QColor(200, 50, 50)
        elif self._gear == 1:
            return QColor(128, 128, 128)
        else:
            return QColor(255, 255, 255)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        font = QFont()
        font.setPointSize(48)
        font.setBold(True)
        painter.setFont(font)

        color = self.gear_color()
        painter.setPen(color)

        label = self.gear_label()
        painter.drawText(0, 0, w, h, Qt.AlignmentFlag.AlignCenter, label)

        painter.end()
