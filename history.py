"""GoodVoice transcription history."""

import json
import time
from pathlib import Path
from dataclasses import dataclass, asdict, field

HISTORY_DIR = Path.home() / "Documents" / "goodvoice"
HISTORY_FILE = HISTORY_DIR / "history.json"
MAX_ENTRIES = 50


@dataclass
class HistoryEntry:
    timestamp: float = 0.0
    text: str = ""
    word_count: int = 0
    char_count: int = 0


class History:
    def __init__(self):
        self.entries: list = []

    def add(self, text: str):
        if not text or not text.strip():
            return
        entry = HistoryEntry(
            timestamp=time.time(),
            text=text,
            word_count=len(text.split()),
            char_count=len(text),
        )
        self.entries.append(asdict(entry))
        if len(self.entries) > MAX_ENTRIES:
            self.entries = self.entries[-MAX_ENTRIES:]
        self.save()

    def get_recent(self, n: int = 20) -> list:
        return list(reversed(self.entries[-n:]))

    def clear(self):
        self.entries = []
        self.save()

    def save(self):
        HISTORY_DIR.mkdir(parents=True, exist_ok=True)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(self.entries, f, indent=2, ensure_ascii=False)

    def load(self) -> "History":
        if HISTORY_FILE.exists():
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    self.entries = json.load(f)
            except Exception:
                self.entries = []
        return self
