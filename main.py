"""GoodVoice — Windows voice dictation tool.

Press Right Ctrl to start dictation (hold or toggle mode).
Release to transcribe and paste text into the active field.
Press Escape to cancel without inserting.
"""

import sys
import threading
import time
from pathlib import Path

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

from settings import Settings
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

        self.recorder.on_volume = self._on_volume

    def _on_volume(self, rms: float):
        QTimer.singleShot(0, lambda r=rms: self.hud.set_rms(r))

    def start(self):
        print("GoodVoice: загрузка модели...")
        self.transcriber.load_model()
        print("GoodVoice: модель загружена.")

        self.hotkey.on_start = self._on_record_start
        self.hotkey.on_stop = self._on_record_stop
        self.hotkey.on_cancel = self._on_record_cancel

        self.tray.on_show = lambda: QTimer.singleShot(0, self.hud.show)
        self.tray.on_hide = lambda: QTimer.singleShot(0, self.hud.hide)
        self.tray.on_quit = self._quit

        self.hotkey.start()
        self.tray.start()
        self._running = True

        print("GoodVoice: готово! Нажмите Right Ctrl для записи.")
        self.hud.set_state(HudState.IDLE)

        sys.exit(self._app.exec())

    def _hud(self, func, *args, **kwargs):
        """Call HUD method on main thread."""
        QTimer.singleShot(0, lambda: func(*args, **kwargs))

    def _on_record_start(self):
        print("[REC] запись...")
        self.recorder.start()
        lang = self.settings.language.upper() if self.settings.language != "auto" else "AUTO"
        self._hud(self.hud.set_state, HudState.RECORDING)
        self._hud(self.hud.set_text, "")
        self._hud(self.hud.set_language, lang)

    def _on_record_stop(self):
        print("[REC] остановка...")
        self._hud(self.hud.set_state, HudState.THINKING)

        audio = self.recorder.stop()

        if len(audio) < 1600:
            print("[REC] слишком коротко")
            self._hud(self.hud.set_text, "Тишина")
            QTimer.singleShot(1000, lambda: self._hud(self.hud.set_state, HudState.HIDDEN))
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
                    success = self.inserter.insert(text)
                    print(f"[REC] вставка: {'OK' if success else 'ОШИБКА'}")
                    self._hud(self.hud.set_state, HudState.SUCCESS)
                    time.sleep(1.2)
                    self._hud(self.hud.set_state, HudState.HIDDEN)
                else:
                    self._hud(self.hud.set_text, "Тишина")
                    time.sleep(1.0)
                    self._hud(self.hud.set_state, HudState.HIDDEN)

            except Exception as e:
                print(f"[REC] ошибка: {e}")
                self._hud(self.hud.set_text, "Ошибка")
                time.sleep(1.5)
                self._hud(self.hud.set_state, HudState.HIDDEN)

        threading.Thread(target=_do_transcribe, daemon=True).start()

    def _on_record_cancel(self):
        print("[REC] отмена")
        self.recorder.stop()
        self._hud(self.hud.set_text, "Отменено")
        self._hud(self.hud.set_state, HudState.HIDDEN)

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
