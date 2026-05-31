"""In-app console: live log + live values, with filters.

Opens from the Dashboard's View -> Console... menu. Non-modal -- stays
open alongside the main window, can be moved to a second monitor.

Two tabs:

  * Log tab -- monospace, color-coded by log level, filterable by source
    (logger name suffix), level, and free-text search. Pause / Clear /
    Save buttons. New log lines append in real time via the LogBus
    Qt signal installed at app startup.

  * Live Values tab -- a tree of the current state of the telemetry
    pipeline: connection health, session info, the UDP-driven telemetry
    fields, and the shared-memory-driven physics fields. Each leaf
    updates on its source's signal.
"""

from __future__ import annotations

import contextlib
import logging
from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QTextCharFormat, QTextCursor
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ontrack_dashboard.logging_bridge import LogBus
from ontrack_dashboard.network.shared_memory import PhysicsPacket, SharedMemoryReader
from ontrack_dashboard.network.udp_receiver import UDPReceiver
from ontrack_dashboard.telemetry import SessionInfo, TelemetryPacket
from ontrack_dashboard.theme import (
    ACCENT_AMBER,
    ACCENT_CYAN,
    ACCENT_LIME,
    ACCENT_RED,
    FG_PRIMARY,
    FG_SUBTLE,
)

_LEVEL_COLOR = {
    logging.DEBUG: QColor(120, 130, 145),
    logging.INFO: QColor(220, 226, 236),
    logging.WARNING: ACCENT_AMBER,
    logging.ERROR: ACCENT_RED,
    logging.CRITICAL: ACCENT_RED,
}

_SOURCE_FILTERS = [
    ("All sources", None),
    ("UDP receiver", "udp_receiver"),
    ("Shared memory", "shared_memory"),
    ("App", "app"),
]

_LEVEL_FILTERS = [
    ("All levels", 0),
    ("DEBUG and up", logging.DEBUG),
    ("INFO and up", logging.INFO),
    ("WARNING and up", logging.WARNING),
    ("ERROR and up", logging.ERROR),
]


class ConsoleWindow(QDialog):
    """Live console + live values view."""

    def __init__(
        self,
        udp_receiver: UDPReceiver,
        shm_reader: SharedMemoryReader,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("OnTrack — Console")
        self.setWindowFlag(Qt.WindowType.Window)  # independent, non-modal
        self.setMinimumSize(880, 580)

        self._udp_receiver = udp_receiver
        self._shm_reader = shm_reader

        # Filter state
        self._filter_source: str | None = None
        self._filter_level: int = 0
        self._filter_search: str = ""
        self._paused = False

        # Counters / latest state for live values
        self._udp_count = 0
        self._physics_count = 0
        self._last_telemetry = TelemetryPacket()
        self._last_physics = PhysicsPacket()

        self._build_ui()
        self._wire_signals()
        self._replay_buffer()
        self._refresh_live_values()  # initial seed

    # --- UI ----------------------------------------------------------------

    def _build_ui(self) -> None:
        tabs = QTabWidget()

        # Log tab
        log_tab = self._build_log_tab()
        tabs.addTab(log_tab, "Log")

        # Live values tab
        live_tab = self._build_live_tab()
        tabs.addTab(live_tab, "Live values")

        root = QVBoxLayout()
        root.setContentsMargins(12, 12, 12, 12)
        root.addWidget(tabs)
        self.setLayout(root)

    def _build_log_tab(self):
        tab = QWidget()

        # Filter row
        filter_row = QHBoxLayout()
        filter_row.setSpacing(8)

        self._source_combo = QComboBox()
        for label, _ in _SOURCE_FILTERS:
            self._source_combo.addItem(label)
        self._source_combo.currentIndexChanged.connect(self._on_source_changed)
        filter_row.addWidget(QLabel("Source:"))
        filter_row.addWidget(self._source_combo)

        self._level_combo = QComboBox()
        for label, _ in _LEVEL_FILTERS:
            self._level_combo.addItem(label)
        self._level_combo.currentIndexChanged.connect(self._on_level_changed)
        filter_row.addWidget(QLabel("Level:"))
        filter_row.addWidget(self._level_combo)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search…")
        self._search.textChanged.connect(self._on_search_changed)
        filter_row.addWidget(self._search, stretch=1)

        self._pause_btn = QCheckBox("Pause autoscroll")
        self._pause_btn.toggled.connect(self._on_pause_toggled)
        filter_row.addWidget(self._pause_btn)

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._on_clear)
        filter_row.addWidget(clear_btn)

        save_btn = QPushButton("Save…")
        save_btn.clicked.connect(self._on_save)
        filter_row.addWidget(save_btn)

        # Log view
        self._log_view = QPlainTextEdit()
        self._log_view.setReadOnly(True)
        self._log_view.setMaximumBlockCount(10000)
        mono = QFont("Cascadia Code")
        if not mono.exactMatch():
            mono = QFont("Consolas")
        mono.setPointSize(10)
        self._log_view.setFont(mono)
        self._log_view.setStyleSheet(
            "QPlainTextEdit { background: rgb(16,18,23); color: rgb(220,226,236); "
            "border: 1px solid rgba(255,255,255,18); border-radius: 8px; }"
        )

        layout = QVBoxLayout()
        layout.addLayout(filter_row)
        layout.addWidget(self._log_view)
        tab.setLayout(layout)
        return tab

    def _build_live_tab(self):
        tab = QWidget()

        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(["Field", "Value"])
        self._tree.setRootIsDecorated(True)
        self._tree.setUniformRowHeights(True)
        self._tree.setIndentation(18)
        self._tree.setColumnWidth(0, 260)
        self._tree.setStyleSheet(
            "QTreeWidget { background: rgb(16,18,23); color: rgb(220,226,236); "
            "border: 1px solid rgba(255,255,255,18); border-radius: 8px; padding: 6px; }"
            "QTreeWidget::item { padding: 4px; }"
            "QHeaderView::section { background: rgb(28,32,40); color: rgb(140,148,160); "
            "padding: 6px; border: none; }"
        )

        # Build a fixed tree skeleton so we can mutate leaves in place.
        self._items: dict[str, QTreeWidgetItem] = {}

        connection = QTreeWidgetItem(["Connection"])
        connection.setExpanded(True)
        self._tree.addTopLevelItem(connection)
        for key, label in (
            ("conn.udp", "UDP receiver"),
            ("conn.udp_count", "UDP packets received"),
            ("conn.shm", "Shared memory"),
            ("conn.shm_count", "Physics frames received"),
        ):
            item = QTreeWidgetItem([label, "—"])
            connection.addChild(item)
            self._items[key] = item

        session = QTreeWidgetItem(["Session"])
        session.setExpanded(True)
        self._tree.addTopLevelItem(session)
        for key, label in (
            ("sess.car", "Car"),
            ("sess.driver", "Driver"),
            ("sess.track", "Track"),
            ("sess.config", "Layout"),
        ):
            item = QTreeWidgetItem([label, "—"])
            session.addChild(item)
            self._items[key] = item

        telemetry = QTreeWidgetItem(["Telemetry (UDP)"])
        telemetry.setExpanded(True)
        self._tree.addTopLevelItem(telemetry)
        for key, label in (
            ("t.speed", "Speed (km/h)"),
            ("t.rpm", "RPM"),
            ("t.gear", "Gear"),
            ("t.throttle", "Throttle"),
            ("t.brake", "Brake"),
            ("t.lap", "Lap"),
            ("t.lap_time", "Current lap (ms)"),
            ("t.best", "Best lap (ms)"),
            ("t.last", "Last lap (ms)"),
            ("t.g_lat", "G lateral"),
            ("t.g_long", "G longitudinal"),
            ("t.g_vert", "G vertical"),
            ("t.abs", "ABS"),
            ("t.tc", "TC"),
            ("t.pos_norm", "Lap position (0-1)"),
            ("t.coords", "World coords (X Y Z)"),
        ):
            item = QTreeWidgetItem([label, "—"])
            telemetry.addChild(item)
            self._items[key] = item

        physics = QTreeWidgetItem(["Physics (shared memory)"])
        physics.setExpanded(True)
        self._tree.addTopLevelItem(physics)
        for key, label in (
            ("p.fuel", "Fuel (L)"),
            ("p.tyre_temps", "Tyre core temps (°C)"),
            ("p.tyre_press", "Tyre pressures (psi)"),
            ("p.tyre_wear", "Tyre wear (0-1)"),
            ("p.packet_id", "Packet ID"),
        ):
            item = QTreeWidgetItem([label, "—"])
            physics.addChild(item)
            self._items[key] = item

        layout = QVBoxLayout()
        layout.addWidget(self._tree)
        tab.setLayout(layout)
        return tab

    # --- signal wiring -----------------------------------------------------

    def _wire_signals(self) -> None:
        LogBus.instance().message_emitted.connect(self._on_log_record)

        self._udp_receiver.telemetry_received.connect(self._on_telemetry)
        self._udp_receiver.session_info_received.connect(self._on_session_info)
        self._udp_receiver.connection_status.connect(self._on_udp_status)

        self._shm_reader.physics_received.connect(self._on_physics)
        self._shm_reader.availability_changed.connect(self._on_shm_status)

    def closeEvent(self, event) -> None:  # noqa: N802 (Qt API)
        # Disconnect from signals so we stop adding work behind the scenes.
        with contextlib.suppress(TypeError):
            LogBus.instance().message_emitted.disconnect(self._on_log_record)
        super().closeEvent(event)

    # --- log handling ------------------------------------------------------

    def _replay_buffer(self) -> None:
        for record in LogBus.instance().buffer:
            self._append_record(record)

    def _on_log_record(self, record: logging.LogRecord) -> None:
        if not self._record_passes_filters(record):
            return
        self._append_record(record)

    def _record_passes_filters(self, record: logging.LogRecord) -> bool:
        if self._filter_level and record.levelno < self._filter_level:
            return False
        if self._filter_source and self._filter_source not in record.name:
            return False
        if self._filter_search:
            text = (record.getMessage() + record.name).lower()
            if self._filter_search not in text:
                return False
        return True

    def _append_record(self, record: logging.LogRecord) -> None:
        timestamp = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
        source = record.name.rsplit(".", 1)[-1]
        line = f"{timestamp} {record.levelname:7s} {source:18s} {record.getMessage()}"

        cursor = self._log_view.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        fmt = QTextCharFormat()
        fmt.setForeground(_LEVEL_COLOR.get(record.levelno, FG_PRIMARY))
        cursor.insertText(line + "\n", fmt)

        if not self._paused:
            sb = self._log_view.verticalScrollBar()
            sb.setValue(sb.maximum())

    # --- filter handlers ---------------------------------------------------

    def _on_source_changed(self, idx: int) -> None:
        self._filter_source = _SOURCE_FILTERS[idx][1]
        self._reapply_filters()

    def _on_level_changed(self, idx: int) -> None:
        self._filter_level = _LEVEL_FILTERS[idx][1]
        self._reapply_filters()

    def _on_search_changed(self, text: str) -> None:
        self._filter_search = text.strip().lower()
        self._reapply_filters()

    def _on_pause_toggled(self, checked: bool) -> None:
        self._paused = checked

    def _reapply_filters(self) -> None:
        self._log_view.clear()
        for record in LogBus.instance().buffer:
            if self._record_passes_filters(record):
                self._append_record(record)

    # --- toolbar -----------------------------------------------------------

    def _on_clear(self) -> None:
        self._log_view.clear()

    def _on_save(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Save log", "ontrack-console.log",
            "Log files (*.log);;Text files (*.txt);;All files (*)",
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(self._log_view.toPlainText())
        except OSError as exc:
            logging.getLogger(__name__).exception(
                "failed to save console log: %s", exc
            )

    # --- live values -------------------------------------------------------

    def _on_telemetry(self, packet: TelemetryPacket) -> None:
        self._udp_count += 1
        self._last_telemetry = packet
        self._refresh_telemetry_live()

    def _on_physics(self, physics: PhysicsPacket) -> None:
        self._physics_count += 1
        self._last_physics = physics
        self._refresh_physics_live()

    def _on_session_info(self, session: SessionInfo) -> None:
        self._items["sess.car"].setText(1, session.car_name or "—")
        self._items["sess.driver"].setText(1, session.driver_name or "—")
        self._items["sess.track"].setText(1, session.track_name or "—")
        self._items["sess.config"].setText(1, session.track_config or "—")

    def _on_udp_status(self, connected: bool) -> None:
        item = self._items["conn.udp"]
        item.setText(1, "● connected" if connected else "○ waiting")
        item.setForeground(1, ACCENT_LIME if connected else FG_SUBTLE)

    def _on_shm_status(self, available: bool) -> None:
        item = self._items["conn.shm"]
        item.setText(1, "● available" if available else "○ waiting")
        item.setForeground(1, ACCENT_CYAN if available else FG_SUBTLE)

    def _refresh_live_values(self) -> None:
        # Seed defaults so the tab is populated before any signal fires.
        self._items["conn.udp"].setText(1, "○ waiting")
        self._items["conn.shm"].setText(1, "○ waiting")
        self._refresh_telemetry_live()
        self._refresh_physics_live()

    def _refresh_telemetry_live(self) -> None:
        p = self._last_telemetry
        i = self._items
        i["conn.udp_count"].setText(1, str(self._udp_count))
        i["t.speed"].setText(1, f"{p.speed_kmh:.1f}")
        i["t.rpm"].setText(1, str(p.rpm))
        i["t.gear"].setText(1, _gear_label(p.gear))
        i["t.throttle"].setText(1, f"{p.throttle:.2f}")
        i["t.brake"].setText(1, f"{p.brake:.2f}")
        i["t.lap"].setText(1, str(p.lap))
        i["t.lap_time"].setText(1, str(p.lap_time_ms))
        i["t.best"].setText(1, str(p.best_lap_ms))
        i["t.last"].setText(1, str(p.last_lap_ms))
        i["t.g_lat"].setText(1, f"{p.g_lat:+.2f}")
        i["t.g_long"].setText(1, f"{p.g_long:+.2f}")
        i["t.g_vert"].setText(1, f"{p.g_vert:+.2f}")
        i["t.abs"].setText(
            1, _flag_label(p.abs_enabled, p.abs_in_action),
        )
        i["t.tc"].setText(
            1, _flag_label(p.tc_enabled, p.tc_in_action),
        )
        i["t.pos_norm"].setText(1, f"{p.car_pos_normalized:.3f}")
        i["t.coords"].setText(
            1, f"({p.car_x:+.1f}, {p.car_y:+.1f}, {p.car_z:+.1f})",
        )

    def _refresh_physics_live(self) -> None:
        p = self._last_physics
        i = self._items
        i["conn.shm_count"].setText(1, str(self._physics_count))
        i["p.fuel"].setText(1, f"{p.fuel:.2f}")
        i["p.tyre_temps"].setText(
            1,
            "FL {:.1f}  FR {:.1f}  RL {:.1f}  RR {:.1f}".format(*p.tyre_core_temps_c),
        )
        i["p.tyre_press"].setText(
            1,
            "FL {:.1f}  FR {:.1f}  RL {:.1f}  RR {:.1f}".format(*p.tyre_pressures),
        )
        i["p.tyre_wear"].setText(
            1,
            "FL {:.3f}  FR {:.3f}  RL {:.3f}  RR {:.3f}".format(*p.tyre_wear),
        )
        i["p.packet_id"].setText(1, str(p.packet_id))


# --- helpers ---------------------------------------------------------------


def _gear_label(gear: int) -> str:
    if gear == 0:
        return "R"
    if gear == 1:
        return "N"
    return str(gear - 1)


def _flag_label(enabled: bool, active: bool) -> str:
    if active:
        return "ACTIVE"
    if enabled:
        return "on"
    return "off"


# Module-level reference so ruff doesn't flag FG_PRIMARY as unused -- it's
# the fallback color used by the level table.
_FALLBACK_FG = FG_PRIMARY
