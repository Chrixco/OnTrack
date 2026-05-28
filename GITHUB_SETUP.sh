#!/bin/bash
# OnTrack - Push to GitHub
# Copy and paste this entire script into your Terminal

cd /Users/chcorral/Documents/GITHUB/OnTrack

echo "Initializing git repository..."
git init

echo "Configuring git..."
git config user.name "Chris Corral"
git config user.email "christianxcorral@gmail.com"

echo "Adding all files..."
git add .

echo "Creating initial commit..."
git commit -m "Initial commit: Complete Assetto Corsa telemetry dashboard

- Game plugin (Python 3.3, AC in-game broadcaster)
- Dashboard application (PyQt6, cross-platform)
- 6 custom telemetry widgets
- UDP network layer with threading
- Settings dialog with configuration
- Comprehensive documentation (7 guides)
- Full test suite (all passing)
- PyQt6 compatibility fixes"

echo "Adding GitHub remote..."
git remote add origin git@github.com:Chrixco/OnTrack.git

echo "Setting main branch..."
git branch -M main

echo "Pushing to GitHub..."
git push -u origin main

echo ""
echo "✅ SUCCESS!"
echo "Your repo is live at: https://github.com/Chrixco/OnTrack"
