from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QFont, QColor
from PyQt6.QtCore import Qt

class PedalWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._throttle = 0.0
        self._brake = 0.0
        self.setMinimumSize(200, 150)
        self.setStyleSheet("background-color: #1a1a1a; border-radius: 8px;")

    def update_data(self, data):
        """Update pedal values from telemetry."""
        self._throttle = data.get('thr', 0.0)
        self._brake = data.get('brk', 0.0)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        margin = 10
        bar_width = int((w - margin * 3) / 2)

        bar_height = h - 40

        x_throttle = margin
        x_brake = margin * 2 + bar_width
        y_top = 20

        throttle_fill = int(bar_height * self._throttle)
        brake_fill = int(bar_height * self._brake)

        painter.fillRect(x_throttle, y_top, bar_width, bar_height,
                         QColor(40, 40, 40))
        painter.fillRect(x_throttle, y_top + (bar_height - throttle_fill),
                         bar_width, throttle_fill, QColor(100, 200, 100))

        painter.fillRect(x_brake, y_top, bar_width, bar_height,
                         QColor(40, 40, 40))
        painter.fillRect(x_brake, y_top + (bar_height - brake_fill),
                         bar_width, brake_fill, QColor(200, 80, 80))

        font = QFont()
        font.setPointSize(10)
        painter.setFont(font)
        painter.setPen(QColor(200, 200, 200))

        painter.drawText(x_throttle, y_top + bar_height + 5, bar_width,
                         20, Qt.AlignmentFlag.AlignCenter, "T")
        painter.drawText(x_brake, y_top + bar_height + 5, bar_width,
                         20, Qt.AlignmentFlag.AlignCenter, "B")

        pct_throttle = int(self._throttle * 100)
        pct_brake = int(self._brake * 100)

        if pct_throttle > 10:
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(x_throttle, y_top + bar_height // 2 - 10, bar_width,
                             20, Qt.AlignmentFlag.AlignCenter, "{0}%".format(pct_throttle))

        if pct_brake > 10:
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(x_brake, y_top + bar_height // 2 - 10, bar_width,
                             20, Qt.AlignmentFlag.AlignCenter, "{0}%".format(pct_brake))

        painter.end()
