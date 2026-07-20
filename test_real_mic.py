"""Test real microphone → HUD response."""
import sys
import time
import threading
sys.path.insert(0, r"C:\Users\Евгений\Desktop\Projects\goodvoice")

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from audio_recorder import AudioRecorder
from hud_hybrid_v2 import HudWidget, HudState


def main():
    app = QApplication(sys.argv)
    hud = HudWidget()
    recorder = AudioRecorder()

    # Wire RMS → HUD
    def on_vol(rms):
        QTimer.singleShot(0, lambda r=rms: hud.set_rms(r))
    recorder.on_volume = on_vol

    hud.show()
    hud.set_state(HudState.RECORDING)
    print("ГОВОРИТЕ В МИКРОФОН — проверьте что бары и круг реагируют!")
    print("Нажмите Ctrl+C для выхода...")

    recorder.start()

    # Keep alive
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        pass
    finally:
        recorder.stop()
        hud.destroy()


if __name__ == "__main__":
    main()
