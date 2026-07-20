"""Global hotkey listener using pynput."""

from pynput import keyboard
from enum import Enum


class TriggerMode(Enum):
    HOLD = "hold"
    TOGGLE = "toggle"


class HotkeyManager:
    def __init__(self, mode: TriggerMode = TriggerMode.HOLD):
        self.mode = mode
        self._listener = None
        self._recording = False
        self.on_start = None
        self.on_stop = None
        self.on_cancel = None

    def start(self) -> None:
        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self._listener.start()

    def stop(self) -> None:
        if self._listener:
            self._listener.stop()
            self._listener = None

    def _on_press(self, key):
        if key == keyboard.Key.ctrl_r:
            if self.mode == TriggerMode.HOLD:
                if not self._recording:
                    self._recording = True
                    if self.on_start:
                        self.on_start()
            elif self.mode == TriggerMode.TOGGLE:
                if self._recording:
                    self._recording = False
                    if self.on_stop:
                        self.on_stop()
                else:
                    self._recording = True
                    if self.on_start:
                        self.on_start()
        elif key == keyboard.Key.esc:
            if self._recording:
                self._recording = False
                if self.on_cancel:
                    self.on_cancel()

    def _on_release(self, key):
        if key == keyboard.Key.ctrl_r and self.mode == TriggerMode.HOLD:
            if self._recording:
                self._recording = False
                if self.on_stop:
                    self.on_stop()

    @property
    def is_recording(self) -> bool:
        return self._recording
