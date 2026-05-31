#!/usr/bin/env python3
"""Live monitor of what's actually flowing from AC into the dashboard.

Runs standalone -- no Qt window, no GUI. Connects to both transports the
same way the dashboard does:

  * UDP: sends a handshake to AC's port 9996, reads N RTCarInfo frames,
    decodes them with the same TelemetryPacket parser the widgets use.
  * Shared memory: opens Local\\acpmf_physics, reads one frame, decodes
    it via the same PhysicsPacket parser.

Then prints a side-by-side report mapping every field to the widget(s)
that consume it. Use this to answer "what is the app actually getting
from AC and where does it go?".

Usage:
    python scripts/monitor.py             # one shot
    python scripts/monitor.py --watch     # stream live values continuously
"""

from __future__ import annotations

import argparse
import socket
import sys
import time
from typing import Optional

from ontrack_dashboard.network.shared_memory import (
    PHYSICS_STRUCT_SIZE,
    PhysicsPacket,
    SPageFilePhysics,
)
from ontrack_dashboard.telemetry import (
    AC_UDP_PORT,
    HANDSHAKE_RESPONSE_SIZES,
    OP_HANDSHAKE,
    OP_SUBSCRIBE_UPDATE,
    RT_CAR_INFO_SIZE,
    SessionInfo,
    TelemetryError,
    TelemetryPacket,
    build_handshake,
)


# Field -> (source, consumer widgets, units / interpretation).
FIELD_MAP = {
    # --- UDP fields ---
    "speed_kmh":    ("UDP",      "SpeedDisplay (center middle)",            "km/h"),
    "rpm":          ("UDP",      "ShiftIndicator (LED strip + label)",      "rpm"),
    "gear":         ("UDP",      "ShiftIndicator (gear character)",         "0=R 1=N 2..=fwd"),
    "throttle":     ("UDP",      "PedalsCard, InputGraph (lime curve)",     "0..1"),
    "brake":        ("UDP",      "PedalsCard, InputGraph (red curve)",      "0..1"),
    "lap":          ("UDP",      "RaceStatsPanel (LAP counter)",            "n"),
    "lap_time_ms":  ("UDP",      "RaceStatsPanel (CURRENT)",                "ms"),
    "best_lap_ms":  ("UDP",      "RaceStatsPanel (BEST)",                   "ms"),
    "last_lap_ms":  ("UDP",      "RaceStatsPanel (LAST + delta)",           "ms"),
    "g_lat":        ("UDP",      "AccelerationDisplay (horizontal axis)",   "G"),
    "g_long":       ("UDP",      "AccelerationDisplay (vertical axis)",     "G"),
    "g_vert":       ("UDP",      "(not visualised)",                        "G"),
    "abs_enabled":  ("UDP",      "AssistsCard (ABS pill 'on'/dim)",         "bool"),
    "abs_in_action":("UDP",      "AssistsCard (ABS pill 'ACTIVE'/glow)",    "bool"),
    "tc_enabled":   ("UDP",      "AssistsCard (TC pill 'on'/dim)",          "bool"),
    "tc_in_action": ("UDP",      "AssistsCard (TC pill 'ACTIVE'/glow)",     "bool"),
    # --- Physics-merged fields ---
    "fuel":         ("SHM",      "FuelDisplay (big number + bar)",          "L"),
    "tyre_core_temps_c": ("SHM", "WheelTempsCard (2x2 cells, blue->red)",   "C / corner"),
    # --- Session ---
    "car_name":     ("UDP-hs",   "CarInfoPanel (CAR row)",                  "string"),
    "driver_name":  ("UDP-hs",   "CarInfoPanel (DRIVER row)",               "string"),
    "track_name":   ("UDP-hs",   "CarInfoPanel (TRACK row)",                "string"),
    "track_config": ("UDP-hs",   "CarInfoPanel (CONFIG row)",               "string"),
    # --- Available from SHM but not currently rendered ---
    "tyre_pressures":("SHM",     "(captured, not yet displayed)",           "psi / corner"),
    "tyre_wear":    ("SHM",      "(captured, not yet displayed)",           "0..1 / corner"),
}


# --- UDP client (minimal version of UDPReceiver, blocking) -----------------

def udp_collect(
    ac_ip: str = "127.0.0.1",
    ac_port: int = AC_UDP_PORT,
    frames: int = 1,
    timeout: float = 4.0,
) -> tuple[Optional[SessionInfo], list[TelemetryPacket]]:
    """Handshake + subscribe + collect N RTCarInfo frames."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    if hasattr(socket, "SIO_UDP_CONNRESET"):
        sock.ioctl(socket.SIO_UDP_CONNRESET, False)
    # Short per-recv timeout so we keep retrying within the overall budget.
    sock.settimeout(0.4)

    session: Optional[SessionInfo] = None
    packets: list[TelemetryPacket] = []
    subscribed = False
    last_handshake_at = 0.0
    deadline = time.monotonic() + timeout + frames * 0.5

    try:
        while time.monotonic() < deadline and len(packets) < frames:
            # Resend handshake periodically until we get a response.
            if not subscribed and time.monotonic() - last_handshake_at > 1.5:
                sock.sendto(build_handshake(OP_HANDSHAKE), (ac_ip, ac_port))
                last_handshake_at = time.monotonic()

            try:
                data, _ = sock.recvfrom(4096)
            except (TimeoutError, ConnectionResetError):
                continue
            size = len(data)
            if size in HANDSHAKE_RESPONSE_SIZES:
                try:
                    session = SessionInfo.from_handshake(data)
                except TelemetryError:
                    pass
                if not subscribed:
                    sock.sendto(build_handshake(OP_SUBSCRIBE_UPDATE), (ac_ip, ac_port))
                    subscribed = True
            elif size == RT_CAR_INFO_SIZE:
                try:
                    packets.append(TelemetryPacket.from_bytes(data))
                except TelemetryError:
                    pass
    finally:
        sock.close()
    return session, packets


# --- Shared memory reader (one-shot) --------------------------------------

def shm_collect() -> Optional[PhysicsPacket]:
    import mmap
    try:
        with mmap.mmap(
            -1, max(PHYSICS_STRUCT_SIZE, 1024),
            tagname="Local\\acpmf_physics",
            access=mmap.ACCESS_READ,
        ) as mm:
            mm.seek(0)
            raw = mm.read(PHYSICS_STRUCT_SIZE)
            if len(raw) != PHYSICS_STRUCT_SIZE:
                return None
            return PhysicsPacket.from_struct(SPageFilePhysics.from_buffer_copy(raw))
    except OSError:
        return None


# --- Pretty printing -------------------------------------------------------

_GROUPS = [
    ("UDP RTCarInfo", "UDP", [
        "speed_kmh", "rpm", "gear", "throttle", "brake",
        "lap", "lap_time_ms", "best_lap_ms", "last_lap_ms",
        "g_lat", "g_long", "g_vert",
        "abs_enabled", "abs_in_action", "tc_enabled", "tc_in_action",
    ]),
    ("Shared memory physics", "SHM", [
        "fuel", "tyre_core_temps_c", "tyre_pressures", "tyre_wear",
    ]),
    ("UDP handshake", "UDP-hs", [
        "car_name", "driver_name", "track_name", "track_config",
    ]),
]


def _fmt(value) -> str:
    if isinstance(value, tuple) and len(value) == 4:
        return "(" + " ".join(f"{v:.2f}" for v in value) + ")"
    if isinstance(value, float):
        return f"{value:.3f}"
    if isinstance(value, str):
        return value if value else "(empty)"
    return str(value)


def print_report(
    session: Optional[SessionInfo],
    packets: list[TelemetryPacket],
    physics: Optional[PhysicsPacket],
) -> None:
    print()
    print("=" * 84)
    print("OnTrack data audit -- what AC sends, what each widget uses")
    print("=" * 84)
    print(f"UDP frames captured: {len(packets)}    SHM physics frame: "
          f"{'yes' if physics else 'no'}    Handshake: {'yes' if session else 'no'}")
    print()

    packet = packets[-1] if packets else TelemetryPacket()
    if physics is None:
        physics = PhysicsPacket()

    sources = {
        "UDP": packet,
        "SHM": physics,
        "UDP-hs": session or SessionInfo(),
    }

    for group_label, source_tag, fields in _GROUPS:
        obj = sources[source_tag]
        print(f"-- {group_label} ({source_tag}) " + "-" * (60 - len(group_label) - len(source_tag)))
        for field in fields:
            if not hasattr(obj, field):
                continue
            value = getattr(obj, field)
            info = FIELD_MAP.get(field, ("?", "?", ""))
            print(
                f"  {field:<20s} {_fmt(value):<26s}"
                f"  -> {info[1]} [{info[2]}]"
            )
        print()


# --- CLI -------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ip", default="127.0.0.1", help="AC server IP")
    parser.add_argument("--port", type=int, default=AC_UDP_PORT, help="AC UDP port")
    parser.add_argument("--frames", type=int, default=1, help="RTCarInfo frames to grab")
    parser.add_argument("--watch", action="store_true",
                        help="loop indefinitely (~2 Hz refresh)")
    args = parser.parse_args()

    if not args.watch:
        session, packets = udp_collect(args.ip, args.port, args.frames)
        physics = shm_collect()
        print_report(session, packets, physics)
        return 0

    print("watching -- Ctrl+C to stop")
    last_session: Optional[SessionInfo] = None
    try:
        while True:
            session, packets = udp_collect(args.ip, args.port, frames=1, timeout=1.0)
            physics = shm_collect()
            if session:
                last_session = session
            # Clear screen on each refresh for a "top"-style view.
            sys.stdout.write("\x1b[2J\x1b[H")
            print_report(last_session, packets, physics)
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nstopped.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
