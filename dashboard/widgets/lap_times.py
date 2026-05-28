from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QFont, QColor
from PyQt6.QtCore import Qt

class LapTimesWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._current_lap = 0
        self._lap_time = 0
        self._best_lap = 0
        self._last_lap = 0
        self._lap_count = 0
        self.setMinimumSize(250, 120)
        self.setStyleSheet("background-color: #1a1a1a; border-radius: 8px;")

    def update_data(self, data):
        """Update lap times from telemetry."""
        self._lap_time = data.get('lap_t', 0)
        self._best_lap = data.get('best_t', 0)
        self._last_lap = data.get('last_t', 0)
        self._lap_count = data.get('lap', 0)
        self.update()

    def format_ms(self, ms):
        """Format milliseconds to M:SS.mmm."""
        if ms <= 0:
            return "--:--.---"
        s = ms / 1000.0
        mins = int(s) // 60
        secs = s - mins * 60
        return "{0:d}:{1:06.3f}".format(mins, secs)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        font_small = QFont()
        font_small.setPointSize(9)
        painter.setFont(font_small)

        x = 15
        y = 15
        line_height = 28

        painter.setPen(QColor(150, 150, 150))
        painter.drawText(x, y, "CURR:")
        painter.setPen(QColor(200, 200, 200))
        painter.drawText(x + 80, y, self.format_ms(self._lap_time))

        painter.setPen(QColor(150, 150, 150))
        painter.drawText(x, y + line_height, "BEST:")
        painter.setPen(QColor(255, 215, 0))
        painter.drawText(x + 80, y + line_height, self.format_ms(self._best_lap))

        painter.setPen(QColor(150, 150, 150))
        painter.drawText(x, y + line_height * 2, "LAST:")
        if self._last_lap > 0 and self._best_lap > 0:
            delta = self._last_lap - self._best_lap
            if delta < 0:
                painter.setPen(QColor(100, 200, 100))
            else:
                painter.setPen(QColor(200, 100, 100))
            delta_text = "{0:.3f}".format(delta / 1000.0)
            painter.drawText(x + 80, y + line_height * 2, self.format_ms(self._last_lap))
        else:
            painter.setPen(QColor(200, 200, 200))
            painter.drawText(x + 80, y + line_height * 2, self.format_ms(self._last_lap))

        font_large = QFont()
        font_large.setPointSize(12)
        font_large.setBold(True)
        painter.setFont(font_large)
        painter.setPen(QColor(100, 150, 255))
        painter.drawText(w - 100, 15, "LAP {0}".format(self._lap_count))

        painter.end()
