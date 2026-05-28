# OnTrack - Quick Start Guide

**OnTrack** is a real-time telemetry dashboard for Assetto Corsa. Get it running in 5 minutes.

---

## **macOS - Run Dashboard (Right Now)**

```bash
# 1. Navigate to project
cd /Users/chcorral/Documents/GITHUB/OnTrack/dashboard

# 2. Activate virtual environment
source venv/bin/activate

# 3. Run dashboard
python3 main.py
```

The dashboard window opens with 6 widgets showing telemetry values (all zero since no data yet).

---

## **Send Test Data (Without Game)**

Open a new terminal in the same `dashboard` folder:

```bash
source venv/bin/activate
python3 << 'EOF'
import socket, json, time
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Simulate a drive: speed 0-150, RPM 3000-7500
data = {
    'v': 1, 'spd': 0, 'rpm': 3000, 'gear': 1,
    'thr': 0.0, 'brk': 0.0, 'fuel': 50,
    'lap': 1, 'lap_t': 0, 'best_t': 0, 'last_t': 0,
    'tyre': [70, 70, 70, 70], 'gx': 0.0, 'gy': 0.0, 'gz': 0.0
}

for i in range(200):
    data['spd'] = i * 0.75  # 0-150 km/h
    data['rpm'] = 3000 + i * 22.5  # 3000-7500 RPM
    data['thr'] = min(i / 200.0, 1.0)
    data['gear'] = min(1 + i // 50, 5)
    data['lap_t'] = i * 500
    data['tyre'] = [70 + i*0.05, 72 + i*0.05, 68 + i*0.05, 71 + i*0.05]
    sock.sendto(json.dumps(data).encode(), ('127.0.0.1', 20777))
    time.sleep(0.033)  # 30 Hz
sock.close()
print("Sent 200 telemetry packets!")
EOF
```

Watch the dashboard update in real-time! 🎯

---

## **With Assetto Corsa (Windows)**

### Plugin Setup (On Windows Machine)

1. **Copy plugin to AC folder**:
   ```
   From: /Users/chcorral/Documents/GITHUB/OnTrack/game_plugin/
   To:   C:\Program Files (x86)\Steam\steamapps\common\assettocorsa\apps\python\OnTrack\
   ```

2. **Edit plugin configuration**:
   ```
   C:\...\assettocorsa\apps\python\OnTrack\config.ini
   ```

   **If dashboard is on same PC:**
   ```ini
   [UDP]
   ip = 127.0.0.1
   port = 20777
   ```

   **If dashboard is on macOS (replace with your Mac IP):**
   ```bash
   # Find Mac IP in Terminal:
   ifconfig | grep "inet " | grep -v 127.0.0.1
   # Example: inet 192.168.1.50
   ```
   ```ini
   [UDP]
   ip = 192.168.1.50
   port = 20777
   ```

3. **Enable plugin in AC**:
   - Launch Assetto Corsa
   - Go to **Options** → **UI Modules**
   - Check **OnTrack** ✓
   - Click **OK**

4. **Start a session** and drive!
   - The dashboard should immediately show live telemetry
   - Speed, RPM, gear, lap times, tire temps all update in real-time

---

## **Dashboard Controls**

### Menu Bar
- **File → Settings** - Configure UDP IP/port, dark mode, widget visibility
- **File → Exit** - Close the app
- **View → Toggle Dark Mode** - Switch between dark/light themes
- **Help → About** - About the app

### Settings Dialog (File → Settings)
- **UDP Bind IP** - Where to listen (default: 0.0.0.0 = all interfaces)
- **UDP Port** - Port number (default: 20777)
- **Dark Mode** - Toggle on/off
- **Max RPM** - Gauge calibration (default: 8000)
- **Speed Unit** - km/h or mph
- **Widget Toggles** - Show/hide each widget

Click **Apply** to save and reconnect.

---

## **Widgets Explained**

| Widget | Shows | Range |
|--------|-------|-------|
| **Speed Gauge** | Current speed | 0-300 km/h |
| **RPM Bar** | Engine RPM | 0-max RPM (configurable) |
| **Pedals** | Throttle/brake input | 0-100% |
| **Lap Times** | Current/best/last lap | Time format: M:SS.mmm |
| **Gear Display** | Current gear | R, N, 1-9 |
| **Tire Temps** | All 4 tire temps | Color: blue (cold) → green (optimal) → red (hot) |

---

## **Troubleshooting**

### Dashboard won't start
```bash
# Check Python version (need 3.8+)
python3 --version

# Reinstall dependencies
pip install --upgrade PyQt6

# Verify imports work
python3 -c "from app import MainWindow; print('OK')"
```

### Dashboard runs but no data
1. Check **File → Settings** - verify IP and port
2. Check firewall allows port 20777
3. Verify AC plugin is enabled (Options → UI Modules)
4. Check plugin config.ini has correct IP

### Test the connection
```bash
# Terminal 1: Check if UDP listener is running
lsof -i :20777

# Terminal 2: Send test packet
python3 << 'EOF'
import socket, json
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
data = {'v': 1, 'spd': 100, 'rpm': 5000, 'gear': 3, 'thr': 0.5,
        'brk': 0.0, 'fuel': 40, 'lap': 1, 'lap_t': 75000,
        'best_t': 75000, 'last_t': 0, 'tyre': [75,76,74,75],
        'gx': 0.0, 'gy': 0.8, 'gz': 0.0}
sock.sendto(json.dumps(data).encode(), ('127.0.0.1', 20777))
sock.close()
print("Test packet sent!")
EOF
```

---

## **Run Tests**

Verify all components work:

```bash
cd /Users/chcorral/Documents/GITHUB/OnTrack/dashboard
source venv/bin/activate
python3 test_components.py
```

Expected output:
```
✓ PASS - Imports
✓ PASS - ConfigManager
✓ PASS - JSON Packet Format
✓ PASS - Widget Updates

✓ All tests passed!
```

---

## **Next Steps**

1. **Read full documentation**: See `README.md`
2. **Deployment details**: See `DEPLOYMENT.md`
3. **Develop further**: See `DEVELOPER_GUIDE.md`
4. **Project overview**: See `PROJECT_SUMMARY.md`
5. **Bug fixes applied**: See `FIXES_APPLIED.md`

---

## **File Locations**

```
/Users/chcorral/Documents/GITHUB/OnTrack/
├── game_plugin/          ← Copy to AC on Windows
├── dashboard/            ← Run on macOS/Windows
│   ├── main.py          ← Entry point
│   ├── test_components.py ← Test suite
│   ├── venv/            ← Virtual environment
│   └── requirements.txt  ← Dependencies
└── *.md                 ← Documentation
```

---

## **Common Commands**

```bash
# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
pip install -r requirements.txt

# Run the dashboard
python3 main.py

# Run tests
python3 test_components.py

# Deactivate virtual environment
deactivate
```

---

## **Example: Full Setup**

1. **Terminal 1 - Dashboard**:
   ```bash
   cd /Users/chcorral/Documents/GITHUB/OnTrack/dashboard
   source venv/bin/activate
   python3 main.py
   ```

2. **Terminal 2 - Test Data**:
   ```bash
   cd /Users/chcorral/Documents/GITHUB/OnTrack/dashboard
   source venv/bin/activate
   # Run test data script from above
   ```

3. **See live telemetry** in the dashboard window! 🎯

---

That's it! You're ready to use OnTrack. 🚀

For detailed setup with Assetto Corsa, see **DEPLOYMENT.md**.
