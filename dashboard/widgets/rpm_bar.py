from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QLinearGradient, QFont
from PyQt6.QtCore import Qt

class RPMBar(QWidget):
    def __init__(self):
        super().__init__()
        self._rpm = 0
        self._max_rpm = 8000
        self.setMinimumSize(300, 80)
        self.setStyleSheet("background-color: #1a1a1a; border-radius: 8px;")

    def set_max_rpm(self, max_rpm):
        """Set maximum RPM for scaling."""
        self._max_rpm = max_rpm

    def update_data(self, data):
        """Update RPM from telemetry."""
        self._rpm = data.get('rpm', 0)
        self._max_rpm = data.get('max_rpm', 8000)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        margin = 10
        bar_height = 40

        bar_y = (h - bar_height) // 2
        bar_width = w - margin * 2
        bar_x = margin

        painter.fillRect(bar_x, bar_y, bar_width, bar_height, QColor(40, 40, 40))

        rpm_ratio = min(self._rpm / float(self._max_rpm), 1.0)
        fill_width = bar_width * rpm_ratio

        gradient = QLinearGradient(bar_x, 0, bar_x + bar_width, 0)
        gradient.setColorAt(0.0, QColor(100, 200, 100))
        gradient.setColorAt(0.7, QColor(255, 200, 50))
        gradient.setColorAt(1.0, QColor(200, 50, 50))

        painter.fillRect(bar_x, bar_y, int(fill_width), bar_height, gradient)

        redline_x = bar_x + bar_width * 0.9
        painter.setPen(QColor(255, 255, 255))
        painter.drawLine(int(redline_x), bar_y - 5, int(redline_x), bar_y + bar_height + 5)

        if rpm_ratio > 0.95:
            painter.fillRect(w - 30, 5, 20, 20, QColor(255, 255, 255))

        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor(200, 200, 200))

        rpm_text = "{0} RPM".format(int(self._rpm))
        painter.drawText(10, h - 15, rpm_text)

        painter.end()
