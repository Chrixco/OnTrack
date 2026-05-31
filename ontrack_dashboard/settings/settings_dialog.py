"""Settings dialog -- minimal, themed."""

from __future__ import annotations

import re

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)


class SettingsDialog(QDialog):
    settings_changed = pyqtSignal(dict)

    def __init__(self, current_config, parent=None):
        super().__init__(parent)
        self.setWindowTitle("OnTrack — Settings")
        self.setMinimumWidth(420)
        self.current_config = dict(current_config)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout()

        title = QLabel("OnTrack Settings")
        title_font = QFont()
        title_font.setPointSize(13)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        layout.addSpacing(8)

        form = QFormLayout()
        form.setSpacing(10)

        self.ac_ip = QLineEdit()
        self.ac_ip.setText(self.current_config.get("ac_ip", "127.0.0.1"))
        form.addRow("AC server IP:", self.ac_ip)

        self.ac_port = QSpinBox()
        self.ac_port.setMinimum(1)
        self.ac_port.setMaximum(65535)
        self.ac_port.setValue(self.current_config.get("ac_port", 9996))
        form.addRow("AC UDP port:", self.ac_port)

        self.max_rpm = QSpinBox()
        self.max_rpm.setMinimum(2000)
        self.max_rpm.setMaximum(22000)
        self.max_rpm.setSingleStep(500)
        self.max_rpm.setValue(self.current_config.get("max_rpm", 8000))
        form.addRow("Max RPM:", self.max_rpm)

        self.speed_unit = QComboBox()
        self.speed_unit.addItems(["kmh", "mph"])
        self.speed_unit.setCurrentText(self.current_config.get("speed_unit", "kmh"))
        form.addRow("Speed unit:", self.speed_unit)

        self.dark_mode = QCheckBox("Dark mode")
        self.dark_mode.setChecked(self.current_config.get("dark_mode", True))
        form.addRow("", self.dark_mode)

        layout.addLayout(form)
        layout.addSpacing(12)

        buttons = QHBoxLayout()
        apply_btn = QPushButton("Apply")
        cancel_btn = QPushButton("Cancel")
        apply_btn.clicked.connect(self._apply)
        cancel_btn.clicked.connect(self.reject)
        buttons.addStretch()
        buttons.addWidget(apply_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)

        self.setLayout(layout)

    def _apply(self) -> None:
        ip = self.ac_ip.text().strip()
        if not self._is_valid_ip(ip):
            QMessageBox.warning(
                self,
                "Invalid IP",
                "Please enter a valid IP address (e.g. 127.0.0.1 for same-machine).",
            )
            return

        config = {
            "ac_ip": ip,
            "ac_port": self.ac_port.value(),
            "max_rpm": self.max_rpm.value(),
            "speed_unit": self.speed_unit.currentText(),
            "dark_mode": self.dark_mode.isChecked(),
        }
        self.settings_changed.emit(config)
        self.accept()

    @staticmethod
    def _is_valid_ip(ip: str) -> bool:
        pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
        if not re.match(pattern, ip):
            return False
        return all(int(part) <= 255 for part in ip.split("."))
