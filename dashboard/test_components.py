#!/usr/bin/env python3
"""
Test script to validate all OnTrack components without GUI display.
"""

import sys
import json

def test_imports():
    """Test that all modules import successfully."""
    print("Testing imports...")
    try:
        from settings.config_manager import ConfigManager
        print("  ✓ ConfigManager")

        from network.udp_receiver import UDPReceiver
        print("  ✓ UDPReceiver")

        from widgets.speed_gauge import SpeedGauge
        print("  ✓ SpeedGauge")

        from widgets.rpm_bar import RPMBar
        print("  ✓ RPMBar")

        from widgets.pedals import PedalWidget
        print("  ✓ PedalWidget")

        from widgets.lap_times import LapTimesWidget
        print("  ✓ LapTimesWidget")

        from widgets.gear_display import GearDisplay
        print("  ✓ GearDisplay")

        from widgets.tire_temps import TireTempsWidget
        print("  ✓ TireTempsWidget")

        return True
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False

def test_config_manager():
    """Test ConfigManager functionality."""
    print("\nTesting ConfigManager...")
    try:
        from settings.config_manager import ConfigManager

        config = ConfigManager()
        print("  ✓ ConfigManager initialized")

        assert config.get('udp_ip') == '0.0.0.0', "Default IP should be 0.0.0.0"
        print("  ✓ Default config loaded")

        config.set('test_key', 'test_value')
        assert config.get('test_key') == 'test_value', "Set/get failed"
        print("  ✓ Set/get operations work")

        return True
    except Exception as e:
        print(f"  ✗ ConfigManager test failed: {e}")
        return False

def test_json_packet():
    """Test UDP packet format."""
    print("\nTesting JSON packet format...")
    try:
        test_packet = {
            'v': 1,
            'spd': 150.7,
            'rpm': 6800,
            'gear': 4,
            'thr': 0.82,
            'brk': 0.0,
            'fuel': 34.2,
            'lap': 3,
            'lap_t': 87432,
            'best_t': 85120,
            'last_t': 86890,
            'tyre': [78.2, 79.1, 81.4, 80.0],
            'gx': -0.12,
            'gy': 1.43,
            'gz': 0.02
        }

        json_str = json.dumps(test_packet)
        parsed = json.loads(json_str)
        assert parsed['spd'] == 150.7, "Speed mismatch"
        assert len(parsed['tyre']) == 4, "Tyre data mismatch"
        print("  ✓ JSON packet format valid")

        return True
    except Exception as e:
        print(f"  ✗ JSON packet test failed: {e}")
        return False

def test_widgets_data_update():
    """Test that widgets can accept data updates."""
    print("\nTesting widget data updates...")
    try:
        from PyQt6.QtWidgets import QApplication

        # Need app for widgets
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        from widgets.speed_gauge import SpeedGauge
        from widgets.rpm_bar import RPMBar
        from widgets.gear_display import GearDisplay

        test_data = {
            'spd': 120.5,
            'rpm': 5000,
            'gear': 3,
            'thr': 0.6,
            'brk': 0.1,
            'fuel': 45,
            'lap': 2,
            'lap_t': 80000,
            'best_t': 75000,
            'last_t': 0,
            'tyre': [80, 82, 78, 79],
            'gx': -0.3,
            'gy': 1.1,
            'gz': 0.0
        }

        speed = SpeedGauge()
        speed.update_data(test_data)
        assert speed._speed == 120.5, "Speed not updated"
        print("  ✓ SpeedGauge.update_data() works")

        rpm = RPMBar()
        rpm.update_data(test_data)
        assert rpm._rpm == 5000, "RPM not updated"
        print("  ✓ RPMBar.update_data() works")

        gear = GearDisplay()
        gear.update_data(test_data)
        assert gear._gear == 3, "Gear not updated"
        print("  ✓ GearDisplay.update_data() works")

        return True
    except Exception as e:
        print(f"  ✗ Widget update test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("=" * 50)
    print("OnTrack Component Test Suite")
    print("=" * 50)

    results = []
    results.append(("Imports", test_imports()))
    results.append(("ConfigManager", test_config_manager()))
    results.append(("JSON Packet", test_json_packet()))
    results.append(("Widget Updates", test_widgets_data_update()))

    print("\n" + "=" * 50)
    print("Test Results:")
    print("=" * 50)

    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} - {name}")

    all_passed = all(r[1] for r in results)

    if all_passed:
        print("\n✓ All tests passed!")
        return 0
    else:
        print("\n✗ Some tests failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())
