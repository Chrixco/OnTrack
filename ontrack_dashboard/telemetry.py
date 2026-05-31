"""AC remote-telemetry wire format.

Single source of truth for parsing Assetto Corsa's built-in UDP telemetry
into typed attributes the rest of the dashboard consumes. AC ships a
remote-telemetry protocol that's always on at UDP port 9996 -- a client
must send a 12-byte handshake (3 little-endian int32: identifier, version,
operation), receive an 808-byte response, then send a SUBSCRIBE_UPDATE
operation to start receiving RTCarInfo packets (328 bytes each).

The byte layout below is derived from the canonical Romagnoli/Kunos
documentation and cross-checked against rickwest/ac-remote-telemetry-client
(see https://github.com/rickwest/ac-remote-telemetry-client).

Fields RTCarInfo does NOT carry (tyre temperatures, fuel level) are
exposed as zeros here -- they are only available via AC's shared-memory
interface, which is same-machine only.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field

AC_UDP_PORT = 9996
"""Fixed UDP port AC's telemetry server listens on (no config needed)."""

# --- Handshake -----------------------------------------------------------

# Operation codes for the handshake's third int32.
OP_HANDSHAKE = 0
OP_SUBSCRIBE_UPDATE = 1
OP_SUBSCRIBE_SPOT = 2
OP_DISMISS = 3

class TelemetryError(ValueError):
    """Raised when a UDP datagram cannot be interpreted by this module."""


_HANDSHAKE_FMT = "<3i"
HANDSHAKE_SIZE = struct.calcsize(_HANDSHAKE_FMT)  # 12

# Default values used by the reference rickwest client. AC accepts any
# identifier/version pair; only operation is meaningful.
_HANDSHAKE_IDENTIFIER = 0  # platform id; arbitrary
_HANDSHAKE_VERSION = 1


def build_handshake(operation: int) -> bytes:
    """Build a 12-byte handshake/subscribe/dismiss packet."""
    return struct.pack(
        _HANDSHAKE_FMT, _HANDSHAKE_IDENTIFIER, _HANDSHAKE_VERSION, operation
    )


# Response struct from AC after a HANDSHAKE op:
#   wchar_t carName[N];       // N wchars UTF-16LE
#   wchar_t driverName[N];
#   int     identifier;       // 4
#   int     version;          // 4
#   wchar_t trackName[N];
#   wchar_t trackConfig[N];
# AC's source uses N=50 (408 bytes total); the reference JS client and
# many real packets use N=100 (808 bytes). Both layouts are valid.
_STRING_LEN_408 = 50  # wchars per string for the 408-byte variant
_STRING_LEN_808 = 100
HANDSHAKE_RESPONSE_SIZES = (408, 808)


@dataclass(frozen=True, slots=True)
class SessionInfo:
    """Static session metadata returned by AC's handshake response."""

    car_name: str = ""
    driver_name: str = ""
    track_name: str = ""
    track_config: str = ""

    @classmethod
    def from_handshake(cls, data: bytes) -> SessionInfo:
        if len(data) not in HANDSHAKE_RESPONSE_SIZES:
            raise TelemetryError(
                f"handshake response unexpected size: {len(data)}"
            )

        # Layout:  carName[N] | driverName[N] | identifier(4) | version(4) |
        #          trackName[N] | trackConfig[N]
        # Where N = (len(data) - 8) // 4 bytes (= 50 wchars for 408 B,
        # 100 wchars for 808 B).
        n = (len(data) - 8) // 4
        car_end = n
        drv_end = 2 * n
        track_start = drv_end + 8        # skip identifier + version
        track_end = track_start + n
        cfg_end = track_end + n

        return cls(
            car_name=_decode_wchar(data[0:car_end]),
            driver_name=_decode_wchar(data[car_end:drv_end]),
            track_name=_decode_wchar(data[track_start:track_end]),
            track_config=_decode_wchar(data[track_end:cfg_end]),
        )


def _decode_wchar(buf: bytes) -> str:
    """Decode a fixed-length wchar buffer using AC's wire convention.

    AC's handshake string fields are `wchar_t[50]` (or [100]) buffers
    where Kunos uses '%' as the end-of-string marker (likely a
    `swprintf("%ls%%", ...)` typo). Everything after that '%' is either
    a null pad or, when the slot is otherwise unused (e.g. track_config
    for single-layout tracks), uninitialised stack memory.

    Cut at whichever end-marker appears first -- AC's '%' sentinel or
    the standard C null terminator -- to defend against both AC's quirk
    and any legitimate null-terminated padding.
    """
    try:
        decoded = buf.decode("utf-16-le", errors="replace")
    except UnicodeDecodeError:
        return ""

    pct = decoded.find("%")
    nul = decoded.find("\x00")

    if pct >= 0 and (nul < 0 or pct < nul):
        return decoded[:pct].strip()
    if nul >= 0:
        return decoded[:nul].strip()
    return decoded.strip()


# --- RTCarInfo -----------------------------------------------------------

# Byte layout, verified against rickwest's RTCarInfoParser:
#   0   4s   identifier ('a' + padding)
#   4   i    size
#   8   3f   speedKmh, speedMph, speedMs
#   20  6b   isAbsEnabled, isAbsInAction, isTcInAction, isTcEnabled,
#            isInPit, isEngineLimiterOn
#   26  2x   padding
#   28  3f   accGVertical, accGHorizontal, accGFrontal
#   40  4i   lapTime, lastLap, bestLap, lapCount
#   56  5f   gas, brake, clutch, engineRPM, steer
#   76  i    gear
#   80  f    cgHeight
#   84  4f*14  wheelAngularSpeed, slipAngle, slipAngleContactPatch,
#              slipRatio, tyreSlip, ndSlip, load, Dy, Mz,
#              tyreDirtyLevel, camberRAD, tyreRadius, tyreLoadedRadius,
#              suspensionHeight
#   308 2f   carPositionNormalized, carSlope
#   316 3f   carCoordinates X, Y, Z
_RT_CAR_INFO_FMT = "<4si3f6b2x3f4i5fif" + "4f" * 14 + "2f3f"
RT_CAR_INFO_SIZE = struct.calcsize(_RT_CAR_INFO_FMT)  # 328
assert RT_CAR_INFO_SIZE == 328, "RTCarInfo layout drift -- check the format"

_RT_CAR_INFO_STRUCT = struct.Struct(_RT_CAR_INFO_FMT)


@dataclass(frozen=True, slots=True)
class TelemetryPacket:
    """Immutable snapshot of one frame of car telemetry.

    Field names match the dashboard's existing widget API. Fields not
    carried by AC's RTCarInfo (tyre temps, fuel) default to zero/empty so
    widgets keep rendering without conditional branches.
    """

    speed_kmh: float = 0.0
    rpm: int = 0
    gear: int = 0  # AC convention: 0 = reverse, 1 = neutral, 2.. = forward
    throttle: float = 0.0  # 0..1
    brake: float = 0.0  # 0..1
    fuel: float = 0.0  # not available via RTCarInfo
    lap: int = 0
    lap_time_ms: int = 0
    best_lap_ms: int = 0
    last_lap_ms: int = 0
    tyre_temps_c: tuple[float, float, float, float] = field(
        default=(0.0, 0.0, 0.0, 0.0)
    )  # not available via RTCarInfo
    g_lat: float = 0.0  # accGHorizontal
    g_long: float = 0.0  # accGFrontal
    g_vert: float = 0.0  # accGVertical
    abs_enabled: bool = False
    abs_in_action: bool = False
    tc_enabled: bool = False
    tc_in_action: bool = False
    # World-space position. Y is altitude; we keep it for completeness but
    # the circuit map widget plots X/Z (horizontal plane).
    car_pos_normalized: float = 0.0  # 0..1 around the lap
    car_x: float = 0.0
    car_y: float = 0.0
    car_z: float = 0.0

    @classmethod
    def from_bytes(cls, data: bytes) -> TelemetryPacket:
        """Parse a 328-byte RTCarInfo datagram from AC."""
        if len(data) != RT_CAR_INFO_SIZE:
            raise TelemetryError(
                f"expected {RT_CAR_INFO_SIZE} bytes, got {len(data)}"
            )

        fields = _RT_CAR_INFO_STRUCT.unpack(data)

        identifier_bytes = fields[0]
        # AC stamps RTCarInfo packets with 'a' as the leading byte.
        if not identifier_bytes or identifier_bytes[0:1] != b"a":
            raise TelemetryError(
                f"not an RTCarInfo packet (id={identifier_bytes!r})"
            )

        # Positional unpacking (matches the format string above).
        # 0:identifier  1:size  2-4:speedKmh/Mph/Ms
        # 5:isAbsEnabled  6:isAbsInAction  7:isTcInAction  8:isTcEnabled
        # 9:isInPit  10:isEngineLimiterOn
        # 11-13:accG_vert/horiz/frontal
        # 14-17:lap_t/last/best/count
        # 18-22:gas/brake/clutch/rpm/steer  23:gear  24:cgHeight
        # 25..: wheel arrays (we don't use most of them)
        speed_kmh = fields[2]
        abs_enabled = bool(fields[5])
        abs_in_action = bool(fields[6])
        tc_in_action = bool(fields[7])
        tc_enabled = bool(fields[8])
        acc_g_vertical = fields[11]
        acc_g_horizontal = fields[12]
        acc_g_frontal = fields[13]
        lap_time = fields[14]
        last_lap = fields[15]
        best_lap = fields[16]
        lap_count = fields[17]
        gas = fields[18]
        brake = fields[19]
        engine_rpm = fields[21]
        gear = fields[23]
        # World-space data lives at the tail of the struct:
        #   81: carPositionNormalized  82: carSlope
        #   83..85: carCoordinates X, Y, Z
        car_pos_normalized = fields[81]
        car_x = fields[83]
        car_y = fields[84]
        car_z = fields[85]

        return cls(
            speed_kmh=speed_kmh,
            rpm=int(round(engine_rpm)),
            gear=gear,
            throttle=gas,
            brake=brake,
            lap=lap_count,
            lap_time_ms=lap_time,
            best_lap_ms=best_lap,
            last_lap_ms=last_lap,
            g_lat=acc_g_horizontal,
            g_long=acc_g_frontal,
            g_vert=acc_g_vertical,
            abs_enabled=abs_enabled,
            abs_in_action=abs_in_action,
            tc_enabled=tc_enabled,
            tc_in_action=tc_in_action,
            car_pos_normalized=car_pos_normalized,
            car_x=car_x,
            car_y=car_y,
            car_z=car_z,
        )
