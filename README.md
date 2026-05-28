# OnTrack — Assetto Corsa Telemetry Dashboard

A comprehensive real-time telemetry dashboard for Assetto Corsa consisting of an in-game Python plugin and an external PyQt6 dashboard application.

## Features

- **Real-time Telemetry Display**
  - Speed gauge with analog needle
  - RPM bar with shift indicator
  - Throttle and brake input visualization
  - Current/best/last lap times with delta coloring
  - Gear display (R/N/1-9)
  - Tire temperature monitoring with color-coded temps

- **Network Communication**
  - Plugin broadcasts UDP packets at ~30Hz
  - Dashboard receives UDP on configurable IP/port
  - Works across machines (game on Windows, dashboard on Mac, etc.)

- **Customizable Settings**
  - UDP IP and port configuration
  - Dark/light mode toggle
  - Per-widget visibility controls
  - Speed unit selection (km/h or mph)
  - Max RPM calibration

## Architecture

```
OnTrack/
├── game_plugin/              # Assetto Corsa in-game plugin
│   ├── OnTrack.py            # Main plugin (Python 3.3)
│   ├── OnTrack.ini           # AC app metadata
│   ├── config.py             # Config reader
│   └── config.ini            # User settings
└── dashboard/                # External dashboard application
    ├── main.py               # Entry point
    ├── app.py                # Main window
    ├── requirements.txt      # Python dependencies
    ├── widgets/              # Display widgets
    │   ├── speed_gauge.py    # Analog speed gauge
    │   ├── rpm_bar.py        # RPM bar with shift light
    │   ├── pedals.py         # Throttle/brake bars
    │   ├── lap_times.py      # Lap time display
    │   ├── gear_display.py   # Gear number display
    │   └── tire_temps.py     # Tire temperature display
    ├── settings/             # Configuration
    │   ├── config_manager.py # Settings file I/O
    │   └── settings_dialog.py# Settings GUI
    └── network/              # Networking
        └── udp_receiver.py   # UDP listener thread
```

## Installation & Setup

### Game Plugin Setup (Windows - Assetto Corsa)

1. Copy the `game_plugin` folder to your Assetto Corsa installation:
   ```
   C:\Program Files (x86)\Steam\steamapps\common\assettocorsa\apps\python\OnTrack\
   ```

2. The folder should contain:
   - `OnTrack.py`
   - `OnTrack.ini`
   - `config.py`
   - `config.ini`

3. Launch AC, go to **Options → UI Modules** and enable "OnTrack"

4. (Optional) Edit `config.ini` to change UDP target IP/port:
   ```ini
   [UDP]
   ip = 192.168.1.100    # IP of machine running the dashboard
   port = 20777
   
   [GENERAL]
   update_rate_hz = 30
   ```

### Dashboard Setup (macOS/Windows/Linux)

1. Install Python 3.8+ (if not already installed)

2. Install dependencies:
   ```bash
   cd dashboard
   pip install -r requirements.txt
   ```

3. Run the dashboard:
   ```bash
   python main.py
   ```

## Usage

### Same Machine (Game + Dashboard on Windows)

1. In `game_plugin/config.ini`, set:
   ```ini
   [UDP]
   ip = 127.0.0.1
   port = 20777
   ```

2. Launch AC and enable the OnTrack plugin

3. Run the dashboard: `python main.py`

### Across Network (Game on Windows, Dashboard on macOS)

1. Find your macOS machine's local IP (e.g., `192.168.1.50`):
   ```bash
   ifconfig | grep "inet " | grep -v 127.0.0.1
   ```

2. In `game_plugin/config.ini`, set:
   ```ini
   [UDP]
   ip = 192.168.1.50
   port = 20777
   ```

3. Launch AC and enable the OnTrack plugin

4. On macOS, run the dashboard: `python main.py`

### Configuration

Open **File → Settings** in the dashboard to:

- **UDP Binding**: Set the IP and port the dashboard listens on
  - `0.0.0.0` = listen on all interfaces (default)
  - `127.0.0.1` = only localhost
  - `192.168.x.x` = specific interface

- **Display Settings**:
  - Max RPM (for gauge calibration)
  - Speed unit (km/h or mph)
  - Dark mode toggle

- **Widget Visibility**: Show/hide individual widgets

## UDP Packet Format

The plugin broadcasts JSON packets every frame. Example:

```json
{
  "v": 1,
  "spd": 142.7,
  "rpm": 6800,
  "gear": 4,
  "thr": 0.82,
  "brk": 0.0,
  "fuel": 34.2,
  "lap": 3,
  "lap_t": 87432,
  "best_t": 85120,
  "last_t": 86890,
  "tyre": [78.2, 79.1, 81.4, 80.0],
  "gx": -0.12,
  "gy": 1.43,
  "gz": 0.02
}
```

**Field Reference:**
- `v`: Protocol version (for future compatibility)
- `spd`: Speed in km/h
- `rpm`: Engine RPM
- `gear`: 0=Reverse, 1=Neutral, 2+=Gears
- `thr`: Throttle input (0.0–1.0)
- `brk`: Brake input (0.0–1.0)
- `fuel`: Fuel remaining (liters)
- `lap`: Current lap number
- `lap_t`: Current lap time (ms)
- `best_t`: Best lap time (ms)
- `last_t`: Last lap time (ms)
- `tyre`: [FL, FR, RL, RR] tire temps (°C)
- `gx`, `gy`, `gz`: G-forces (lateral, longitudinal, vertical)

## Testing Without Game

Test the dashboard without AC running:

```bash
# Terminal 1: Start the dashboard
cd dashboard
python main.py

# Terminal 2: Send test UDP packets
python3 -c "
import socket
import json
import time

data = {
    'v': 1, 'spd': 150, 'rpm': 7000, 'gear': 4,
    'thr': 0.8, 'brk': 0.0, 'fuel': 30,
    'lap': 2, 'lap_t': 87000, 'best_t': 85000, 'last_t': 86000,
    'tyre': [80, 82, 78, 79], 'gx': -0.5, 'gy': 1.2, 'gz': 0.1
}

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
for i in range(100):
    data['spd'] = 100 + i
    data['rpm'] = 3000 + i * 50
    sock.sendto(json.dumps(data).encode('utf-8'), ('127.0.0.1', 20777))
    time.sleep(0.033)
sock.close()
"
```

## Troubleshooting

### Dashboard not receiving data

1. **Check UDP settings**: File → Settings, verify IP and port
2. **Check firewall**: Ensure port 20777 is not blocked
3. **Plugin not enabled**: In AC, go to Options → UI Modules and enable "OnTrack"
4. **Wrong IP in config**: If game and dashboard are on different machines, check `game_plugin/config.ini`

### Plugin not showing in AC

1. Ensure folder structure is correct:
   ```
   assettocorsa/apps/python/OnTrack/OnTrack.py
   assettocorsa/apps/python/OnTrack/OnTrack.ini
   ```

2. Check for syntax errors in `OnTrack.py` (must be Python 3.3 compatible)

3. Check AC's `Documents/assettocorsa/logs/py_log.txt` for error messages

### Dashboard crashes on startup

1. Ensure PyQt6 is installed:
   ```bash
   pip install PyQt6>=6.4.0
   ```

2. Check Python version (3.8+ required):
   ```bash
   python3 --version
   ```

## Performance Notes

- Plugin sends ~30 packets/second (configurable)
- Dashboard updates all widgets on each received packet
- Minimal CPU usage (<1% on modern hardware)
- Works well across home network (LAN) latency

## License

Free to use and modify.

## Development Notes

### Plugin (Python 3.3)

The AC plugin uses **Python 3.3** syntax exclusively:
- No f-strings (use `.format()` instead)
- No type hints
- No async/await or threading
- Non-blocking UDP socket for fire-and-forget broadcast

### Dashboard (Python 3.8+)

The dashboard uses modern Python and PyQt6:
- Type hints for clarity
- Threading for UDP receiver
- Qt signals/slots for thread-safe GUI updates

## Future Enhancements

- [ ] G-force visualization widget
- [ ] Brake bias indicator
- [ ] Diff lock percentage
- [ ] Engine temperature monitoring
- [ ] Damage visualization
- [ ] Stint timer
- [ ] Export telemetry to CSV
- [ ] Recording/playback mode
# OnTrack
