# OnTrack Deployment Guide

Complete step-by-step instructions for deploying OnTrack on your system.

## Prerequisites

- **Windows**: Assetto Corsa installed via Steam
- **macOS/Windows**: Python 3.8+
- **Network**: Both machines on same LAN (or explicit IP routing)

## Part 1: Game Plugin Installation (Windows)

### Step 1: Locate AC Apps Folder

```
C:\Program Files (x86)\Steam\steamapps\common\assettocorsa\apps\python\
```

If you installed AC elsewhere, navigate to your AC root directory and open `apps\python\`.

### Step 2: Create OnTrack Plugin Folder

Create a new folder:
```
apps\python\OnTrack\
```

### Step 3: Copy Plugin Files

Copy these files from the `game_plugin` folder into `apps\python\OnTrack\`:

- `OnTrack.py`
- `OnTrack.ini`
- `config.py`
- `config.ini`

Your folder should look like:
```
apps/python/OnTrack/
├── OnTrack.py
├── OnTrack.ini
├── config.py
└── config.ini
```

### Step 4: Configure Network Settings

Edit `apps\python\OnTrack\config.ini`:

**For dashboard on same Windows machine:**
```ini
[UDP]
ip = 127.0.0.1
port = 20777

[GENERAL]
update_rate_hz = 30
```

**For dashboard on different machine (e.g., macOS at 192.168.1.50):**
```ini
[UDP]
ip = 192.168.1.50
port = 20777

[GENERAL]
update_rate_hz = 30
```

### Step 5: Enable Plugin in AC

1. Launch Assetto Corsa
2. Go to **Options** → **UI Modules**
3. Look for "OnTrack" in the list
4. Check the checkbox to enable it
5. Click **OK**

The plugin should now be active. You'll see a small window in AC that indicates it's running.

### Step 6: Verify Plugin is Working

1. Launch a session (free roam, time trial, etc.)
2. Check the documents folder for logs:
   ```
   Documents\Assetto Corsa\logs\py_log.txt
   ```
3. You should see lines like:
   ```
   OnTrack: Initialized. Broadcasting to 127.0.0.1:20777
   ```

## Part 2: Dashboard Installation

### macOS

#### Step 1: Install Python (if needed)

Check if Python 3.8+ is installed:
```bash
python3 --version
```

If not, install from https://www.python.org/downloads/

#### Step 2: Clone/Download OnTrack

Make sure the `dashboard` folder is on your Mac.

#### Step 3: Install Dependencies

```bash
cd /path/to/OnTrack/dashboard
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Step 4: Configure Network (if game on Windows)

Get your Mac's local IP:
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

Example output:
```
inet 192.168.1.50 netmask 0xffffff00 broadcast 192.168.1.255
```

Note the IP address (e.g., `192.168.1.50`).

On Windows, edit `game_plugin/config.ini`:
```ini
[UDP]
ip = 192.168.1.50
port = 20777
```

#### Step 5: Run Dashboard

```bash
source venv/bin/activate
python3 main.py
```

The dashboard window should open.

### Windows (if dashboard on Windows)

#### Step 1: Install Python

Download and install from https://www.python.org/downloads/
- Check "Add Python to PATH" during installation

#### Step 2: Install Dependencies

Open Command Prompt in the `dashboard` folder:

```cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

#### Step 3: Run Dashboard

```cmd
venv\Scripts\activate
python main.py
```

## Part 3: Testing

### Test 1: Dashboard Starts

Run `python main.py` in the dashboard folder. You should see a window with:
- Speed gauge (left side, circular)
- RPM bar (top right)
- Gear display (top middle)
- Pedals widget (middle right)
- Lap times (middle right)
- Tire temps (bottom)

### Test 2: UDP Receives Data (without game)

**Terminal 1** (start dashboard):
```bash
cd dashboard
python3 main.py
```

**Terminal 2** (send test data):
```bash
python3 << 'EOF'
import socket
import json
import time

data = {
    'v': 1, 'spd': 120, 'rpm': 5000, 'gear': 3,
    'thr': 0.6, 'brk': 0.0, 'fuel': 40,
    'lap': 1, 'lap_t': 75000, 'best_t': 75000, 'last_t': 0,
    'tyre': [75, 76, 74, 75], 'gx': 0.0, 'gy': 0.8, 'gz': 0.0
}

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
for i in range(60):
    data['spd'] = 100 + i * 2
    data['rpm'] = 3000 + i * 80
    sock.sendto(json.dumps(data).encode(), ('127.0.0.1', 20777))
    time.sleep(0.033)
sock.close()
print("Test data sent!")
EOF
```

You should see the speed and RPM values increase in the dashboard.

### Test 3: With Assetto Corsa

1. Start the dashboard
2. Launch AC
3. Enable OnTrack in UI Modules
4. Start a session
5. Drive the car

The dashboard should show real-time telemetry.

## Troubleshooting

### Plugin not showing in UI Modules

1. Verify file structure:
   ```
   apps/python/OnTrack/OnTrack.py  ← exists?
   apps/python/OnTrack/OnTrack.ini ← exists?
   ```

2. Check `py_log.txt` for errors:
   ```
   Documents\Assetto Corsa\logs\py_log.txt
   ```

3. Common errors:
   - `SyntaxError`: Plugin code has Python syntax error
   - `ImportError`: Missing standard library (shouldn't happen)
   - `Cannot connect to socket`: Network configuration issue

### Dashboard won't start

1. Check Python version:
   ```bash
   python3 --version  # Should be 3.8 or higher
   ```

2. Check PyQt6 is installed:
   ```bash
   python3 -c "from PyQt6.QtWidgets import QApplication; print('OK')"
   ```

3. If PyQt6 import fails, reinstall:
   ```bash
   pip3 install --upgrade PyQt6
   ```

### Dashboard shows but no data

1. Check UDP settings:
   - Open **File → Settings**
   - Note the "UDP Bind IP" and "UDP Port"
   - Should default to `0.0.0.0:20777`

2. Check firewall:
   - Windows: Allow port 20777 inbound
   - macOS: System Preferences → Security & Privacy → Firewall Options

3. Check plugin config.ini:
   - `game_plugin/config.ini` IP should match dashboard machine
   - Plugin IP = where dashboard is running
   - Test with `127.0.0.1` on same machine first

4. Verify plugin is enabled in AC:
   - Options → UI Modules → Check "OnTrack"

### Data received but widgets don't update

1. Make sure widgets are enabled:
   - File → Settings
   - Check visibility toggles for each widget

2. Make sure widgets are visible:
   - Widgets might be hidden off-screen if window is small
   - Try resizing window

## Network Configuration Examples

### Example 1: Same Computer (Windows)

Plugin IP: `127.0.0.1`
Dashboard: Runs on same Windows machine
Port: `20777`

**game_plugin/config.ini:**
```ini
[UDP]
ip = 127.0.0.1
port = 20777
```

### Example 2: Game on Windows, Dashboard on macOS

1. Find Mac IP:
   ```bash
   ifconfig | grep "inet " | grep -v 127.0.0.1
   # Example: inet 192.168.1.50
   ```

2. In Windows, edit plugin config:
   ```ini
   [UDP]
   ip = 192.168.1.50
   port = 20777
   ```

3. Dashboard on Mac binds to:
   ```
   IP: 0.0.0.0 (listen on all)
   Port: 20777
   ```

### Example 3: Multiple Dashboards

If you want multiple dashboards (main screen + tablet):

- **Main dashboard**: `192.168.1.50:20777`
- **Tablet**: Change tablet's binding to port `20778`
- **Plugin**: Send to both (edit plugin to send twice)

## Performance Tuning

### Reduce Network Load

Edit `game_plugin/config.ini`:
```ini
[GENERAL]
update_rate_hz = 15  # Send 15 times/second instead of 30
```

### Improve GUI Performance

In dashboard **Settings**:
- Disable widgets you don't use (reduces rendering)
- Speed gauge and tire temps are most expensive

## Uninstallation

### Remove Plugin (Windows)

Delete the folder:
```
apps\python\OnTrack\
```

### Remove Dashboard

Just delete the dashboard folder or uninstall via package manager.

## Support

For issues:

1. Check the logs:
   - Plugin: `Documents\Assetto Corsa\logs\py_log.txt`
   - Dashboard: Console output when running

2. Common fixes:
   - Restart AC and dashboard
   - Check firewall settings
   - Verify network connectivity with ping
   - Reinstall Python packages
