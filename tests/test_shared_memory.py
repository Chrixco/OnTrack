"""Tests for the shared-memory physics layer.

These tests don't require Assetto Corsa or Windows -- they construct an
SPageFilePhysics struct in memory, feed it to PhysicsPacket.from_struct,
and verify the field mapping.

Critical: the byte offsets of the fields we read must match Kunos's
canonical layout. If AC ever reorders or inserts a field, the assertions
below catch it before we ever see garbage tyre temperatures live.
"""

from __future__ import annotations

import ctypes

import pytest

from ontrack_dashboard.network import shared_memory
from ontrack_dashboard.network.shared_memory import (
    PHYSICS_STRUCT_SIZE,
    PhysicsPacket,
    SPageFilePhysics,
)

# Canonical offsets from the Kunos SDK header. If any of these change,
# AC has revised the wire format and we need to update the struct.
_CANONICAL_OFFSETS = {
    "packetId": 0,
    "gas": 4,
    "brake": 8,
    "fuel": 12,
    "gear": 16,
    "rpms": 20,
    "speedKmh": 28,
    "tyreCoreTemperature": 152,
    "abs": 252,
}


def test_canonical_field_offsets() -> None:
    for name, expected in _CANONICAL_OFFSETS.items():
        actual = getattr(SPageFilePhysics, name).offset
        assert actual == expected, (
            f"{name} offset drift: expected {expected}, got {actual}"
        )


def test_struct_size_covers_all_declared_fields() -> None:
    # Last declared field is `abs` at offset 252 + 4 bytes -> 256.
    assert PHYSICS_STRUCT_SIZE >= 256


def test_from_struct_reads_fuel_and_tyre_temps() -> None:
    s = SPageFilePhysics()
    s.packetId = 42
    s.fuel = 33.5
    s.tyreCoreTemperature[0] = 78.0
    s.tyreCoreTemperature[1] = 81.2
    s.tyreCoreTemperature[2] = 76.9
    s.tyreCoreTemperature[3] = 80.4
    s.wheelsPressure[0] = 27.5
    s.wheelsPressure[1] = 27.5
    s.wheelsPressure[2] = 26.0
    s.wheelsPressure[3] = 26.0
    s.tyreWear[0] = 0.98
    s.tyreWear[1] = 0.97
    s.tyreWear[2] = 0.99
    s.tyreWear[3] = 0.99

    packet = PhysicsPacket.from_struct(s)

    assert packet.packet_id == 42
    assert packet.fuel == pytest.approx(33.5)
    # c_float is 32-bit so the round-trip introduces tiny imprecision.
    assert packet.tyre_core_temps_c == pytest.approx((78.0, 81.2, 76.9, 80.4))
    assert packet.tyre_pressures == pytest.approx((27.5, 27.5, 26.0, 26.0))
    assert packet.tyre_wear[0] > 0.96


def test_from_struct_decodes_buffer_round_trip() -> None:
    """Pack a struct to bytes, decode back, and check fields survived."""
    s = SPageFilePhysics()
    s.fuel = 12.5
    s.tyreCoreTemperature[2] = 99.9

    raw = bytes(ctypes.string_at(ctypes.byref(s), PHYSICS_STRUCT_SIZE))
    assert len(raw) == PHYSICS_STRUCT_SIZE

    decoded = SPageFilePhysics.from_buffer_copy(raw)
    packet = PhysicsPacket.from_struct(decoded)
    assert packet.fuel == pytest.approx(12.5)
    assert packet.tyre_core_temps_c[2] == pytest.approx(99.9)


def test_packet_immutable() -> None:
    packet = PhysicsPacket()
    with pytest.raises((AttributeError, TypeError)):
        packet.fuel = 99.0  # type: ignore[misc]


def test_sleep_never_passes_negative_to_time_sleep(monkeypatch) -> None:
    """Regression: the poll-sleep crashed the reader thread when the clock
    advanced past the deadline between the loop check and the sleep call,
    yielding `time.sleep(<negative>)` -> ValueError. Reproduced live on an
    AC track reload (mugello -> ks_vallelunga). The helper must clamp the
    remaining time and never hand a negative value to time.sleep.
    """
    # Bypass QThread.__init__ -- _sleep only touches self._running + time.
    reader = shared_memory.SharedMemoryReader.__new__(
        shared_memory.SharedMemoryReader
    )
    reader._running = True

    # Adversarial clock: deadline = 100.0 + 0.05 = 100.05. The second tick
    # is just under the deadline; the third slips just past it -- exactly
    # the race that produced a negative remaining time.
    ticks = iter([100.0, 100.049, 100.051, 100.2])
    monkeypatch.setattr(shared_memory.time, "monotonic", lambda: next(ticks))

    slept: list[float] = []

    def fake_sleep(seconds: float) -> None:
        assert seconds >= 0, f"time.sleep got negative value {seconds}"
        slept.append(seconds)

    monkeypatch.setattr(shared_memory.time, "sleep", fake_sleep)

    reader._sleep(0.05)  # must return cleanly, never raise

    assert slept and all(s >= 0 for s in slept)
