"""Ripple Voice statistics tracker."""

import json
import time
from pathlib import Path
from dataclasses import dataclass, asdict, field

STATS_DIR = Path.home() / "Documents" / "ripple-voice"
STATS_FILE = STATS_DIR / "stats.json"


@dataclass
class Session:
    timestamp: float = 0.0
    text: str = ""
    word_count: int = 0
    char_count: int = 0
    duration_seconds: float = 0.0


@dataclass
class Stats:
    total_sessions: int = 0
    total_words: int = 0
    total_chars: int = 0
    sessions: list = field(default_factory=list)

    @property
    def avg_words(self) -> float:
        return self.total_words / max(1, self.total_sessions)

    @property
    def avg_chars(self) -> float:
        return self.total_chars / max(1, self.total_sessions)

    def add_session(self, text: str, duration: float):
        if not text or not text.strip():
            return
        words = len(text.split())
        chars = len(text)
        session = Session(
            timestamp=time.time(),
            text=text,
            word_count=words,
            char_count=chars,
            duration_seconds=duration,
        )
        self.sessions.append(asdict(session))
        # Keep last 100 sessions
        if len(self.sessions) > 100:
            self.sessions = self.sessions[-100:]
        self.total_sessions += 1
        self.total_words += words
        self.total_chars += chars
        self.save()

    def save(self):
        STATS_DIR.mkdir(parents=True, exist_ok=True)
        with open(STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=2, ensure_ascii=False)

    def load(self) -> "Stats":
        if STATS_FILE.exists():
            try:
                with open(STATS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.total_sessions = data.get("total_sessions", 0)
                self.total_words = data.get("total_words", 0)
                self.total_chars = data.get("total_chars", 0)
                self.sessions = data.get("sessions", [])
            except Exception:
                pass
        return self

    def clear(self):
        self.total_sessions = 0
        self.total_words = 0
        self.total_chars = 0
        self.sessions = []
        self.save()
