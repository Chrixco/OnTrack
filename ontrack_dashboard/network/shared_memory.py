"""AC shared-memory physics reader.

Bridges Assetto Corsa's first-party `Local\\acpmf_physics` shared-memory
region into the same widget pipeline used by the UDP receiver. Carries
the fields RTCarInfo omits -- principally tyre core temperatures and
fuel level -- without requiring an in-game plugin.

The shared-memory transport is Windows-only and same-machine only. The
reader sleeps + retries while AC is closed; once a session starts AC
creates the file mapping and the reader picks it up on the next poll.

Layout source: Kunos AC SDK / SPageFilePhysics struct. Fields up to and
including the ones we consume are mirrored 1:1; trailing fields are not
declared (the mmap is read by size, so an over-reserved struct would
fail). The mapping size is rounded up to comfortably exceed the real
struct -- ctypes reads only the declared fields.
"""

from __future__ import annotations

import ctypes
import logging
import mmap
import time
from dataclasses import dataclass

from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)

PHYSICS_MAP_NAME = "Local\\acpmf_physics"
_POLL_INTERVAL_SEC = 0.033   # ~30 Hz
_RETRY_INTERVAL_SEC = 1.5


class SPageFilePhysics(ctypes.Structure):
    """Subset of Kunos's SPageFilePhysics struct.

    Fields are declared in their native order and the natural 4-byte
    alignment matches AC's emit format. We stop after `abs` -- everything
    we need lives above it and downstream fields aren't read.
    """

    _pack_ = 4
    _fields_ = [
        ("packetId", ctypes.c_int32),
        ("gas", ctypes.c_float),
        ("brake", ctypes.c_float),
        ("fuel", ctypes.c_float),
        ("gear", ctypes.c_int32),
        ("rpms", ctypes.c_int32),
        ("steerAngle", ctypes.c_float),
        ("speedKmh", ctypes.c_float),
        ("velocity", ctypes.c_float * 3),
        ("accG", ctypes.c_float * 3),
        ("wheelSlip", ctypes.c_float * 4),
        ("wheelLoad", ctypes.c_float * 4),
        ("wheelsPressure", ctypes.c_float * 4),
        ("wheelAngularSpeed", ctypes.c_float * 4),
        ("tyreWear", ctypes.c_float * 4),
        ("tyreDirtyLevel", ctypes.c_float * 4),
        ("tyreCoreTemperature", ctypes.c_float * 4),
        ("camberRAD", ctypes.c_float * 4),
        ("suspensionTravel", ctypes.c_float * 4),
        ("drs", ctypes.c_float),
        ("tc", ctypes.c_float),
        ("heading", ctypes.c_float),
        ("pitch", ctypes.c_float),
        ("roll", ctypes.c_float),
        ("cgHeight", ctypes.c_float),
        ("carDamage", ctypes.c_float * 5),
        ("numberOfTyresOut", ctypes.c_int32),
        ("pitLimiterOn", ctypes.c_int32),
        ("abs", ctypes.c_float),
    ]


PHYSICS_STRUCT_SIZE = ctypes.sizeof(SPageFilePhysics)
# AC publishes a struct larger than what we declare; map a comfortable
# upper bound so the OS hands us the full page.
_MAP_SIZE = 1024


@dataclass(frozen=True, slots=True)
class PhysicsPacket:
    """Typed snapshot of one shared-memory physics frame."""

    packet_id: int = 0
    fuel: float = 0.0
    tyre_core_temps_c: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)
    tyre_pressures: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)
    tyre_wear: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)
    air_temp_c: float = 0.0  # not in physics; placeholder for future graphics page

    @classmethod
    def from_struct(cls, s: SPageFilePhysics) -> PhysicsPacket:
        return cls(
            packet_id=int(s.packetId),
            fuel=float(s.fuel),
            tyre_core_temps_c=(
                float(s.tyreCoreTemperature[0]),
                float(s.tyreCoreTemperature[1]),
                float(s.tyreCoreTemperature[2]),
                float(s.tyreCoreTemperature[3]),
            ),
            tyre_pressures=(
                float(s.wheelsPressure[0]),
                float(s.wheelsPressure[1]),
                float(s.wheelsPressure[2]),
                float(s.wheelsPressure[3]),
            ),
            tyre_wear=(
                float(s.tyreWear[0]),
                float(s.tyreWear[1]),
                float(s.tyreWear[2]),
                float(s.tyreWear[3]),
            ),
        )


class SharedMemoryReader(QThread):
    """Polls Local\\acpmf_physics and emits PhysicsPacket on every new frame."""

    physics_received = pyqtSignal(object)  # PhysicsPacket
    availability_changed = pyqtSignal(bool)

    def __init__(self) -> None:
        super().__init__()
        self._running = True
        self._mmap: mmap.mmap | None = None
        self._last_packet_id: int = -1
        self._available = False

    def run(self) -> None:
        logger.info(
            "shared-memory reader started (struct=%d B, map=%d B)",
            PHYSICS_STRUCT_SIZE, _MAP_SIZE,
        )

        while self._running:
            if self._mmap is None:
                self._try_open()
                if self._mmap is None:
                    self._sleep(_RETRY_INTERVAL_SEC)
                    continue

            try:
                self._mmap.seek(0)
                raw = self._mmap.read(PHYSICS_STRUCT_SIZE)
            except (ValueError, OSError):
                logger.info("shared-memory read failed -- reopening")
                self._close_mmap()
                self._set_available(False)
                self._sleep(_RETRY_INTERVAL_SEC)
                continue

            if len(raw) != PHYSICS_STRUCT_SIZE:
                self._sleep(_POLL_INTERVAL_SEC)
                continue

            struct = SPageFilePhysics.from_buffer_copy(raw)
            if struct.packetId != self._last_packet_id:
                self._last_packet_id = struct.packetId
                if not self._available:
                    self._set_available(True)
                self.physics_received.emit(PhysicsPacket.from_struct(struct))

            self._sleep(_POLL_INTERVAL_SEC)

        self._close_mmap()

    def _try_open(self) -> None:
        try:
            self._mmap = mmap.mmap(
                -1, _MAP_SIZE, tagname=PHYSICS_MAP_NAME, access=mmap.ACCESS_READ
            )
            logger.debug("opened %s", PHYSICS_MAP_NAME)
        except OSError as exc:
            # Common case: AC not running yet -- silent retry.
            logger.debug("%s not available: %s", PHYSICS_MAP_NAME, exc)
            self._mmap = None

    def _close_mmap(self) -> None:
        if self._mmap is None:
            return
        try:
            self._mmap.close()
        except (ValueError, OSError):
            pass
        finally:
            self._mmap = None
            self._last_packet_id = -1

    def _set_available(self, available: bool) -> None:
        if self._available == available:
            return
        self._available = available
        logger.info("shared-memory %s", "available" if available else "lost")
        self.availability_changed.emit(available)

    def _sleep(self, seconds: float) -> None:
        # Coarse stop responsiveness without a dedicated event primitive.
        deadline = time.monotonic() + seconds
        while self._running:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            time.sleep(min(0.05, remaining))

    def stop(self) -> None:
        self._running = False
        self.quit()
        self.wait()
