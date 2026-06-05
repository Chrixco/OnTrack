# OnTrack — Assetto Corsa Telemetry Dashboard

A real-time telemetry dashboard for Assetto Corsa. PyQt6 desktop app that
speaks AC's built-in UDP remote-telemetry protocol — **no in-game plugin
required**, no AC config edits, no firewall holes for same-machine setups.

## Features

- Speed gauge, RPM bar with shift indicator, gear display
- Throttle / brake input bars plus a rolling 7 s input trace
- Current / best / last lap times with delta vs. best
- G-force ball with trail, lateral / longitudinal read-out
- Tyre core temperatures and fuel level (via AC's shared-memory
  interface, overlaid onto the UDP stream — same-machine only)
- Auto-recorded circuit map with live position dot
- Auto-handshake: starts polling AC every 2 s, connects the moment a
  session begins, reconnects after a session restart
- In-app console (Ctrl+Shift+C) with live values + filterable log
- Dark / light mode, km/h or mph, configurable max RPM

## Architecture

```
OnTrack/
├── pyproject.toml               # Package metadata, deps, entry points
├── ontrack_dashboard/           # Dashboard package (Python 3.10+)
│   ├── __main__.py              # `python -m ontrack_dashboard`
│   ├── main.py                  # Entry point + logging setup
│   ├── app.py                   # QMainWindow + merged-packet dispatch
│   ├── telemetry.py             # AC RTCarInfo binary parser
│   ├── theme.py                 # Colours, fonts, global QSS
│   ├── logging_bridge.py        # In-app console log bus
│   ├── network/
│   │   ├── udp_receiver.py      # AC UDP client (handshake + subscribe)
│   │   └── shared_memory.py     # acpmf_physics reader (tyre temps, fuel)
│   ├── widgets/                 # QPainter-based gauges + cards
│   └── settings/                # Persisted config + settings dialog
└── tests/
    ├── test_telemetry.py        # UDP protocol parser tests (pytest)
    └── test_shared_memory.py    # Shared-memory struct + reader tests
```

## Why no plugin?

AC ships an embedded Python 3.3 interpreter without the `_socket` C
extension, which makes shipping a UDP-broadcasting plugin painful (you
end up vendoring a binary `.pyd` from a long-EOL Python build). AC also
ships a first-party UDP telemetry server on port **9996** that requires
no enablement — sending a 12-byte handshake to that port makes AC start
streaming `RTCarInfo` packets at the simulation frame rate. The
dashboard uses that protocol directly. See `ontrack_dashboard/telemetry.py`
for the byte layout, derived from the canonical Romagnoli/Kunos doc and
cross-checked against
[rickwest/ac-remote-telemetry-client](https://github.com/rickwest/ac-remote-telemetry-client).

The trade-off: `RTCarInfo` doesn't carry tyre temperatures or fuel
level. Those come from AC's first-party shared-memory interface
(`Local\acpmf_physics`), which `network/shared_memory.py` reads in a
parallel thread and overlays onto the UDP stream. Shared memory is
same-machine only, so over the LAN the tyre-temps and fuel read-outs
fall back to their idle state while everything else stays live.

## Install

Python 3.10+ required.

```bash
pip install -e .              # runtime only
pip install -e ".[dev]"       # plus pytest + ruff
```

Run:

```bash
ontrack                       # console script (preferred)
python -m ontrack_dashboard   # module form, identical behaviour
```

## Usage

### Same machine (game + dashboard on the same Windows box)

1. Launch Assetto Corsa, enter a session (any car/track).
2. In another terminal: `ontrack`.
3. Within ~2 s the dashboard handshakes AC and starts receiving frames.

Defaults are `ac_ip = 127.0.0.1`, `ac_port = 9996` — same-machine works
out of the box.

### Across the LAN (game on Windows, dashboard on Mac/Linux)

1. On the Windows machine, find the LAN IP: `ipconfig` → look at the
   IPv4 address of the active adapter (e.g. `192.168.1.50`).
2. On the other machine, run `ontrack`, open **File → Settings**, set
   **AC server IP** to that address, **Apply**.

The dashboard will keep retrying the handshake every two seconds, so it
will auto-connect as soon as AC enters a session.

## Settings

**File → Settings** exposes:

- **AC server IP** — `127.0.0.1` for same-machine, otherwise the LAN IP
  of the box running AC.
- **AC UDP port** — `9996` (don't change unless you know AC has been
  configured otherwise).
- **Max RPM** — calibrates the RPM bar's redline marker.
- **Speed unit** — km/h or mph.
- **Dark mode** — palette toggle.

Settings live at `~/.config/ontrack/settings.json` on all platforms.

## Wire format

AC's remote telemetry uses a tiny custom protocol:

| Direction | Payload | Size |
|---|---|---|
| Client → AC | `<3i`: `(identifier, version, operation)` | 12 B |
| AC → Client (after `op=0`) | Handshake response (4× UTF-16LE strings + 2 ints) | 408 or 808 B |
| AC → Client (after `op=1`) | `RTCarInfo` stream | 328 B / packet |

Operations: `0=HANDSHAKE`, `1=SUBSCRIBE_UPDATE`, `2=SUBSCRIBE_SPOT`,
`3=DISMISS`. The dashboard sends `0` until it sees a handshake reply,
then sends `1` to start the stream, and sends `3` at shutdown.

`RTCarInfo` byte layout (the fields the dashboard actually reads): see
`_RT_CAR_INFO_FMT` in `ontrack_dashboard/telemetry.py:78` — verified
against `RT_CAR_INFO_SIZE == 328`.

## Testing without AC

The protocol layer is fully unit-tested with synthetic byte buffers:

```bash
pip install -e ".[dev]"
pytest
```

25 tests covering the handshake encoder, struct layout sanity, decoding
of all consumed `RTCarInfo` fields, RPM rounding, fields-not-in-protocol
defaulting to zero, packet immutability, rejection of malformed
datagrams, and the shared-memory physics struct (canonical field
offsets + reader sleep behaviour).

## Troubleshooting

**Dashboard logs `UDP receiver listening` then no telemetry arrives.**
That message confirms the socket is up but says nothing about AC. Check:
- AC is *in a session* — handshakes only get a response once the physics
  engine is running (post-loading-screen).
- `ac_ip` matches the box running AC. For same-machine that's
  `127.0.0.1`; the AC machine's own LAN IP also works.
- Nothing else is listening on UDP 9996 on the AC box (other telemetry
  apps can compete for the port).

**Dashboard runs but stays connected to a stale AC session.**
The receiver detects packet timeout after 5 s of silence and drops back
to handshake retries. Just keep it running through your session switch.

**Cross-machine setup not connecting.**
Windows Firewall on the AC machine blocks inbound UDP by default. Allow
`acs.exe` on the Private network profile, or temporarily disable the
firewall on the AC adapter to confirm it's the cause.

## Development notes

- **Python 3.10+** for the dashboard (`from __future__ import
  annotations`, `X | None`, `match`, `tuple[...]` generics in runtime
  contexts).
- **Single source of truth** for the wire format is
  `ontrack_dashboard/telemetry.py`. Widgets consume the typed
  `TelemetryPacket` dataclass; no field-name stringly-typed dict access
  anywhere in the rendering path.
- **Logging** via `logging` (configured in `main.py`); never `print`.
- **Threading** via `QThread`, emitting `pyqtSignal(object)` carrying
  immutable `TelemetryPacket` instances — safe to consume on the GUI
  thread.
- **Lint** via ruff (config in `pyproject.toml`); tests via pytest.

## License

Free to use and modify.
