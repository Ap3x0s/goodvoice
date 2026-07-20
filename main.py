"""GoodVoice — Windows voice dictation tool.

Press Left Ctrl to start dictation (hold or toggle mode).
Release to transcribe and paste text into the active field.
Press Escape to cancel without inserting.
"""

import sys
import threading
import time
from pathlib import Path

from settings import Settings
from audio_recorder import AudioRecorder
from transcriber import Transcriber
from text_inserter import TextInserter
from hotkey_manager import HotkeyManager, TriggerMode
from hud_window import HUDWindow
from tray_icon import TrayIcon

ASSETS_DIR = Path(__file__).parent / "assets"
MIC_ICON = ASSETS_DIR / "mic.png"


class GoodVoiceApp:
    def __init__(self):
        self.settings = Settings().load()
        self.recorder = AudioRecorder()
        self.transcriber = Transcriber(model_size=self.settings.model_size)
        self.inserter = TextInserter()
        self.hud = HUDWindow()
        self.hotkey = HotkeyManager(
            mode=TriggerMode(self.settings.trigger_mode)
        )
        self.tray = TrayIcon(str(MIC_ICON))
        self._running = False

    def start(self):
        print("GoodVoice: загрузка модели...")
        self.transcriber.load_model()
        print("GoodVoice: модель загружена.")

        self.hud.create()

        self.hotkey.on_start = self._on_record_start
        self.hotkey.on_stop = self._on_record_stop
        self.hotkey.on_cancel = self._on_record_cancel

        self.tray.on_show = self.hud.show
        self.tray.on_hide = self.hud.hide
        self.tray.on_quit = self._quit

        self.hotkey.start()
        self.tray.start()
        self._running = True

        print("GoodVoice: готово! Нажмите Left Ctrl для записи.")

        try:
            self.hud.run()
        except KeyboardInterrupt:
            self._quit()

    def _on_record_start(self):
        print("[REC] запись...")
        self.recorder.start()
        self.hud.set_recording(True)
        self.hud.update_text("Говорите...")
        self.hud.show()

    def _on_record_stop(self):
        print("[REC] остановка, распознавание...")
        self.hud.set_recording(False)
        self.hud.update_text("Распознавание...")

        audio = self.recorder.stop()

        if len(audio) < 1600:
            self.hud.update_text("Слишком коротко")
            time.sleep(0.5)
            self.hud.hide()
            return

        def _do_transcribe():
            text = self.transcriber.transcribe(
                audio,
                language=self.settings.language,
                punctuation=self.settings.punctuation,
            )
            if text:
                print(f"[REC] текст: {text}")
                self.hud.update_text(text)
                self.inserter.insert(text)
                time.sleep(0.3)
            else:
                self.hud.update_text("Ничего не распознано")
                time.sleep(0.5)
            self.hud.hide()

        threading.Thread(target=_do_transcribe, daemon=True).start()

    def _on_record_cancel(self):
        print("[REC] отмена")
        self.recorder.stop()
        self.hud.set_recording(False)
        self.hud.update_text("Отменено")
        time.sleep(0.5)
        self.hud.hide()

    def _quit(self):
        self._running = False
        self.hotkey.stop()
        self.tray.stop()
        self.hud.destroy()
        sys.exit(0)


def main():
    app = GoodVoiceApp()
    app.start()


if __name__ == "__main__":
    main()
