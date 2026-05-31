"""Tests for the AC RTCarInfo binary telemetry parser.

These run without PyQt6 -- they exercise the protocol layer in isolation
so wire-format bugs surface without needing a GUI or a live AC session.
"""

from __future__ import annotations

import struct

import pytest

from ontrack_dashboard.telemetry import (
    HANDSHAKE_SIZE,
    OP_DISMISS,
    OP_HANDSHAKE,
    OP_SUBSCRIBE_UPDATE,
    RT_CAR_INFO_SIZE,
    SessionInfo,
    TelemetryError,
    TelemetryPacket,
    build_handshake,
)


def _build_rt_car_info(
    speed_kmh: float = 0.0,
    speed_mph: float = 0.0,
    speed_ms: float = 0.0,
    acc_g_vert: float = 0.0,
    acc_g_horiz: float = 0.0,
    acc_g_front: float = 0.0,
    lap_time: int = 0,
    last_lap: int = 0,
    best_lap: int = 0,
    lap_count: int = 0,
    gas: float = 0.0,
    brake: float = 0.0,
    clutch: float = 0.0,
    engine_rpm: float = 0.0,
    steer: float = 0.0,
    gear: int = 0,
    cg_height: float = 0.0,
    identifier: bytes = b"a\x00\x00\x00",
    abs_enabled: int = 0,
    abs_in_action: int = 0,
    tc_in_action: int = 0,
    tc_enabled: int = 0,
    is_in_pit: int = 0,
    is_engine_limiter_on: int = 0,
) -> bytes:
    """Pack a synthetic 328-byte RTCarInfo datagram for tests.

    Wheel-array tail (224 bytes) and trailing pos/coord fields (20 bytes)
    are left zero -- the parser ignores them today so the values don't
    matter, but we still send the full struct so the size check passes.
    """
    head = struct.pack(
        "<4si3f6b2x3f4i5fif",
        identifier,
        328,  # size field (informational; parser doesn't validate it)
        speed_kmh, speed_mph, speed_ms,
        abs_enabled, abs_in_action, tc_in_action, tc_enabled,
        is_in_pit, is_engine_limiter_on,
        acc_g_vert, acc_g_horiz, acc_g_front,
        lap_time, last_lap, best_lap, lap_count,
        gas, brake, clutch, engine_rpm, steer,
        gear,
        cg_height,
    )
    tail = b"\x00" * (RT_CAR_INFO_SIZE - len(head))
    return head + tail


# --- Handshake -----------------------------------------------------------


def test_handshake_is_twelve_bytes() -> None:
    assert HANDSHAKE_SIZE == 12


def test_build_handshake_encodes_operation() -> None:
    pkt = build_handshake(OP_SUBSCRIBE_UPDATE)
    assert len(pkt) == 12
    ident, version, op = struct.unpack("<3i", pkt)
    assert op == OP_SUBSCRIBE_UPDATE


def test_each_operation_round_trips() -> None:
    for op in (OP_HANDSHAKE, OP_SUBSCRIBE_UPDATE, OP_DISMISS):
        _, _, decoded = struct.unpack("<3i", build_handshake(op))
        assert decoded == op


# --- RTCarInfo struct sanity --------------------------------------------


def test_rt_car_info_layout_size_is_328() -> None:
    assert RT_CAR_INFO_SIZE == 328


def test_synthetic_packet_is_full_size() -> None:
    assert len(_build_rt_car_info()) == RT_CAR_INFO_SIZE


# --- TelemetryPacket.from_bytes -----------------------------------------


def test_from_bytes_decodes_basic_fields() -> None:
    data = _build_rt_car_info(
        speed_kmh=142.7,
        engine_rpm=6800.4,
        gear=4,
        gas=0.82,
        brake=0.05,
        lap_time=87432,
        last_lap=86890,
        best_lap=85120,
        lap_count=3,
        acc_g_vert=0.02,
        acc_g_horiz=-0.12,
        acc_g_front=1.43,
    )
    packet = TelemetryPacket.from_bytes(data)
    assert packet.speed_kmh == pytest.approx(142.7, rel=1e-4)
    assert packet.rpm == 6800
    assert packet.gear == 4
    assert packet.throttle == pytest.approx(0.82, rel=1e-4)
    assert packet.brake == pytest.approx(0.05, rel=1e-4)
    assert packet.lap == 3
    assert packet.lap_time_ms == 87432
    assert packet.last_lap_ms == 86890
    assert packet.best_lap_ms == 85120
    assert packet.g_lat == pytest.approx(-0.12, rel=1e-4)
    assert packet.g_long == pytest.approx(1.43, rel=1e-4)
    assert packet.g_vert == pytest.approx(0.02, rel=1e-4)


def test_from_bytes_rpm_is_rounded_to_int() -> None:
    packet = TelemetryPacket.from_bytes(_build_rt_car_info(engine_rpm=6800.7))
    assert packet.rpm == 6801


def test_from_bytes_fields_not_in_rt_car_info_are_zero() -> None:
    packet = TelemetryPacket.from_bytes(_build_rt_car_info(speed_kmh=120.0))
    # Fuel and tyre temps are not carried by RTCarInfo, so they stay zero.
    assert packet.fuel == 0.0
    assert packet.tyre_temps_c == (0.0, 0.0, 0.0, 0.0)


def test_from_bytes_rejects_wrong_size() -> None:
    with pytest.raises(TelemetryError):
        TelemetryPacket.from_bytes(b"\x00" * 100)


def test_from_bytes_rejects_wrong_identifier() -> None:
    bad = _build_rt_car_info(identifier=b"X\x00\x00\x00")
    with pytest.raises(TelemetryError):
        TelemetryPacket.from_bytes(bad)


def test_packet_is_immutable() -> None:
    packet = TelemetryPacket.from_bytes(_build_rt_car_info(engine_rpm=5000.0))
    with pytest.raises((AttributeError, TypeError)):
        packet.rpm = 9000  # type: ignore[misc]


def _build_handshake_response(
    car: str = "", driver: str = "", track: str = "", config: str = "",
    *, n_wchars: int = 50,
) -> bytes:
    """Pack a synthetic handshake response.

    Layout:  car[n] | driver[n] | identifier(i32) | version(i32) | track[n] | config[n]
    Strings are UTF-16LE, padded with nulls.
    """
    def s(value: str) -> bytes:
        encoded = value.encode("utf-16-le")
        return encoded + b"\x00" * (n_wchars * 2 - len(encoded))

    return (
        s(car)
        + s(driver)
        + struct.pack("<i", 4242)
        + struct.pack("<i", 1)
        + s(track)
        + s(config)
    )


def test_session_info_parses_408_byte_handshake() -> None:
    data = _build_handshake_response(
        car="mercedes_sls",
        driver="Chrixco",
        track="mugello",
        config="Layout A",
        n_wchars=50,
    )
    assert len(data) == 408
    info = SessionInfo.from_handshake(data)
    assert info.car_name == "mercedes_sls"
    assert info.driver_name == "Chrixco"
    assert info.track_name == "mugello"
    assert info.track_config == "Layout A"


def test_session_info_parses_808_byte_handshake() -> None:
    data = _build_handshake_response(
        car="ferrari_488", driver="A", track="spa", config="",
        n_wchars=100,
    )
    assert len(data) == 808
    info = SessionInfo.from_handshake(data)
    assert info.car_name == "ferrari_488"
    assert info.track_name == "spa"


def test_session_info_rejects_wrong_size() -> None:
    with pytest.raises(TelemetryError):
        SessionInfo.from_handshake(b"\x00" * 100)


def test_session_info_strips_trailing_percent_quirk() -> None:
    """AC uses '%' as the end-of-string marker in handshake fields.

    Verified live against a real AC session -- the raw bytes for the
    car field were 'mercedes_sls%\\0...'. We cut at the '%' so the UI
    shows the actual name.
    """
    def s(value: str, n_wchars: int = 50) -> bytes:
        encoded = (value + "%").encode("utf-16-le") + b"\x00\x00"
        return encoded + b"\x00" * (n_wchars * 2 - len(encoded))

    data = (
        s("mercedes_sls")
        + s("Chrixco")
        + struct.pack("<i", 4242) + struct.pack("<i", 1)
        + s("mugello")
        + s("Layout A")
    )
    assert len(data) == 408

    info = SessionInfo.from_handshake(data)
    assert info.car_name == "mercedes_sls"
    assert info.driver_name == "Chrixco"
    assert info.track_name == "mugello"
    assert info.track_config == "Layout A"


def test_session_info_handles_garbage_after_percent_marker() -> None:
    """track_config on single-layout tracks contains 'mugello%' + stack
    garbage before any null terminator. We must still cut cleanly at '%'.
    """
    n_wchars = 50

    def field(prefix: str, garbage: bytes = b"") -> bytes:
        # prefix + '%' + garbage + nulls to fill the slot
        head = (prefix + "%").encode("utf-16-le") + garbage
        return head + b"\x00" * (n_wchars * 2 - len(head))

    data = (
        field("mercedes_sls")
        + field("Chrixco")
        + struct.pack("<i", 4242) + struct.pack("<i", 1)
        + field("mugello")
        # track_config: same prefix as track, then arbitrary non-null bytes
        + field("mugello", b"\xdc\xb6\x59\x5f\x7f\x3f\x91\x9c\x6e\x4a")
    )
    assert len(data) == 408

    info = SessionInfo.from_handshake(data)
    assert info.car_name == "mercedes_sls"
    assert info.track_name == "mugello"
    # Garbage after the '%' marker must not leak into track_config
    assert info.track_config == "mugello"


def test_session_info_strips_uninitialised_buffer_tail() -> None:
    """AC pads handshake string fields with uninitialised memory after
    the null terminator -- decoded text must stop at the first \\x00."""

    def s_with_garbage(value: str, garbage: bytes, n_wchars: int = 50) -> bytes:
        encoded = value.encode("utf-16-le") + b"\x00\x00"  # explicit terminator
        # Fill the rest with arbitrary non-null bytes
        padding = (b"\x25\x00" * n_wchars)[: n_wchars * 2 - len(encoded)]
        return encoded + padding + garbage[: 0]  # keep total = n_wchars*2

    car = s_with_garbage("mercedes_sls", b"")
    driver = s_with_garbage("Chrixco", b"")
    track = s_with_garbage("mugello", b"")
    config = s_with_garbage("Layout A", b"")
    data = (
        car + driver
        + struct.pack("<i", 4242) + struct.pack("<i", 1)
        + track + config
    )
    assert len(data) == 408

    info = SessionInfo.from_handshake(data)
    assert info.car_name == "mercedes_sls"
    assert info.driver_name == "Chrixco"
    assert info.track_name == "mugello"
    assert info.track_config == "Layout A"


def test_from_bytes_decodes_car_coordinates() -> None:
    """carCoordinates live at the very tail of the 328-byte struct."""
    base = _build_rt_car_info()  # zeros for tail
    # Patch carPositionNormalized (offset 308) and carCoordinates (316..324).
    patched = bytearray(base)
    patched[308:312] = struct.pack("<f", 0.42)   # carPositionNormalized
    patched[316:320] = struct.pack("<f", 123.5)  # carCoordinates X
    patched[320:324] = struct.pack("<f", 1.25)   # carCoordinates Y
    patched[324:328] = struct.pack("<f", -67.8)  # carCoordinates Z

    packet = TelemetryPacket.from_bytes(bytes(patched))
    assert packet.car_pos_normalized == pytest.approx(0.42, rel=1e-4)
    assert packet.car_x == pytest.approx(123.5, rel=1e-4)
    assert packet.car_y == pytest.approx(1.25, rel=1e-4)
    assert packet.car_z == pytest.approx(-67.8, rel=1e-4)


def test_from_bytes_decodes_abs_and_tc() -> None:
    packet = TelemetryPacket.from_bytes(_build_rt_car_info(
        abs_enabled=1, abs_in_action=0, tc_enabled=1, tc_in_action=1,
    ))
    assert packet.abs_enabled is True
    assert packet.abs_in_action is False
    assert packet.tc_enabled is True
    assert packet.tc_in_action is True

    packet = TelemetryPacket.from_bytes(_build_rt_car_info())
    assert packet.abs_enabled is False
    assert packet.tc_enabled is False
