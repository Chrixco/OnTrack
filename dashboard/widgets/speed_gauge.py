import math
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QFont, QPainterPath, QPolygonF, QPen
from PyQt6.QtCore import Qt, QPointF

class SpeedGauge(QWidget):
    def __init__(self):
        super().__init__()
        self._speed = 0.0
        self._max_speed = 300.0
        self._speed_unit = "kmh"
        self.setMinimumSize(250, 250)
        self.setStyleSheet("background-color: #1a1a1a; border-radius: 8px;")

    def set_speed_unit(self, unit):
        """Set speed unit (kmh or mph)."""
        self._speed_unit = unit

    def update_data(self, data):
        """Update speed from telemetry."""
        self._speed = data.get('spd', 0.0)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        center_x = w / 2.0
        center_y = h / 2.0
        radius = min(w, h) / 2.0 - 20

        painter.setBrush(QColor(30, 30, 40))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(int(center_x - radius), int(center_y - radius),
                           int(radius * 2), int(radius * 2))

        self.draw_gauge_background(painter, center_x, center_y, radius)
        self.draw_ticks(painter, center_x, center_y, radius)
        self.draw_needle(painter, center_x, center_y, radius)

        painter.setPen(QColor(200, 200, 200))
        painter.setBrush(QColor(50, 50, 60))
        painter.drawEllipse(int(center_x - 8), int(center_y - 8), 16, 16)

        font = QFont()
        font.setPointSize(28)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor(100, 200, 100))

        speed_text = "{0:.0f}".format(self._speed)
        painter.drawText(int(center_x - 50), int(center_y + 30),
                        100, 40, Qt.AlignmentFlag.AlignCenter, speed_text)

        font_small = QFont()
        font_small.setPointSize(10)
        painter.setFont(font_small)
        painter.setPen(QColor(150, 150, 150))

        unit_text = "km/h" if self._speed_unit == "kmh" else "mph"
        painter.drawText(int(center_x - 40), int(center_y + 65),
                        80, 20, Qt.AlignmentFlag.AlignCenter, unit_text)

        painter.end()

    def draw_gauge_background(self, painter, cx, cy, radius):
        """Draw the gauge arc background."""
        painter.setPen(QPen(QColor(80, 80, 100), 2))
        start_angle = 225
        span_angle = -270
        painter.drawArc(int(cx - radius), int(cy - radius),
                       int(radius * 2), int(radius * 2),
                       int(start_angle * 16), int(span_angle * 16))

    def draw_ticks(self, painter, cx, cy, radius):
        """Draw speed ticks around the gauge."""
        painter.setPen(QColor(100, 100, 120))

        for speed in range(0, int(self._max_speed) + 1, 20):
            angle_deg = 225 - (speed / self._max_speed) * 270
            angle_rad = math.radians(angle_deg)

            outer_x = cx + radius * math.cos(angle_rad)
            outer_y = cy + radius * math.sin(angle_rad)

            inner_x = cx + (radius - 15) * math.cos(angle_rad)
            inner_y = cy + (radius - 15) * math.sin(angle_rad)

            painter.drawLine(int(inner_x), int(inner_y),
                           int(outer_x), int(outer_y))

            label_x = cx + (radius - 35) * math.cos(angle_rad)
            label_y = cy + (radius - 35) * math.sin(angle_rad)

            font = QFont()
            font.setPointSize(8)
            painter.setFont(font)
            painter.drawText(int(label_x - 10), int(label_y - 10),
                           20, 20, Qt.AlignmentFlag.AlignCenter,
                           str(int(speed)))

    def draw_needle(self, painter, cx, cy, radius):
        """Draw the rotating speed needle."""
        speed_ratio = min(self._speed / self._max_speed, 1.0)
        angle_deg = 225 - (speed_ratio * 270)
        angle_rad = math.radians(angle_deg)

        needle_length = radius - 30

        tip_x = cx + needle_length * math.cos(angle_rad)
        tip_y = cy + needle_length * math.sin(angle_rad)

        perp_angle = angle_rad + math.pi / 2
        base_width = 6

        base_x1 = cx + base_width * math.cos(perp_angle)
        base_y1 = cy + base_width * math.sin(perp_angle)

        base_x2 = cx - base_width * math.cos(perp_angle)
        base_y2 = cy - base_width * math.sin(perp_angle)

        polygon = QPolygonF([
            QPointF(base_x1, base_y1),
            QPointF(base_x2, base_y2),
            QPointF(tip_x, tip_y)
        ])

        painter.setBrush(QColor(220, 50, 50))
        painter.setPen(QColor(200, 30, 30))
        painter.drawPolygon(polygon)
