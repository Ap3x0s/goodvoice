"""System tray icon using pystray."""

import threading
from PIL import Image
import pystray


class TrayIcon:
    def __init__(self, icon_path: str):
        self._icon_path = icon_path
        self._icon = None
        self._thread = None
        self.on_show = None
        self.on_hide = None
        self.on_settings = None
        self.on_quit = None
        self._visible = True

    def start(self) -> None:
        """Start the tray icon in a background thread."""
        image = Image.open(self._icon_path)
        menu = pystray.Menu(
            pystray.MenuItem("Показать/Скрыть", self._toggle_hud, default=True),
            pystray.MenuItem("Выход", self._quit),
        )
        self._icon = pystray.Icon("GoodVoice", image, "GoodVoice", menu)
        self._thread = threading.Thread(target=self._icon.run, daemon=True)
        self._thread.start()

    def _toggle_hud(self, icon=None, item=None):
        self._visible = not self._visible
        if self._visible and self.on_show:
            self.on_show()
        elif not self._visible and self.on_hide:
            self.on_hide()

    def _open_settings(self, icon=None, item=None):
        if self.on_settings:
            self.on_settings()

    def _quit(self, icon=None, item=None):
        if self._icon:
            self._icon.stop()
        if self.on_quit:
            self.on_quit()

    def stop(self) -> None:
        if self._icon:
            self._icon.stop()
