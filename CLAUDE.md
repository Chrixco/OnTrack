# CLAUDE.md — handoff for the next session

OnTrack is a PyQt6 telemetry dashboard for Assetto Corsa. Speaks AC's two
first-party transports directly; no in-game plugin. Read this once before
touching code so you don't relearn the gotchas the hard way.

## Run / test / lint

```bash
pip install -e ".[dev]"     # one-time
ontrack                     # launches the dashboard (or: python -m ontrack_dashboard)
pytest                      # 25 tests, all should be green
python -m ruff check ontrack_dashboard tests
python scripts/monitor.py   # one-shot data audit; --watch for continuous
```

The dashboard logs to **stderr**. The launch helper used during this
session redirects to `dashboard.log` (gitignored). View → Console or
**Ctrl+Shift+C** for the in-app live view.

## Architecture in one screen

```
   Assetto Corsa (Windows)
      │
      ├── UDP port 9996   ────►  UDPReceiver (QThread)
      │     RTCarInfo 328 B           │
      │                               ▼
      │                       TelemetryPacket.from_bytes
      │
      └── Local\acpmf_physics ──►  SharedMemoryReader (QThread)
            SPageFilePhysics              │
                                          ▼
                                  PhysicsPacket.from_struct

                MainWindow._dispatch_merged()
        ── dataclasses.replace(udp, fuel=…, tyre_temps_c=…) ──►
                       widgets paintEvent
```

Two independent transports run in parallel `QThread`s. `MainWindow`
keeps the latest of each and overlays physics-only fields (fuel, tyre
core temps) onto the latest UDP packet before pushing to widgets via
`dataclasses.replace`. Widgets stay oblivious to which transport
supplied which field.

## Critical AC behaviours (each one bit us at least once)

1. **AC's embedded Python 3.3 has no `_socket`.** Means no plugin can
   `import socket` without bundling `_socket.pyd` from a long-EOL build.
   We dropped the plugin entirely in favour of AC's native transports.
   Don't rebuild the plugin path.

2. **UDP handshake is required.** AC won't push anything until the
   client sends `struct.pack('<3i', 0, 1, 0)` (operation 0 = HANDSHAKE)
   to port 9996. After the 408/808-byte response, send op 1
   (SUBSCRIBE_UPDATE). See `network/udp_receiver.py`.

3. **AC handshake strings use `%` as end-of-string marker**, not the C
   null. They're also padded with uninitialised stack memory after the
   terminator. `_decode_wchar` in `telemetry.py` cuts at whichever
   marker comes first (`%` or `\x00`). Regression tests cover both.

4. **Windows raises `ConnectionResetError` on UDP recvfrom** when the
   destination has no listener (ICMP "port unreachable"). We disable
   it with `SIO_UDP_CONNRESET=False` at socket creation AND defensively
   catch `ConnectionResetError` in the recv loop. Without this the
   receiver loop dies the moment AC isn't in a session.

5. **AC allows only one UDP subscriber at a time.** Running the
   dashboard and `scripts/monitor.py` simultaneously means the monitor
   gets zero frames. Stop the dashboard first or use the in-app
   console for live monitoring.

6. **Shared memory persists briefly after AC exits.** Don't assume
   "SHM available" means AC is in a session — `acs.exe` may have
   already quit. Check the process list if confused.

7. **AC sends (0, 0, 0) coordinates during loading screens.** The
   circuit map widget filters these out so the trace doesn't anchor on
   an origin point that never gets driven.

## Repo layout

```
ontrack_dashboard/
├── main.py                 entry point + logging config + LogBus install
├── app.py                  MainWindow, the three-column layout, signal wiring
├── telemetry.py            wire-format types: TelemetryPacket, SessionInfo,
│                           the handshake protocol, RTCarInfo struct fmt
├── theme.py                colors, fonts, GLOBAL_QSS, build_app_palette
├── logging_bridge.py       singleton LogBus + handler for the in-app console
├── network/
│   ├── udp_receiver.py     UDP client (handshake, subscribe, re-handshake)
│   └── shared_memory.py    SPageFilePhysics ctypes struct + reader thread
├── settings/
│   ├── config_manager.py   ~/.config/ontrack/settings.json
│   └── settings_dialog.py
└── widgets/
    ├── card.py             NeumorphCard base (dual paint-time shadows)
    ├── shift_indicator.py  RPM LED strip + gear character
    ├── speed_display.py    big cyan number + half-arc
    ├── acceleration_display.py  G ball with magenta trail
    ├── fuel_display.py     vertical bar, amber number
    ├── pedals_card.py      throttle + brake bars
    ├── input_graph.py      rolling 7s throttle/brake trace
    ├── assists_card.py     ABS + TC pills (off / on / ACTIVE)
    ├── wheel_temps_card.py 2x2 corners, color-coded by temp
    ├── car_info_panel.py   car/driver/track from handshake
    ├── circuit_map_card.py auto-recorded track outline + position dot
    ├── race_stats_panel.py lap counter, current/best/last, delta
    └── console_window.py   in-app log + live values, with filters

tests/                      25 pytest cases (run `pytest -v` for the list)
scripts/monitor.py          standalone CLI audit tool
```

## Conventions

- **Frozen dataclasses with slots** for all wire-format types
  (`TelemetryPacket`, `PhysicsPacket`, `SessionInfo`). Never mutate;
  always construct new ones (use `dataclasses.replace` for overlay).
- **`from __future__ import annotations`** in every module.
- **`logging.getLogger(__name__)`**, never `print`.
- **No type checking framework**, but every public function gets type
  hints. Use `X | None` (PEP 604), `tuple[...]` generics, etc.
  Project is Python 3.10+.
- **Ruff config** in `pyproject.toml` enforces E/F/W/I/B/UP/SIM. Run it
  after any non-trivial change.
- **Widget update signature** is always `def update_data(self, packet:
  TelemetryPacket)`. If a widget needs session metadata
  (`car_name`/`track_name`/etc.), add a separate `set_session(session)`
  method and wire it in `MainWindow.on_session_info`.
- **Painting**: each widget extends `NeumorphCard` and overrides
  `paint_content(painter)`. Use `self.content_rect()` for the drawable
  area inside padding+shadow margins. Use theme constants
  (`ACCENT_CYAN`, `FG_MUTED`, `FONT_LABEL_CAPS`, etc.), never hardcoded
  colors or fonts.

## Data the dashboard receives but doesn't show yet

Available from `TelemetryPacket` but not consumed by any widget:
- `g_vert` (vertical G)
- Most of the RTCarInfo wheel arrays (`slipAngle[4]`, `slipRatio[4]`,
  `tyreSlip[4]`, `ndSlip[4]`, `load[4]`, `Dy[4]`, `Mz[4]`,
  `tyreDirtyLevel[4]`, `camberRAD[4]`, `tyreRadius[4]`,
  `tyreLoadedRadius[4]`, `suspensionHeight[4]`) — we don't unpack them
  past the float slots we use. To consume any of them, extend
  `TelemetryPacket` and update the positional unpack in `from_bytes`.

Available from `PhysicsPacket`:
- `tyre_pressures`, `tyre_wear` — captured, ready to be displayed
- AC's shared memory carries ~80 more physics fields we don't parse
  (suspension travel, damage, heading/pitch/roll, DRS, TC level,
  carDamage[5], etc.). Add to the `SPageFilePhysics` ctypes struct in
  declaration order, then expose via `PhysicsPacket.from_struct`.

## Open work the user mentioned

In rough priority order:

1. **InputGraph button + filters.** The user asked for an action on
   the input-trace card that opens a detail window showing full
   session / last race / last lap, with filters to "improve driving on
   a specific circuit". Probably needs a `SessionRecorder` that
   accumulates samples per lap (detect via `packet.lap` increment),
   stored in `MainWindow`. Then a detail QDialog driven from a "…"
   button on the InputGraph card.

2. **Display tyre pressures / wear.** Both already in
   `PhysicsPacket`. Either extend `WheelTempsCard` to show secondary
   readings on hover/click, or add a separate tyre-detail card.

## How to verify a change works end-to-end

1. `pytest` — must stay green.
2. `python -m ruff check ontrack_dashboard tests` — must say "All
   checks passed!".
3. Launch the app (`ontrack`), open the in-app console
   (Ctrl+Shift+C), watch the Live Values tab + Log tab with AC running
   in a session. Field updates and packet counters prove the change is
   live, not just compiled.
4. If you broke the wire format, `scripts/monitor.py` (with the
   dashboard stopped) shows what the protocol layer actually decodes.

## Don't do these

- **Don't rebuild the plugin.** It can't work without vendoring
  `_socket.pyd`, and we deliberately went a different route. See
  `feedback-ac-python-plugins` memory.
- **Don't add per-widget visibility toggles to settings.** The curated
  layout is intentional; the old `show_speed` / `show_rpm` flags were
  removed when we restructured.
- **Don't print to stdout/stderr.** Use `logging.getLogger(__name__)`
  so the in-app console captures it.
- **Don't hardcode colors or fonts.** Use the theme constants.
- **Don't force-push without `--force-with-lease`.** When pushing to
  a divergent main, see the `feedback-ontrack-push` memory for the
  established workflow.
- **Don't let an exception escape a `QThread.run()`.** An unhandled
  exception in a reader thread's `run()` aborts the whole process — the
  window just vanishes with a traceback on stderr, no dialog. The SHM
  reader's `_sleep` once handed a negative duration to `time.sleep`
  (clock slipped past the deadline mid-loop) and took the app down on a
  track reload (mugello → ks_vallelunga). Now fixed by clamping the
  remaining time; regression test in `tests/test_shared_memory.py`
  (`test_sleep_never_passes_negative_to_time_sleep`). Guard loop bodies
  and clamp any computed sleep/timeout you pass into stdlib calls.

## Useful one-liners

```powershell
# What's actually in dashboard.log right now
Get-Content C:\Users\chris\Documents\Github\OnTrack\dashboard.log

# Force-read AC's log even when it shows 0 bytes (Windows open-file lock)
$log = "$env:USERPROFILE\Documents\Assetto Corsa\logs\py_log.txt"
$fs = [System.IO.File]::Open($log,'Open','Read','ReadWrite')
(New-Object System.IO.StreamReader($fs)).ReadToEnd(); $fs.Close()

# Is AC in a session right now?
Get-Process | ? { $_.ProcessName -in @('acs','AssettoCorsa') }

# What's on UDP 20777/9996?
netstat -ano -p UDP | Select-String "9996|20777"
```
