"""Persisted user settings.

Stored as JSON under ``~/.config/ontrack/settings.json`` on all platforms
(Windows respects the same path under the user profile).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ConfigManager:
    DEFAULT_CONFIG: dict[str, Any] = {
        # AC's telemetry server -- 127.0.0.1 for same-machine, otherwise
        # the LAN IP of the Windows box running AC. Port 9996 is fixed by AC.
        "ac_ip": "127.0.0.1",
        "ac_port": 9996,
        "dark_mode": True,
        "speed_unit": "kmh",
        "max_rpm": 8000,
    }

    def __init__(self, config_dir: Path | None = None) -> None:
        self.config_dir = config_dir or (Path.home() / ".config" / "ontrack")
        self.config_file = self.config_dir / "settings.json"
        self.config: dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """Load config from disk, merging with defaults."""
        if not self.config_file.exists():
            self.config = dict(self.DEFAULT_CONFIG)
            self.save()
            return

        try:
            with self.config_file.open("r", encoding="utf-8") as fh:
                loaded = json.load(fh)
        except (OSError, json.JSONDecodeError):
            logger.exception("failed to load config, falling back to defaults")
            self.config = dict(self.DEFAULT_CONFIG)
            return

        merged = dict(self.DEFAULT_CONFIG)
        if isinstance(loaded, dict):
            merged.update(loaded)
        self.config = merged

    def save(self) -> None:
        """Persist current config to disk."""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with self.config_file.open("w", encoding="utf-8") as fh:
                json.dump(self.config, fh, indent=2)
        except OSError:
            logger.exception("failed to save config")

    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.config[key] = value
        self.save()

    def update(self, **kwargs: Any) -> None:
        self.config.update(kwargs)
        self.save()
