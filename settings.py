"""Settings management for GoodVoice."""

import json
from pathlib import Path
from dataclasses import dataclass, asdict

SETTINGS_DIR = Path.home() / "Documents" / "goodvoice"
SETTINGS_FILE = SETTINGS_DIR / "settings.json"


@dataclass
class Settings:
    model_size: str = "medium"
    language: str = "auto"
    trigger_mode: str = "hold"  # "hold" or "toggle"
    punctuation: bool = True
    hud_position: str = "center"  # "center" or "cursor"
    autostart: bool = False
    hotkey: str = "ctrl_r"
    hud_theme: str = "google"  # "google" or "vercel"

    def load(self) -> "Settings":
        """Load settings from JSON file, create with defaults if missing."""
        if SETTINGS_FILE.exists():
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            for key, value in data.items():
                if hasattr(self, key):
                    setattr(self, key, value)
        return self

    def save(self) -> None:
        """Save current settings to JSON file."""
        SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=2, ensure_ascii=False)
