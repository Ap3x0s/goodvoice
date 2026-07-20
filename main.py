"""GoodVoice — Windows voice dictation tool.

Press Right Ctrl to start dictation (hold or toggle mode).
Release to transcribe and paste text into the active field.
Press Escape to cancel without inserting.
"""

import sys
import threading
import time
import queue
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

        # Thread-safe queue for HUD updates from pynput thread
        self._hud_queue = queue.Queue()

        # Wire volume callback
        self.recorder.on_volume = self._on_volume

    def _on_volume(self, rms: float):
        self._hud_queue.put(("rms", rms))

    def _hud_update(self, state=None, text=None, language=None, rms=None):
        """Queue a HUD update (thread-safe)."""
        self._hud_queue.put(("update", state, text, language, rms))

    def _process_hud_queue(self):
        """Process queued HUD updates on the main thread."""
        while not self._hud_queue.empty():
            try:
                msg = self._hud_queue.get_nowait()
                if msg[0] == "rms":
                    self.hud.set_rms(msg[1])
                elif msg[0] == "update":
                    _, state, text, language, rms = msg
                    if state is not None:
                        self.hud.set_state(state)
                    if text is not None:
                        self.hud.set_text(text)
                    if language is not None:
                        self.hud.set_language(language)
                    if rms is not None:
                        self.hud.set_rms(rms)
            except queue.Empty:
                break

    def start(self):
        print("GoodVoice: загрузка модели...")
        self.transcriber.load_model()
        print("GoodVoice: модель загружена.")

        self.hotkey.on_start = self._on_record_start
        self.hotkey.on_stop = self._on_record_stop
        self.hotkey.on_cancel = self._on_record_cancel

        self.tray.on_show = lambda: self._hud_update(state=HudState.IDLE)
        self.tray.on_hide = lambda: self._hud_update(state=HudState.HIDDEN)
        self.tray.on_quit = self._quit

        self.hotkey.start()
        self.tray.start()
        self._running = True

        # Poll queue every 16ms
        self._poll_timer = QTimer()
        self._poll_timer.timeout.connect(self._process_hud_queue)
        self._poll_timer.start(16)

        print("GoodVoice: готово! Нажмите Right Ctrl для записи.")
        self.hud.set_state(HudState.IDLE)

        sys.exit(self._app.exec())

    def _on_record_start(self):
        print("[REC] запись...")
        self.recorder.start()
        lang = self.settings.language.upper() if self.settings.language != "auto" else "AUTO"
        self._hud_update(state=HudState.RECORDING, text="", language=lang)

    def _on_record_stop(self):
        print("[REC] остановка...")
        self._hud_update(state=HudState.THINKING, text="")

        audio = self.recorder.stop()

        if len(audio) < 1600:
            print("[REC] слишком коротко")
            self._hud_update(text="Тишина")
            time.sleep(0.8)
            self._hud_update(state=HudState.HIDDEN)
            return

        print(f"[REC] аудио: {len(audio)/16000:.1f}с, распознавание...")
        self._hud_update(text="Распознавание...")

        def _do_transcribe():
            try:
                text = self.transcriber.transcribe(
                    audio,
                    language=self.settings.language,
                    punctuation=self.settings.punctuation,
                )
                print(f"[REC] результат: '{text}'")

                if text and text.strip():
                    # Show recognized text for 1.5 seconds
                    self._hud_update(text=text)
                    time.sleep(1.5)

                    # Insert text
                    success = self.inserter.insert(text)
                    print(f"[REC] вставка: {'OK' if success else 'ОШИБКА'}")

                    # Show success for 1.5 seconds
                    if success:
                        self._hud_update(state=HudState.SUCCESS, text="Вставлено")
                    else:
                        self._hud_update(state=HudState.SUCCESS, text="Ошибка вставки")
                    time.sleep(1.5)

                    # Hide
                    self._hud_update(state=HudState.HIDDEN)
                else:
                    self._hud_update(text="Тишина")
                    time.sleep(1.0)
                    self._hud_update(state=HudState.HIDDEN)

            except Exception as e:
                print(f"[REC] ошибка: {e}")
                self._hud_update(text=f"Ошибка: {str(e)[:30]}")
                time.sleep(1.5)
                self._hud_update(state=HudState.HIDDEN)

        threading.Thread(target=_do_transcribe, daemon=True).start()

    def _on_record_cancel(self):
        print("[REC] отмена")
        self.recorder.stop()
        self._hud_update(state=HudState.SUCCESS, text="Отменено")
        time.sleep(0.8)
        self._hud_update(state=HudState.HIDDEN)

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
