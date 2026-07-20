"""GoodVoice — Windows voice dictation tool.

Press Right Ctrl to start dictation (hold or toggle mode).
Release to transcribe and paste text into the active field.
Press Escape to cancel without inserting.
Right Alt+P — open settings.
"""

import sys
import threading
import time
import queue
from pathlib import Path

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QIcon

from settings import Settings
from stats import Stats
from history import History
from audio_recorder import AudioRecorder
from transcriber import Transcriber
from text_inserter import TextInserter
from hotkey_manager import HotkeyManager, TriggerMode
from hud_window import create_hud, HudState
from tray_icon import TrayIcon

ASSETS_DIR = Path(__file__).parent / "assets"
MIC_ICON = ASSETS_DIR / "mic.png"


class GoodVoiceApp:
    def __init__(self):
        self._app = QApplication.instance() or QApplication(sys.argv)
        # Set app icon for taskbar and window
        icon_path = Path(__file__).parent / "assets" / "icon.png"
        if icon_path.exists():
            self._app.setWindowIcon(QIcon(str(icon_path)))

        self.settings = Settings().load()
        print(f"Settings: model={self.settings.model_size}, lang={self.settings.language}, mode={self.settings.trigger_mode}")

        self.recorder = AudioRecorder()
        self.transcriber = Transcriber(model_size=self.settings.model_size)
        self.inserter = TextInserter()
        self.hud = create_hud(self.settings.hud_theme)
        print(f"HUD theme: {self.settings.hud_theme}")
        self.hotkey = HotkeyManager(
            mode=TriggerMode(self.settings.trigger_mode)
        )
        self.tray = TrayIcon(str(MIC_ICON))
        self._running = False
        self.stats = Stats().load()
        self.history = History().load()
        self._rec_start = 0.0
        self._settings_win = None
        self._hud_visible = True

        self._q = queue.Queue()
        self.recorder.on_volume = lambda rms: self._q.put(("rms", rms))

    def _cmd(self, *args):
        self._q.put(args)

    def _process_queue(self):
        while not self._q.empty():
            try:
                cmd = self._q.get_nowait()
                action = cmd[0]
                if action == "rms":
                    self.hud.set_rms(cmd[1])
                elif action == "state":
                    self.hud.set_state(cmd[1])
                elif action == "text":
                    self.hud.set_text(cmd[1])
                elif action == "lang":
                    self.hud.set_language(cmd[1])
                elif action == "show":
                    self.hud.show()
                elif action == "hide":
                    self.hud.hide()
            except queue.Empty:
                break

    def start(self):
        print("GoodVoice: загрузка модели...")
        self.transcriber.load_model()
        print("GoodVoice: модель загружена.")

        self.hotkey.on_start = self._on_record_start
        self.hotkey.on_stop = self._on_record_stop
        self.hotkey.on_cancel = self._on_record_cancel
        self.hotkey.on_settings = lambda: self._q.put(("open_settings",))

        self.tray.on_show = lambda: self._cmd("show")
        self.tray.on_hide = lambda: self._cmd("hide")
        self.tray.on_quit = lambda: self._q.put(("quit",))

        self.hotkey.start()
        self.tray.start()
        self._running = True

        self._poll = QTimer()
        self._poll.timeout.connect(self._process_queue)
        self._poll.start(16)

        # Process queue for settings/quit commands
        self._cmd_timer = QTimer()
        self._cmd_timer.timeout.connect(self._process_commands)
        self._cmd_timer.start(16)

        print("GoodVoice: готово! Нажмите Right Ctrl для записи.")
        print("GoodVoice: Right Alt+P — открыть настройки.")
        self._cmd("state", HudState.IDLE)

        sys.exit(self._app.exec())

    def _process_commands(self):
        # Check tray commands
        tray_cmd = self.tray.get_command()
        if tray_cmd == "toggle_hud":
            self._cmd("show" if not self._hud_visible else "hide")
            self._hud_visible = not self._hud_visible
        elif tray_cmd == "open_settings":
            self._open_settings()
        elif tray_cmd == "quit":
            self._quit()
            return

        # Check internal queue
        while not self._q.empty():
            try:
                cmd = self._q.get_nowait()
                if cmd[0] == "open_settings":
                    self._open_settings()
                elif cmd[0] == "quit":
                    self._quit()
                    return
                else:
                    self._q.put(cmd)
                    break
            except queue.Empty:
                break

    def _open_settings(self):
        print("[UI] opening settings...")
        from settings_window import SettingsWindow
        self._settings_win = SettingsWindow()
        self._settings_win.show()
        self._settings_win.activateWindow()
        self._settings_win.raise_()

    def _on_record_start(self):
        print("[REC] запись...")
        self._rec_start = time.time()
        self.recorder.start()
        lang = self.settings.language.upper() if self.settings.language != "auto" else "AUTO"
        self._cmd("state", HudState.RECORDING)
        self._cmd("text", "")
        self._cmd("lang", lang)

    def _on_record_stop(self):
        print("[REC] остановка...")
        self._cmd("state", HudState.THINKING)

        audio = self.recorder.stop()

        if len(audio) < 1600:
            print("[REC] слишком коротко")
            self._cmd("text", "Тишина")
            time.sleep(1.0)
            self._cmd("state", HudState.HIDDEN)
            return

        print(f"[REC] аудио: {len(audio)/16000:.1f}с, распознавание...")

        def _do_transcribe():
            try:
                text = self.transcriber.transcribe(
                    audio,
                    language=self.settings.language,
                    punctuation=self.settings.punctuation,
                )
                print(f"[REC] результат: '{text}'")

                if text and text.strip():
                    duration = time.time() - self._rec_start
                    self.stats.add_session(text, duration)
                    self.history.add(text)
                    success = self.inserter.insert(text)
                    print(f"[REC] вставка: {'OK' if success else 'ОШИБКА'}")
                    self._cmd("state", HudState.SUCCESS)
                    time.sleep(1.2)
                    self._cmd("state", HudState.HIDDEN)
                else:
                    self._cmd("text", "Тишина")
                    time.sleep(1.0)
                    self._cmd("state", HudState.HIDDEN)

            except Exception as e:
                print(f"[REC] ошибка: {e}")
                self._cmd("text", "Ошибка")
                time.sleep(1.5)
                self._cmd("state", HudState.HIDDEN)

        threading.Thread(target=_do_transcribe, daemon=True).start()

    def _on_record_cancel(self):
        print("[REC] отмена")
        self.recorder.stop()
        self._cmd("text", "Отменено")
        time.sleep(0.8)
        self._cmd("state", HudState.HIDDEN)

    def _quit(self):
        self._running = False
        self.hotkey.stop()
        self.tray.stop()
        self.hud.hide()
        self._app.quit()


def main():
    app = GoodVoiceApp()
    app.start()


if __name__ == "__main__":
    main()
