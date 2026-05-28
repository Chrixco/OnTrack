# OnTrack - Project Manifest

Complete list of all files and components delivered.

## Game Plugin Files

### `/game_plugin/OnTrack.py` (147 lines)
Main AC plugin with telemetry reading and UDP broadcasting
- `acMain()` - Initialize socket and AC window
- `acUpdate()` - Read telemetry and broadcast
- `acShutdown()` - Cleanup
- Non-blocking UDP socket
- NaN value protection
- Python 3.3 compatible

### `/game_plugin/config.py` (40 lines)
Configuration file reader
- Python 3.3 compatible ConfigParser
- Default fallbacks
- Read IP, port, update rate

### `/game_plugin/OnTrack.ini` (5 lines)
AC plugin metadata
- Required by AC to load plugin
- Specifies Python version, name, author, description

### `/game_plugin/config.ini` (6 lines)
User-editable configuration
- UDP target IP (default 127.0.0.1)
- UDP target port (default 20777)
- Update frequency (default 30 Hz)

---

## Dashboard Files

### Core Application

#### `/dashboard/main.py` (11 lines)
Entry point for dashboard
- QApplication creation
- MainWindow instantiation
- Proper Qt event loop

#### `/dashboard/app.py` (234 lines)
Main window implementation
- QMainWindow with QGridLayout
- Menu bar (File, View, Help)
- Settings dialog integration
- Dark mode implementation
- UDP receiver lifecycle
- Telemetry dispatch to widgets

#### `/dashboard/requirements.txt` (1 line)
Python dependencies
- PyQt6>=6.4.0

### Network Layer

#### `/dashboard/network/udp_receiver.py` (62 lines)
UDP listener thread
- QThread-based (non-blocking)
- Configurable IP and port binding
- JSON parsing with error handling
- Signal emission for thread safety
- Connection status tracking
- Timeout handling

#### `/dashboard/network/__init__.py` (1 line)
Package marker

### Settings

#### `/dashboard/settings/config_manager.py` (65 lines)
Configuration file management
- JSON config persistence
- Reads/writes to ~/.config/ontrack/settings.json
- Default value merging
- Cross-platform path handling
- Simple get/set/update API

#### `/dashboard/settings/settings_dialog.py` (140 lines)
Settings GUI dialog
- QDialog with QFormLayout
- Network configuration (IP, port)
- Display settings (dark mode, max RPM, speed unit)
- Widget visibility toggles (7 widgets)
- Input validation (IP regex, port range)
- Settings changed signal

#### `/dashboard/settings/__init__.py` (1 line)
Package marker

### Widgets

#### `/dashboard/widgets/speed_gauge.py` (162 lines)
Analog speed gauge widget
- Circular arc gauge (225° to -45°)
- Rotating needle with trigonometry
- Tick marks at 20 km/h intervals
- Digital readout at bottom
- Configurable max speed (0-300 km/h)
- Antialiased QPainter rendering

#### `/dashboard/widgets/rpm_bar.py` (85 lines)
RPM bar with shift indicator
- Horizontal bar chart
- Color gradient (green → yellow → red)
- Redline marker at 90% of max
- Shift light (flashing white circle)
- Configurable max RPM (3000-20000)

#### `/dashboard/widgets/pedals.py` (85 lines)
Throttle and brake input visualization
- Two vertical bars side by side
- Left bar: throttle (green)
- Right bar: brake (red)
- Percentage labels
- Dark background

#### `/dashboard/widgets/lap_times.py` (115 lines)
Lap timing display
- CURR / BEST / LAST times
- Time formatter: M:SS.mmm format
- BEST lap in gold, LAST in delta-colored text
- Lap counter in corner
- Invalid/zero time handling

#### `/dashboard/widgets/gear_display.py` (65 lines)
Large gear number display
- Single character centered
- R (red), N (gray), 1-9 (white)
- Large 48pt bold font
- Rounded rect background

#### `/dashboard/widgets/tire_temps.py` (130 lines)
Tire temperature display
- 2×2 grid of four tires (FL, FR, RL, RR)
- HSV color interpolation by temperature
- Blue (<60°C) → Green (75-95°C) → Red (>105°C)
- Temperature and corner labels
- Smooth color gradients

#### `/dashboard/widgets/__init__.py` (1 line)
Package marker

---

## Documentation Files

### `/README.md` (300 lines)
Complete user documentation
- Feature overview
- Installation instructions
- Usage guide (same machine, cross-network)
- Configuration options
- UDP packet format
- Testing without game
- Troubleshooting
- License and future enhancements

### `/DEPLOYMENT.md` (250 lines)
Step-by-step deployment guide
- Prerequisites
- Plugin installation (Windows AC)
- Dashboard installation (macOS, Windows, Linux)
- Network configuration examples
- Testing procedures
- Troubleshooting
- Performance tuning
- Uninstallation

### `/PROJECT_SUMMARY.md` (280 lines)
Complete project overview
- Architecture and design
- Deliverables checklist
- Telemetry data format
- Widget descriptions
- Technical highlights
- Features implemented
- Testing performed
- File statistics
- Conclusion

### `/DEVELOPER_GUIDE.md` (350 lines)
Developer reference
- Code organization
- Plugin development guide
- Dashboard development guide
- Adding new widgets
- Common modifications
- Performance tips
- Testing and debugging
- Quick reference tables
- Version history

### `/MANIFEST.md` (this file)
Complete file listing and line counts

---

## Summary Statistics

### Game Plugin
- **Files**: 4
- **Total Lines**: ~200
- **Language**: Python 3.3

### Dashboard Application
- **Core Files**: 3 (main, app, requirements)
- **Network Files**: 2 (udp_receiver, __init__)
- **Settings Files**: 3 (config_manager, settings_dialog, __init__)
- **Widget Files**: 7 (6 widgets + __init__)
- **Total Python Files**: 14
- **Total Lines**: ~1,100
- **Language**: Python 3.8+, PyQt6

### Documentation
- **Files**: 5
- **Total Lines**: ~1,200
- **Coverage**: User guide, deployment, developer guide, project summary, manifest

### Grand Total
- **All Files**: 23
- **All Code**: ~1,300 lines
- **All Docs**: ~1,200 lines
- **Total**: ~2,500 lines

---

## Directory Tree

```
OnTrack/
├── README.md                          # User guide
├── DEPLOYMENT.md                      # Deployment instructions
├── PROJECT_SUMMARY.md                 # Project overview
├── DEVELOPER_GUIDE.md                 # Developer reference
├── MANIFEST.md                        # This file
│
├── game_plugin/                       # AC in-game plugin
│   ├── OnTrack.py                     # Main plugin (147 lines)
│   ├── config.py                      # Config reader (40 lines)
│   ├── OnTrack.ini                    # AC metadata (5 lines)
│   └── config.ini                     # User config (6 lines)
│
└── dashboard/                         # External dashboard app
    ├── main.py                        # Entry point (11 lines)
    ├── app.py                         # Main window (234 lines)
    ├── requirements.txt               # Dependencies (1 line)
    │
    ├── settings/
    │   ├── __init__.py
    │   ├── config_manager.py          # Config I/O (65 lines)
    │   └── settings_dialog.py         # Settings GUI (140 lines)
    │
    ├── network/
    │   ├── __init__.py
    │   └── udp_receiver.py            # UDP listener (62 lines)
    │
    └── widgets/
        ├── __init__.py
        ├── speed_gauge.py             # Speed gauge (162 lines)
        ├── rpm_bar.py                 # RPM bar (85 lines)
        ├── pedals.py                  # Pedals (85 lines)
        ├── lap_times.py               # Lap times (115 lines)
        ├── gear_display.py            # Gear display (65 lines)
        └── tire_temps.py              # Tire temps (130 lines)
```

---

## Features by Component

### Game Plugin
- ✅ Telemetry reading (14 fields)
- ✅ UDP broadcasting (non-blocking)
- ✅ Network configuration
- ✅ NaN value protection
- ✅ Python 3.3 compatibility
- ✅ AC lifecycle hooks

### Dashboard
- ✅ UDP receiving (threaded)
- ✅ Real-time rendering (6 widgets)
- ✅ Settings dialog
- ✅ Dark mode
- ✅ Configuration persistence
- ✅ Cross-platform
- ✅ Network flexibility

### Widgets (6 total)
- ✅ Speed gauge (analog, 270° arc)
- ✅ RPM bar (gradient, shift light)
- ✅ Pedals (throttle + brake)
- ✅ Lap times (current, best, last, delta)
- ✅ Gear display (R/N/1-9)
- ✅ Tire temps (4-corner, color-coded)

### Documentation
- ✅ User guide (README.md)
- ✅ Deployment instructions (DEPLOYMENT.md)
- ✅ Project overview (PROJECT_SUMMARY.md)
- ✅ Developer guide (DEVELOPER_GUIDE.md)
- ✅ File manifest (MANIFEST.md)

---

## Quality Checklist

- ✅ All Python files compile without syntax errors
- ✅ Proper error handling (try/except, NaN checks)
- ✅ Thread-safe design (Qt signals)
- ✅ Python 3.3 compatibility (plugin)
- ✅ Modern Python practices (dashboard)
- ✅ Comprehensive documentation
- ✅ Clear code organization
- ✅ Configurable settings
- ✅ Cross-platform support
- ✅ Network flexibility (local/LAN)

---

## Deployment Checklist

- ✅ Game plugin ready for AC Windows installation
- ✅ Dashboard ready for cross-platform deployment
- ✅ Dependencies documented (PyQt6)
- ✅ Configuration templates provided
- ✅ Installation instructions complete
- ✅ Troubleshooting guide included
- ✅ Testing procedures documented

---

## Ready for Production

This project is ready for:
1. Installation on Assetto Corsa (Windows)
2. Dashboard deployment (macOS/Windows/Linux)
3. Network testing (local or LAN)
4. User customization (settings, widget visibility)
5. Further development (clear architecture for extensions)

