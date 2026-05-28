import re
from PyQt6.QtWidgets import (QDialog, QFormLayout, QLineEdit, QSpinBox,
                             QCheckBox, QComboBox, QPushButton, QVBoxLayout,
                             QHBoxLayout, QLabel, QMessageBox)
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont

class SettingsDialog(QDialog):
    settings_changed = pyqtSignal(dict)

    def __init__(self, current_config, parent=None):
        super().__init__(parent)
        self.setWindowTitle("OnTrack Settings")
        self.setGeometry(100, 100, 500, 600)
        self.current_config = dict(current_config)

        self.init_ui()

    def init_ui(self):
        """Initialize the settings dialog UI."""
        layout = QVBoxLayout()

        form_layout = QFormLayout()

        title = QLabel("OnTrack Telemetry Settings")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        self.udp_ip = QLineEdit()
        self.udp_ip.setText(self.current_config.get('udp_ip', '0.0.0.0'))
        form_layout.addRow("UDP Bind IP:", self.udp_ip)

        self.udp_port = QSpinBox()
        self.udp_port.setMinimum(1024)
        self.udp_port.setMaximum(65535)
        self.udp_port.setValue(self.current_config.get('udp_port', 20777))
        form_layout.addRow("UDP Port:", self.udp_port)

        self.max_rpm = QSpinBox()
        self.max_rpm.setMinimum(3000)
        self.max_rpm.setMaximum(20000)
        self.max_rpm.setValue(self.current_config.get('max_rpm', 8000))
        self.max_rpm.setSingleStep(500)
        form_layout.addRow("Max RPM:", self.max_rpm)

        self.speed_unit = QComboBox()
        self.speed_unit.addItems(["kmh", "mph"])
        self.speed_unit.setCurrentText(self.current_config.get('speed_unit', 'kmh'))
        form_layout.addRow("Speed Unit:", self.speed_unit)

        form_layout.addRow("", QLabel(""))

        self.dark_mode = QCheckBox("Dark Mode")
        self.dark_mode.setChecked(self.current_config.get('dark_mode', True))
        form_layout.addRow(self.dark_mode)

        form_layout.addRow("", QLabel("Show/Hide Widgets:"))

        self.show_speed = QCheckBox("Speed Gauge")
        self.show_speed.setChecked(self.current_config.get('show_speed', True))
        form_layout.addRow(self.show_speed)

        self.show_rpm = QCheckBox("RPM Bar")
        self.show_rpm.setChecked(self.current_config.get('show_rpm', True))
        form_layout.addRow(self.show_rpm)

        self.show_pedals = QCheckBox("Pedals")
        self.show_pedals.setChecked(self.current_config.get('show_pedals', True))
        form_layout.addRow(self.show_pedals)

        self.show_gear = QCheckBox("Gear Display")
        self.show_gear.setChecked(self.current_config.get('show_gear', True))
        form_layout.addRow(self.show_gear)

        self.show_lap_times = QCheckBox("Lap Times")
        self.show_lap_times.setChecked(self.current_config.get('show_lap_times', True))
        form_layout.addRow(self.show_lap_times)

        self.show_tire_temps = QCheckBox("Tire Temperatures")
        self.show_tire_temps.setChecked(self.current_config.get('show_tire_temps', True))
        form_layout.addRow(self.show_tire_temps)

        self.show_gforces = QCheckBox("G-Forces")
        self.show_gforces.setChecked(self.current_config.get('show_gforces', True))
        form_layout.addRow(self.show_gforces)

        layout.addLayout(form_layout)

        button_layout = QHBoxLayout()
        apply_btn = QPushButton("Apply")
        cancel_btn = QPushButton("Cancel")

        apply_btn.clicked.connect(self.apply_settings)
        cancel_btn.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(apply_btn)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def apply_settings(self):
        """Validate and apply settings."""
        ip = self.udp_ip.text().strip()

        if ip != "0.0.0.0":
            if not self.is_valid_ip(ip):
                QMessageBox.warning(self, "Invalid IP", "Please enter a valid IP address or 0.0.0.0")
                return

        config = {
            'udp_ip': ip,
            'udp_port': self.udp_port.value(),
            'dark_mode': self.dark_mode.isChecked(),
            'max_rpm': self.max_rpm.value(),
            'speed_unit': self.speed_unit.currentText(),
            'show_speed': self.show_speed.isChecked(),
            'show_rpm': self.show_rpm.isChecked(),
            'show_pedals': self.show_pedals.isChecked(),
            'show_gear': self.show_gear.isChecked(),
            'show_lap_times': self.show_lap_times.isChecked(),
            'show_tire_temps': self.show_tire_temps.isChecked(),
            'show_gforces': self.show_gforces.isChecked()
        }

        self.settings_changed.emit(config)
        self.accept()

    def is_valid_ip(self, ip):
        """Validate IP address format."""
        pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if not re.match(pattern, ip):
            return False
        parts = ip.split('.')
        for part in parts:
            if int(part) > 255:
                return False
        return True
