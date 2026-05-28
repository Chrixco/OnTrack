from PyQt6.QtWidgets import (QMainWindow, QWidget, QGridLayout, QVBoxLayout,
                             QMenuBar, QMenu)
from PyQt6.QtGui import QPalette, QColor, QFont, QAction
from PyQt6.QtCore import Qt

from settings.config_manager import ConfigManager
from settings.settings_dialog import SettingsDialog
from network.udp_receiver import UDPReceiver

from widgets.speed_gauge import SpeedGauge
from widgets.rpm_bar import RPMBar
from widgets.pedals import PedalWidget
from widgets.lap_times import LapTimesWidget
from widgets.gear_display import GearDisplay
from widgets.tire_temps import TireTempsWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.config_manager = ConfigManager()
        self.config = self.config_manager.config

        self.setWindowTitle("OnTrack Telemetry Dashboard")
        self.setGeometry(100, 100, 1200, 800)

        self.init_dark_mode()
        self.init_ui()
        self.setup_udp_receiver()

    def init_dark_mode(self):
        """Initialize dark mode theme."""
        app = self.parent() or self

        self.dark_palette = QPalette()
        self.dark_palette.setColor(QPalette.ColorRole.Window, QColor(25, 25, 30))
        self.dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(200, 200, 200))
        self.dark_palette.setColor(QPalette.ColorRole.Base, QColor(35, 35, 40))
        self.dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(50, 50, 60))
        self.dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(0, 0, 0))
        self.dark_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(200, 200, 200))
        self.dark_palette.setColor(QPalette.ColorRole.Text, QColor(200, 200, 200))
        self.dark_palette.setColor(QPalette.ColorRole.Button, QColor(50, 50, 60))
        self.dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor(200, 200, 200))
        self.dark_palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 255, 255))
        self.dark_palette.setColor(QPalette.ColorRole.Link, QColor(100, 150, 255))
        self.dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(100, 150, 255))
        self.dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))

        if self.config.get('dark_mode', True):
            self.setPalette(self.dark_palette)

    def init_ui(self):
        """Initialize the main UI layout."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QGridLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        self.speed_gauge = SpeedGauge()
        self.speed_gauge.set_speed_unit(self.config.get('speed_unit', 'kmh'))
        layout.addWidget(self.speed_gauge, 0, 0, 2, 1)

        self.gear_display = GearDisplay()
        layout.addWidget(self.gear_display, 0, 1)

        self.rpm_bar = RPMBar()
        self.rpm_bar.set_max_rpm(self.config.get('max_rpm', 8000))
        layout.addWidget(self.rpm_bar, 0, 2)

        self.pedals = PedalWidget()
        layout.addWidget(self.pedals, 1, 1)

        self.lap_times = LapTimesWidget()
        layout.addWidget(self.lap_times, 1, 2)

        self.tire_temps = TireTempsWidget()
        layout.addWidget(self.tire_temps, 2, 0, 1, 3)

        central_widget.setLayout(layout)

        self.setup_menu()

    def setup_menu(self):
        """Setup menu bar."""
        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.open_settings)
        file_menu.addAction(settings_action)
        file_menu.addSeparator()
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        view_menu = menubar.addMenu("View")
        dark_mode_action = QAction("Toggle Dark Mode", self)
        dark_mode_action.triggered.connect(self.toggle_dark_mode)
        view_menu.addAction(dark_mode_action)

        help_menu = menubar.addMenu("Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def setup_udp_receiver(self):
        """Initialize UDP receiver thread."""
        ip = self.config.get('udp_ip', '0.0.0.0')
        port = self.config.get('udp_port', 20777)

        self.udp_receiver = UDPReceiver(ip, port)
        self.udp_receiver.telemetry_received.connect(self.on_telemetry)
        self.udp_receiver.start()

    def on_telemetry(self, data):
        """Handle telemetry data from UDP receiver."""
        if self.config.get('show_speed', True):
            self.speed_gauge.update_data(data)
        if self.config.get('show_rpm', True):
            self.rpm_bar.update_data(data)
        if self.config.get('show_pedals', True):
            self.pedals.update_data(data)
        if self.config.get('show_gear', True):
            self.gear_display.update_data(data)
        if self.config.get('show_lap_times', True):
            self.lap_times.update_data(data)
        if self.config.get('show_tire_temps', True):
            self.tire_temps.update_data(data)

    def open_settings(self):
        """Open settings dialog."""
        dialog = SettingsDialog(self.config, self)
        dialog.settings_changed.connect(self.apply_settings)
        dialog.exec()

    def apply_settings(self, new_config):
        """Apply new settings."""
        self.config_manager.update(**new_config)
        self.config = dict(new_config)

        self.speed_gauge.set_speed_unit(self.config.get('speed_unit', 'kmh'))
        self.rpm_bar.set_max_rpm(self.config.get('max_rpm', 8000))

        if self.config.get('dark_mode', True):
            self.setPalette(self.dark_palette)

        self.udp_receiver.stop()

        ip = self.config.get('udp_ip', '0.0.0.0')
        port = self.config.get('udp_port', 20777)

        self.udp_receiver = UDPReceiver(ip, port)
        self.udp_receiver.telemetry_received.connect(self.on_telemetry)
        self.udp_receiver.start()

    def toggle_dark_mode(self):
        """Toggle dark mode."""
        is_dark = self.config.get('dark_mode', True)
        self.config['dark_mode'] = not is_dark
        self.config_manager.set('dark_mode', not is_dark)

        if not is_dark:
            self.setPalette(self.dark_palette)
        else:
            self.setPalette(self.style().standardPalette())

    def show_about(self):
        """Show about dialog."""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.about(self, "About OnTrack",
                         "OnTrack Telemetry Dashboard v1.0\n\n"
                         "Real-time telemetry visualization for Assetto Corsa\n\n"
                         "Receives data from the AC plugin via UDP")

    def closeEvent(self, event):
        """Handle window close."""
        if hasattr(self, 'udp_receiver'):
            self.udp_receiver.stop()
        event.accept()
