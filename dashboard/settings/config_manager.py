import json
import os
from pathlib import Path

class ConfigManager:
    DEFAULT_CONFIG = {
        'udp_ip': '0.0.0.0',
        'udp_port': 20777,
        'dark_mode': True,
        'show_speed': True,
        'show_rpm': True,
        'show_pedals': True,
        'show_gear': True,
        'show_lap_times': True,
        'show_tire_temps': True,
        'show_gforces': True,
        'speed_unit': 'kmh',
        'max_rpm': 8000
    }

    def __init__(self):
        self.config_dir = Path.home() / '.config' / 'ontrack'
        self.config_file = self.config_dir / 'settings.json'
        self.config = {}
        self.load()

    def load(self):
        """Load config from disk, merging with defaults."""
        if self.config_file.exists():
            try:
                with open(str(self.config_file), 'r') as f:
                    loaded = json.load(f)
                    self.config = dict(self.DEFAULT_CONFIG)
                    self.config.update(loaded)
            except Exception as e:
                print("Error loading config: {0}".format(str(e)))
                self.config = dict(self.DEFAULT_CONFIG)
        else:
            self.config = dict(self.DEFAULT_CONFIG)
            self.save()

    def save(self):
        """Save config to disk."""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(str(self.config_file), 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print("Error saving config: {0}".format(str(e)))

    def get(self, key, default=None):
        """Get a config value."""
        return self.config.get(key, default)

    def set(self, key, value):
        """Set a config value and save."""
        self.config[key] = value
        self.save()

    def update(self, **kwargs):
        """Update multiple config values and save."""
        self.config.update(kwargs)
        self.save()
