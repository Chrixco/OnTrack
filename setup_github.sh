#!/bin/bash
set -e

echo "=================================="
echo "OnTrack - GitHub Setup"
echo "=================================="

cd /Users/chcorral/Documents/GITHUB/OnTrack

echo "✓ Initializing git repository..."
git init

echo "✓ Configuring git user (if needed)..."
git config user.name "Chris Corral" 2>/dev/null || true
git config user.email "christianxcorral@gmail.com" 2>/dev/null || true

echo "✓ Adding all files..."
git add .

echo "✓ Creating initial commit..."
git commit -m "Initial commit: Complete Assetto Corsa telemetry dashboard

- Game plugin (Python 3.3, AC in-game broadcaster)
  * Reads 14 telemetry fields from AC
  * Broadcasts JSON via UDP at ~30 Hz
  * Non-blocking socket, fire-and-forget
  * NaN value protection

- Dashboard application (PyQt6, cross-platform)
  * Runs on macOS, Windows, Linux
  * 6 custom telemetry widgets
  * Settings dialog with dark mode
  * Thread-safe UDP receiver

- Widgets (6 custom visualizations)
  * Speed gauge (analog, rotating needle)
  * RPM bar (gradient, shift light)
  * Pedals (throttle + brake)
  * Lap times (current, best, last, delta)
  * Gear display (R/N/1-9)
  * Tire temps (color-coded, 2x2 grid)

- Configuration & Settings
  * JSON config persistence
  * Customizable UDP IP/port
  * Dark/light mode toggle
  * Per-widget visibility controls

- Network
  * UDP broadcasting (plugin)
  * UDP receiving (dashboard)
  * Works on LAN or same machine
  * Tested and working

- Documentation (7 guides)
  * QUICKSTART.md - 5 minute setup
  * README.md - Full user guide
  * DEPLOYMENT.md - Step-by-step
  * DEVELOPER_GUIDE.md - Extending
  * PROJECT_SUMMARY.md - Architecture
  * FIXES_APPLIED.md - Bug fixes
  * COMPLETION_REPORT.md - Status

- Testing
  * test_components.py - Test suite
  * All tests pass ✓
  * Import validation ✓
  * Config management ✓
  * JSON packet format ✓
  * Widget updates ✓

- Bug Fixes Applied
  * PyQt6 fillEllipse() → drawEllipse()
  * PyQt6 fillPolygon() → drawPolygon()
  * Float to int type conversions

Ready for deployment!"

echo ""
echo "✓ Adding remote origin..."
git remote add origin git@github.com:Chrixco/OnTrack.git 2>/dev/null || git remote set-url origin git@github.com:Chrixco/OnTrack.git

echo "✓ Setting main branch..."
git branch -M main

echo "✓ Pushing to GitHub..."
git push -u origin main

echo ""
echo "=================================="
echo "✓ SUCCESS!"
echo "=================================="
echo ""
echo "Your repo is now live at:"
echo "https://github.com/Chrixco/OnTrack"
echo ""
echo "Next steps:"
echo "1. Add topics on GitHub (assetto-corsa, telemetry, pyqt6)"
echo "2. Optionally add a LICENSE file"
echo "3. Share the link!"
echo ""
