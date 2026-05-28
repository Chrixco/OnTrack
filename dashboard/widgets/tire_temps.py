from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QFont
from PyQt6.QtCore import Qt

class TireTempsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._tyre_temps = [0.0, 0.0, 0.0, 0.0]
        self.setMinimumSize(280, 200)
        self.setStyleSheet("background-color: #1a1a1a; border-radius: 8px;")

    def update_data(self, data):
        """Update tire temps from telemetry."""
        tyre = data.get('tyre', [0.0, 0.0, 0.0, 0.0])
        if len(tyre) >= 4:
            self._tyre_temps = tyre[:4]
        else:
            self._tyre_temps = list(tyre) + [0.0] * (4 - len(tyre))
        self.update()

    def temp_to_color(self, temp):
        """Convert temperature to color (blue->green->red)."""
        if temp < 60:
            return QColor.fromHsv(240, 200, 200)
        elif temp < 75:
            t = (temp - 60) / 15.0
            hue = int(240 - t * 120)
            return QColor.fromHsv(hue, 200, 200)
        elif temp < 95:
            return QColor.fromHsv(120, 200, 200)
        else:
            t = min((temp - 95) / 20.0, 1.0)
            hue = int(120 - t * 120)
            return QColor.fromHsv(hue, 220, 220)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        cell_w = 100
        cell_h = 80
        margin_x = 20
        margin_y = 20

        x_fl = margin_x
        x_fr = margin_x + cell_w + 10
        y_top = margin_y
        y_bottom = margin_y + cell_h + 10

        corners = [
            (x_fl, y_top, 0, "FL"),
            (x_fr, y_top, 1, "FR"),
            (x_fl, y_bottom, 2, "RL"),
            (x_fr, y_bottom, 3, "RR")
        ]

        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        painter.setFont(font)

        for x, y, idx, label in corners:
            if idx < len(self._tyre_temps):
                temp = self._tyre_temps[idx]
            else:
                temp = 0.0

            color = self.temp_to_color(temp)
            painter.fillRect(x, y, cell_w, cell_h, color)

            painter.setPen(QColor(30, 30, 30))
            painter.drawRect(x, y, cell_w, cell_h)

            painter.setPen(QColor(0, 0, 0))
            painter.drawText(x, y + 20, cell_w, 20,
                             Qt.AlignmentFlag.AlignCenter, label)

            font_small = QFont()
            font_small.setPointSize(14)
            font_small.setBold(True)
            painter.setFont(font_small)

            temp_text = "{0:.0f}C".format(temp)
            painter.drawText(x, y + 45, cell_w, 20,
                             Qt.AlignmentFlag.AlignCenter, temp_text)

        painter.end()
