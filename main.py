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

        self.tray.on_show = self._hud_show
        self.tray.on_hide = self._hud_hide
        self.tray.on_quit = self._quit

        self.hotkey.start()
        self.tray.start()
        self._running = True

        print("GoodVoice: готово! Нажмите Right Ctrl для записи.")

        try:
            self.hud.run()
        except KeyboardInterrupt:
            self._quit()

    def _hud_show(self):
        if self._root():
            self._root().after(0, self.hud.show)

    def _hud_hide(self):
        if self._root():
            self._root().after(0, self.hud.hide)

    def _root(self):
        return self.hud._root

    def _on_record_start(self):
        print("[REC] запись...")
        self.recorder.start()
        if self._root():
            self._root().after(0, lambda: self.hud.set_recording(True))
            self._root().after(0, lambda: self.hud.update_text("\u0413\u043e\u0432\u043e\u0440\u0438\u0442\u0435..."))
            self._root().after(0, self.hud.show)

    def _on_record_stop(self):
        print("[REC] остановка, распознавание...")
        if self._root():
            self._root().after(0, lambda: self.hud.set_recording(False))
            self._root().after(0, lambda: self.hud.update_text("\u0420\u0430\u0441\u043f\u043e\u0437\u043d\u0430\u0432\u0430\u043d\u0438\u0435..."))

        audio = self.recorder.stop()

        if len(audio) < 1600:
            if self._root():
                self._root().after(0, lambda: self.hud.update_text("\u0421\u043b\u0438\u0448\u043a\u043e\u043c \u043a\u043e\u0440\u043e\u0442\u043a\u043e"))
                self._root().after(500, self.hud.hide)
            return

        def _do_transcribe():
            try:
                text = self.transcriber.transcribe(
                    audio,
                    language=self.settings.language,
                    punctuation=self.settings.punctuation,
                )
                if text:
                    print(f"[REC] текст: {text}")
                    if self._root():
                        self._root().after(0, lambda t=text: self.hud.update_text(t))
                    self.inserter.insert(text)
                    time.sleep(0.4)
                else:
                    if self._root():
                        self._root().after(0, lambda: self.hud.update_text("\u041d\u0438\u0447\u0435\u0433\u043e \u043d\u0435 \u0440\u0430\u0441\u043f\u043e\u0437\u043d\u0430\u043d\u043e"))
                    time.sleep(0.6)
            except Exception as e:
                print(f"[REC] ошибка: {e}")
                if self._root():
                    self._root().after(0, lambda: self.hud.update_text("\u041e\u0448\u0438\u0431\u043a\u0430"))
                    time.sleep(0.6)
            if self._root():
                self._root().after(0, self.hud.hide)

        threading.Thread(target=_do_transcribe, daemon=True).start()

    def _on_record_cancel(self):
        print("[REC] отмена")
        self.recorder.stop()
        if self._root():
            self._root().after(0, lambda: self.hud.set_recording(False))
            self._root().after(0, lambda: self.hud.update_text("\u041e\u0442\u043c\u0435\u043d\u0435\u043d\u043e"))
            self._root().after(500, self.hud.hide)

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
