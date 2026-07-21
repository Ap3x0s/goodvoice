"""System tray icon using pystray with callback queue."""

import threading
import queue
from PIL import Image
import pystray


class TrayIcon:
    def __init__(self, icon_path: str):
        self._icon_path = icon_path
        self._icon = None
        self._thread = None
        self._q = queue.Queue()
        self._visible = True

    def start(self) -> None:
        image = Image.open(self._icon_path)
        menu = pystray.Menu(
            pystray.MenuItem("Показать/Скрыть", self._toggle_hud, default=True),
            pystray.MenuItem("Настройки", self._on_settings_click),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Выход", self._on_quit_click),
        )
        self._icon = pystray.Icon("GoodVoice", image, "GoodVoice", menu)
        self._thread = threading.Thread(target=self._icon.run, daemon=True)
        self._thread.start()

    def _toggle_hud(self, icon=None, item=None):
        self._visible = not self._visible
        self._q.put("toggle_hud")

    def _on_settings_click(self, icon=None, item=None):
        self._q.put("open_settings")

    def _on_quit_click(self, icon=None, item=None):
        self._q.put("quit")
        if self._icon:
            self._icon.stop()

    def get_command(self):
        """Get next command from tray (non-blocking)."""
        try:
            return self._q.get_nowait()
        except queue.Empty:
            return None

    def stop(self) -> None:
        if self._icon:
            try:
                self._icon.stop()
            except Exception:
                pass
