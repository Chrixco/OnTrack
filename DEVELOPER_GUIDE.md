# OnTrack Developer Guide

Guide for developers who want to modify, extend, or understand the OnTrack codebase.

## Code Organization

```
OnTrack/
├── game_plugin/              # AC in-game plugin (Python 3.3)
│   ├── OnTrack.py            # Main plugin logic
│   ├── config.py             # Config reader
│   ├── OnTrack.ini           # AC metadata
│   └── config.ini            # User settings
│
└── dashboard/                # External dashboard (Python 3.8+)
    ├── main.py               # Entry point
    ├── app.py                # Main window
    ├── widgets/              # Display components
    ├── settings/             # Configuration
    ├── network/              # Networking
    └── requirements.txt      # Dependencies
```

## Plugin Development (game_plugin/)

### Understanding the Plugin Architecture

The plugin implements three AC lifecycle functions that AC calls automatically:

```python
def acMain(ac_version):
    # Called once when AC loads the plugin
    # Initialize socket, read config, create AC window
    # Return app name string
    return "OnTrack"

def acUpdate(deltaT):
    # Called every frame (60 Hz)
    # Read telemetry, pack JSON, send UDP
    # Should return immediately (no heavy computation)
    pass

def acShutdown():
    # Called when AC closes or plugin is disabled
    # Clean up resources (close socket, etc.)
    pass
```

### Adding New Telemetry Fields

To add a new telemetry field (e.g., brake temperature):

1. **In acUpdate()**, read the value:
```python
brake_temp = ac.getCarState(0, acsys.CS.BrakeTempFL)  # Example
if math.isnan(brake_temp):
    brake_temp = 0.0
```

2. **Add to telemetry dict**:
```python
telemetry = {
    # ... existing fields ...
    'brake_t': round(brake_temp, 1)  # Short key for bandwidth
}
```

3. **Update UDP packet format** in docs/code

4. **Add to dashboard** (see dashboard section below)

### Modifying Update Rate

Edit `game_plugin/config.ini`:
```ini
[GENERAL]
update_rate_hz = 60  # Send 60 packets/second (default 30)
```

The plugin calculates `_update_every = 60 / update_rate_hz` to throttle sends.

### Testing Plugin Changes

1. Edit `OnTrack.py` locally
2. Check syntax: `python3 -m py_compile OnTrack.py`
3. Copy to AC folder on Windows machine
4. Restart AC
5. Check logs: `Documents\Assetto Corsa\logs\py_log.txt`

### Important: Python 3.3 Rules

These are **strict requirements** because AC embeds Python 3.3:

```python
# ✗ Wrong (Python 3.6+):
f"Speed: {speed}"
def func(x: int) -> float: ...
if (match := regex.search(s)): ...

# ✓ Right (Python 3.3):
"Speed: {}".format(speed)
def func(x): ...
match = regex.search(s)
if match: ...
```

## Dashboard Development (dashboard/)

### Adding a New Widget

Create `dashboard/widgets/new_widget.py`:

```python
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QFont
from PyQt6.QtCore import Qt

class NewWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._value = 0
        self.setMinimumSize(200, 100)
        self.setStyleSheet("background-color: #1a1a1a; border-radius: 8px;")

    def update_data(self, data):
        """Update from telemetry dict."""
        self._value = data.get('new_field', 0)
        self.update()  # Triggers paintEvent

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w = self.width()
        h = self.height()
        
        # Draw your widget here
        painter.fillRect(0, 0, w, h, QColor(50, 50, 60))
        
        painter.setPen(QColor(200, 200, 200))
        painter.drawText(10, 10, "Value: {}".format(self._value))
        
        painter.end()
```

Add to `dashboard/app.py`:

```python
from widgets.new_widget import NewWidget  # Add import

class MainWindow(QMainWindow):
    def init_ui(self):
        # ... existing widgets ...
        self.new_widget = NewWidget()
        layout.addWidget(self.new_widget, row, col)  # Place in grid
    
    def on_telemetry(self, data):
        # ... existing updates ...
        if self.config.get('show_new_widget', True):
            self.new_widget.update_data(data)
```

Add setting to `dashboard/settings/settings_dialog.py`:

```python
self.show_new_widget = QCheckBox("New Widget")
self.show_new_widget.setChecked(self.current_config.get('show_new_widget', True))
form_layout.addRow(self.show_new_widget)

# In apply_settings():
'show_new_widget': self.show_new_widget.isChecked()
```

### Widget Best Practices

1. **Size**: Set `setMinimumSize()` so layout respects widget
2. **Style**: Use stylesheet for background
   ```python
   self.setStyleSheet("background-color: #1a1a1a; border-radius: 8px;")
   ```
3. **Rendering**: Always use `QPainter.RenderHint.Antialiasing`
4. **Colors**: Use consistent dark theme colors:
   - Background: `QColor(26, 26, 30)` (#1a1a1e)
   - Text: `QColor(200, 200, 200)`
   - Accents: `QColor(100, 150, 255)` or domain-specific

### Modifying Layouts

Grid layout in `app.py`:

```python
# Current layout (3x3 grid):
# (0,0) Speed Gauge (2 rows)  | (0,1) Gear    | (0,2) RPM
# (1,0)                       | (1,1) Pedals  | (1,2) Lap Times
# (2,0 colspan=3) Tire Temps
```

To change: edit the `addWidget(widget, row, col, rowspan, colspan)` calls.

### Settings Management

Config file: `~/.config/ontrack/settings.json`

Access anywhere:
```python
config_manager = ConfigManager()
speed_unit = config_manager.get('speed_unit', 'kmh')
config_manager.set('speed_unit', 'mph')
```

### Thread Safety

Never call GUI methods from `UDPReceiver.run()`:

```python
# ✗ Wrong (will crash):
def run(self):
    data = receive_udp()
    self.label.setText(data)  # Segfault!

# ✓ Right (use signals):
def run(self):
    data = receive_udp()
    self.telemetry_received.emit(data)  # Safe, queued to main thread

# In main thread:
self.udp_receiver.telemetry_received.connect(self.on_telemetry)
def on_telemetry(self, data):
    self.label.setText(data)  # Safe, on main thread
```

## Common Modifications

### Change Default Color Scheme

Edit color constants (add to beginning of files):

```python
DARK_BG = QColor(26, 26, 30)
BRIGHT_TEXT = QColor(255, 255, 255)
ACCENT_GREEN = QColor(100, 200, 100)
ACCENT_RED = QColor(200, 50, 50)
```

### Adjust Widget Sizes

Modify `setMinimumSize()`:
```python
self.setMinimumSize(400, 200)  # width, height
```

Or in grid layout:
```python
layout.setSpacing(15)  # Space between widgets
layout.setContentsMargins(15, 15, 15, 15)  # Border margins
```

### Change Update Frequency

On dashboard (all data received at plugin's rate):
- Change plugin rate: edit `game_plugin/config.ini`

On render (only if > 60 FPS):
```python
# In app.py __init__:
self.timer = QTimer()
self.timer.timeout.connect(self.repaint_widgets)
self.timer.start(16)  # ~60 FPS (1000/60)
```

### Add Network Debugging

In `network/udp_receiver.py`:

```python
def run(self):
    # ... existing code ...
    print("UDP listening on {}:{}".format(self.ip, self.port))
    
    while self._running:
        try:
            data, addr = self._socket.recvfrom(4096)
            telemetry = json.loads(data.decode('utf-8'))
            print("Received: spd={}, rpm={}".format(
                telemetry.get('spd'), telemetry.get('rpm')))
            self.telemetry_received.emit(telemetry)
        # ... rest of error handling ...
```

## Performance Tips

### Reduce Rendering Cost

1. **Use setMinimumSize** instead of fixed size
2. **Cache calculations** in `update_data()`, not `paintEvent()`
3. **Avoid complex paths** in paintEvent
4. **Hide unused widgets** (visibility toggle in settings)

### Network Optimization

1. **Reduce update rate** if network is constrained:
   ```ini
   update_rate_hz = 15  # Instead of 30
   ```

2. **Compress data** (if bandwidth is critical):
   ```python
   # Instead of full JSON, use binary format
   # But requires protocol change on both sides
   ```

## Testing & Debugging

### Unit Test Widget Offline

```python
# test_widget.py
import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout
from dashboard.widgets.speed_gauge import SpeedGauge

app = QApplication(sys.argv)
window = QWidget()
layout = QVBoxLayout()

gauge = SpeedGauge()
test_data = {
    'spd': 150.0, 'rpm': 7000, 'gear': 4, 'thr': 0.8, 'brk': 0.0,
    'fuel': 30, 'lap': 2, 'lap_t': 87000, 'best_t': 85000,
    'last_t': 0, 'tyre': [80, 82, 78, 79], 'gx': -0.5, 'gy': 1.2, 'gz': 0.1
}
gauge.update_data(test_data)
layout.addWidget(gauge)

window.setLayout(layout)
window.show()
sys.exit(app.exec())
```

Run: `python3 test_widget.py`

### Debug UDP Data

Monitor incoming packets:

```bash
# macOS/Linux:
tcpdump -i en0 -A 'port 20777'

# Or Python:
python3 << 'EOF'
import socket
import json

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('0.0.0.0', 20777))
while True:
    data, addr = sock.recvfrom(4096)
    telemetry = json.loads(data)
    print("Speed: {} RPM: {}".format(telemetry['spd'], telemetry['rpm']))
EOF
```

### Console Output

Run dashboard with:
```bash
python3 -u main.py  # Unbuffered output
```

Errors and prints appear in console.

## Contributing Back

If you improve OnTrack:

1. **Document changes** in comments
2. **Test on both Windows and macOS**
3. **Follow existing code style** (indentation, naming)
4. **Update README.md** if adding features
5. **Keep Python 3.3 compatibility** in plugin
6. **Use type hints** in dashboard (helpful)

## Resources

- **PyQt6 Docs**: https://www.riverbankcomputing.com/static/Docs/PyQt6/
- **AC SDK**: Forum posts on assettocorsa.net
- **Python 3.3**: https://docs.python.org/3.3/
- **Socket Programming**: https://docs.python.org/3/library/socket.html

## Quick Reference

### Key Files by Task

| Task | File |
|------|------|
| Add telemetry field | `game_plugin/OnTrack.py` |
| Add display widget | `dashboard/widgets/` |
| Change network config | `dashboard/settings/config_manager.py` |
| Modify UI layout | `dashboard/app.py` |
| Add settings option | `dashboard/settings/settings_dialog.py` |
| Change colors | Any widget file (search for `QColor`) |

### Key Methods

**Plugin:**
- `ac.getCarState(0, acsys.CS.*)` - Read telemetry
- `ac.newApp(name)` - Create window
- `socket.sendto(data, address)` - Send UDP

**Dashboard:**
- `widget.update_data(dict)` - Update with telemetry
- `widget.update()` - Trigger repaint
- `painter.drawText/drawRect/fillRect` - Render
- `config_manager.get/set(key)` - Read/write settings

## Version History

- **v1.0** - Initial release (2026)
  - 6 widgets (speed, RPM, pedals, lap times, gear, tires)
  - Settings dialog
  - Dark mode
  - Cross-machine networking
