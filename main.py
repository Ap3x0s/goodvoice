"""GoodVoice — Windows voice dictation tool.

Press Right Ctrl to start dictation (hold or toggle mode).
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
        print(f"Settings: model={self.settings.model_size}, lang={self.settings.language}, mode={self.settings.trigger_mode}")
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
        self.hud.create()
        self.hud.show()
        self.hud.set_recording(False)
        self.hud.update_text("Загрузка модели...")

        print("GoodVoice: загрузка модели...")
        self.transcriber.load_model()
        print("GoodVoice: модель загружена.")

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
        self.hud.set_ready()
        self.hud.update_text("Нажмите Right Ctrl")

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
            self._root().after(0, self.hud.show)

    def _on_record_stop(self):
        print("[REC] остановка, распознавание...")
        if self._root():
            self._root().after(0, lambda: self.hud.set_recording(False))

        audio = self.recorder.stop()

        if len(audio) < 1600:
            print("[REC] слишком коротко")
            if self._root():
                self._root().after(0, lambda: self.hud.update_text("Слишком коротко"))
                self._root().after(800, lambda: self.hud.set_ready())
                self._root().after(800, lambda: self.hud.update_text("Нажмите Right Ctrl"))
            return

        print(f"[REC] аудио: {len(audio)/16000:.1f}с, распознавание...")
        if self._root():
            self._root().after(0, lambda: self.hud.update_text("Распознавание..."))

        def _do_transcribe():
            try:
                text = self.transcriber.transcribe(
                    audio,
                    language=self.settings.language,
                    punctuation=self.settings.punctuation,
                )
                print(f"[REC] результат: '{text}'")

                if text and text.strip():
                    # Show text in HUD
                    if self._root():
                        self._root().after(0, lambda t=text: self.hud.update_text(t))

                    # Small delay then insert
                    time.sleep(0.3)
                    success = self.inserter.insert(text)
                    print(f"[REC] вставка: {'OK' if success else 'ОШИБКА'}")

                    if self._root():
                        if success:
                            self._root().after(0, lambda: self.hud.update_text("Вставлено ✓"))
                        else:
                            self._root().after(0, lambda: self.hud.update_text("Не удалось вставить"))
                        self._root().after(1200, lambda: self.hud.set_ready())
                        self._root().after(1200, lambda: self.hud.update_text("Нажмите Right Ctrl"))
                else:
                    if self._root():
                        self._root().after(0, lambda: self.hud.update_text("Ничего не распознано"))
                        self._root().after(1000, lambda: self.hud.set_ready())
                        self._root().after(1000, lambda: self.hud.update_text("Нажмите Right Ctrl"))

            except Exception as e:
                print(f"[REC] ошибка: {e}")
                if self._root():
                    self._root().after(0, lambda: self.hud.update_text(f"Ошибка: {str(e)[:40]}"))
                    self._root().after(2000, lambda: self.hud.set_ready())
                    self._root().after(2000, lambda: self.hud.update_text("Нажмите Right Ctrl"))

        threading.Thread(target=_do_transcribe, daemon=True).start()

    def _on_record_cancel(self):
        print("[REC] отмена")
        self.recorder.stop()
        if self._root():
            self._root().after(0, lambda: self.hud.set_recording(False))
            self._root().after(0, lambda: self.hud.update_text("Отменено"))
            self._root().after(800, lambda: self.hud.set_ready())
            self._root().after(800, lambda: self.hud.update_text("Нажмите Right Ctrl"))

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
