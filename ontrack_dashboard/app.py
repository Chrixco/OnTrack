"""Main window for the OnTrack dashboard.

Three-column neumorphic layout:

  +----------------+--------------------------------+----------------+
  |   car info     |   shift indicator              |                |
  |   pedals       |   speed display                |  race stats    |
  |   input trace  |   accel | assists | fuel       |                |
  |   tyre temps   |                                |                |
  +----------------+--------------------------------+----------------+
"""

from __future__ import annotations

import dataclasses
import logging
from collections.abc import Mapping
from typing import Any

from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QApplication,
    QGridLayout,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from ontrack_dashboard.network.shared_memory import PhysicsPacket, SharedMemoryReader
from ontrack_dashboard.network.udp_receiver import UDPReceiver
from ontrack_dashboard.settings.config_manager import ConfigManager
from ontrack_dashboard.settings.settings_dialog import SettingsDialog
from ontrack_dashboard.telemetry import SessionInfo, TelemetryPacket
from ontrack_dashboard.theme import GLOBAL_QSS, GUTTER, build_app_palette
from ontrack_dashboard.widgets.acceleration_display import AccelerationDisplay
from ontrack_dashboard.widgets.assists_card import AssistsCard
from ontrack_dashboard.widgets.car_info_panel import CarInfoPanel
from ontrack_dashboard.widgets.circuit_map_card import CircuitMapCard
from ontrack_dashboard.widgets.console_window import ConsoleWindow
from ontrack_dashboard.widgets.fuel_display import FuelDisplay
from ontrack_dashboard.widgets.input_graph import InputGraph
from ontrack_dashboard.widgets.pedals_card import PedalsCard
from ontrack_dashboard.widgets.race_stats_panel import RaceStatsPanel
from ontrack_dashboard.widgets.shift_indicator import ShiftIndicator
from ontrack_dashboard.widgets.speed_display import SpeedDisplay
from ontrack_dashboard.widgets.wheel_temps_card import WheelTempsCard

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.config_manager = ConfigManager()
        self.config = self.config_manager.config
        self.udp_receiver: UDPReceiver | None = None
        self.shm_reader: SharedMemoryReader | None = None
        self.console: ConsoleWindow | None = None
        # Latest snapshot from each transport. UDP carries speed / RPM /
        # gear / pedals / lap times / G; shared memory overlays tyre
        # temps + fuel that UDP doesn't include.
        self._last_udp = TelemetryPacket()
        self._last_physics = PhysicsPacket()

        self.setWindowTitle("OnTrack")
        self.setMinimumSize(1280, 820)
        self.resize(1600, 960)

        # Apply theme to the whole app (palette + QSS for menus/dialogs)
        app = QApplication.instance()
        if app is not None:
            app.setStyle("Fusion")
            app.setPalette(build_app_palette())
            app.setStyleSheet(GLOBAL_QSS)

        self._init_ui()
        self._setup_menu()
        self._start_receiver(self.config["ac_ip"], self.config["ac_port"])
        self._start_shared_memory()

    # --- UI ----------------------------------------------------------------

    def _init_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        # Cards
        self.car_info = CarInfoPanel()
        self.pedals = PedalsCard()
        self.input_graph = InputGraph()
        self.wheel_temps = WheelTempsCard()

        self.shift = ShiftIndicator()
        self.shift.set_max_rpm(self.config.get("max_rpm", 8000))
        self.speed = SpeedDisplay()
        self.speed.set_speed_unit(self.config.get("speed_unit", "kmh"))
        self.accel = AccelerationDisplay()
        self.assists = AssistsCard()
        self.fuel = FuelDisplay()

        self.circuit_map = CircuitMapCard()
        self.race_stats = RaceStatsPanel()

        # --- Left column: 4 stacked cards
        left_layout = QVBoxLayout()
        left_layout.setSpacing(0)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(self.car_info, stretch=3)
        left_layout.addWidget(self.pedals, stretch=2)
        left_layout.addWidget(self.input_graph, stretch=3)
        left_layout.addWidget(self.wheel_temps, stretch=3)
        left_widget = QWidget()
        left_widget.setLayout(left_layout)

        # --- Center column
        center_layout = QVBoxLayout()
        center_layout.setSpacing(0)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.addWidget(self.shift, stretch=2)
        center_layout.addWidget(self.speed, stretch=3)

        # Bottom row: accel | assists | fuel
        bottom_grid = QGridLayout()
        bottom_grid.setSpacing(0)
        bottom_grid.setContentsMargins(0, 0, 0, 0)
        bottom_grid.addWidget(self.accel, 0, 0)
        bottom_grid.addWidget(self.assists, 0, 1)
        bottom_grid.addWidget(self.fuel, 0, 2)
        bottom_grid.setColumnStretch(0, 3)
        bottom_grid.setColumnStretch(1, 2)
        bottom_grid.setColumnStretch(2, 3)
        bottom_holder = QWidget()
        bottom_holder.setLayout(bottom_grid)
        center_layout.addWidget(bottom_holder, stretch=3)

        center_widget = QWidget()
        center_widget.setLayout(center_layout)

        # --- Right column: circuit map (top) + race stats (bottom)
        right_layout = QVBoxLayout()
        right_layout.setSpacing(0)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addWidget(self.circuit_map, stretch=5)
        right_layout.addWidget(self.race_stats, stretch=6)
        right_widget = QWidget()
        right_widget.setLayout(right_layout)

        # Top-level: left | center | right
        root = QHBoxLayout()
        root.setSpacing(0)
        root.setContentsMargins(GUTTER, GUTTER, GUTTER, GUTTER)
        root.addWidget(left_widget, stretch=3)
        root.addWidget(center_widget, stretch=5)
        root.addWidget(right_widget, stretch=3)

        central.setLayout(root)

    def _setup_menu(self) -> None:
        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")
        settings_action = QAction("Settings…", self)
        settings_action.triggered.connect(self.open_settings)
        file_menu.addAction(settings_action)
        file_menu.addSeparator()
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        view_menu = menubar.addMenu("View")
        console_action = QAction("Console…", self)
        console_action.setShortcut("Ctrl+Shift+C")
        console_action.triggered.connect(self.open_console)
        view_menu.addAction(console_action)

        help_menu = menubar.addMenu("Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    # --- Telemetry wiring --------------------------------------------------

    def on_telemetry(self, packet: TelemetryPacket) -> None:
        self._last_udp = packet
        self._dispatch_merged()

    def on_physics(self, physics: PhysicsPacket) -> None:
        self._last_physics = physics
        self._dispatch_merged()

    def _dispatch_merged(self) -> None:
        """Overlay physics fields onto the latest UDP packet, push to widgets."""
        merged = dataclasses.replace(
            self._last_udp,
            fuel=self._last_physics.fuel,
            tyre_temps_c=self._last_physics.tyre_core_temps_c,
        )
        self.shift.update_data(merged)
        self.speed.update_data(merged)
        self.accel.update_data(merged)
        self.assists.update_data(merged)
        self.fuel.update_data(merged)
        self.pedals.update_data(merged)
        self.input_graph.update_data(merged)
        self.wheel_temps.update_data(merged)
        self.circuit_map.update_data(merged)
        self.race_stats.update_data(merged)

    def on_session_info(self, session: SessionInfo) -> None:
        self.car_info.set_session(session)
        self.circuit_map.set_session(session)

    def on_connection(self, connected: bool) -> None:
        self.car_info.set_connected(connected)

    # --- Receiver lifecycle ------------------------------------------------

    def _start_receiver(self, ip: str, port: int) -> None:
        self.udp_receiver = UDPReceiver(ip, port)
        self.udp_receiver.telemetry_received.connect(self.on_telemetry)
        self.udp_receiver.session_info_received.connect(self.on_session_info)
        self.udp_receiver.connection_status.connect(self.on_connection)
        self.udp_receiver.start()

    def _restart_receiver(self, ip: str, port: int) -> None:
        if self.udp_receiver is not None:
            self.udp_receiver.stop()
        self._start_receiver(ip, port)

    def _start_shared_memory(self) -> None:
        self.shm_reader = SharedMemoryReader()
        self.shm_reader.physics_received.connect(self.on_physics)
        self.shm_reader.start()

    # --- Settings ----------------------------------------------------------

    def open_settings(self) -> None:
        dialog = SettingsDialog(self.config, self)
        dialog.settings_changed.connect(self.apply_settings)
        dialog.exec()

    def open_console(self) -> None:
        """Open or focus the live console window."""
        if (
            self.console is None
            or not self.console.isVisible()
            or self.udp_receiver is None
            or self.shm_reader is None
        ):
            if self.udp_receiver is None or self.shm_reader is None:
                return
            self.console = ConsoleWindow(self.udp_receiver, self.shm_reader, self)
            self.console.show()
        else:
            self.console.raise_()
            self.console.activateWindow()

    def apply_settings(self, new_config: Mapping[str, Any]) -> None:
        old_ip = self.config.get("ac_ip", "127.0.0.1")
        old_port = self.config.get("ac_port", 9996)

        self.config_manager.update(**new_config)
        self.config = dict(new_config)

        self.speed.set_speed_unit(self.config.get("speed_unit", "kmh"))
        self.shift.set_max_rpm(self.config.get("max_rpm", 8000))

        new_ip = self.config.get("ac_ip", "127.0.0.1")
        new_port = self.config.get("ac_port", 9996)
        if new_ip != old_ip or new_port != old_port:
            logger.info(
                "AC target changed %s:%s -> %s:%s, restarting client",
                old_ip, old_port, new_ip, new_port,
            )
            self._restart_receiver(new_ip, new_port)

    def show_about(self) -> None:
        QMessageBox.about(
            self,
            "About OnTrack",
            "OnTrack Telemetry Dashboard\n\n"
            "Real-time telemetry for Assetto Corsa over AC's first-party UDP.\n"
            "No in-game plugin required.",
        )

    def closeEvent(self, event) -> None:  # noqa: N802 (Qt API name)
        if self.console is not None:
            self.console.close()
        if self.udp_receiver is not None:
            self.udp_receiver.stop()
        if self.shm_reader is not None:
            self.shm_reader.stop()
        event.accept()
