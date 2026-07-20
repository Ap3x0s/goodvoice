"""Floating HUD window — modern minimalist design like SuperDictate."""

import customtkinter as ctk
import math
import time


class HUDWindow:
    def __init__(self):
        self._root = None
        self._canvas = None
        self._text_label = None
        self._mic_label = None
        self._visible = False
        self._recording = False
        self._pulse_angle = 0
        self._pulse_after_id = None

    def create(self) -> None:
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self._root = ctk.CTk()
        self._root.title("GoodVoice")
        self._root.geometry("360x72")
        self._root.attributes("-topmost", True)
        self._root.attributes("-alpha", 0.0)
        self._root.overrideredirect(True)
        self._root.configure(fg_color="#1e1e2e")

        # Rounded rectangle via canvas
        self._canvas = ctk.CTkCanvas(
            self._root,
            width=360,
            height=72,
            highlightthickness=0,
            bg="#1e1e2e",
        )
        self._canvas.pack(fill="both", expand=True)

        # Mic icon (unicode circle that pulses)
        self._mic_label = ctk.CTkLabel(
            self._root,
            text="\u25cf",
            font=ctk.CTkFont(size=20),
            text_color="#6c7086",
            width=40,
        )
        self._mic_label.place(x=20, y=26)

        # Transcription text
        self._text_label = ctk.CTkLabel(
            self._root,
            text="\u0413\u043e\u0442\u043e\u0432",
            font=ctk.CTkFont(family="Segoe UI", size=15),
            text_color="#cdd6f4",
            anchor="w",
            width=280,
        )
        self._text_label.place(x=60, y=24)

        # Center on screen
        self._root.update_idletasks()
        sw = self._root.winfo_screenwidth()
        sh = self._root.winfo_screenheight()
        x = (sw - 360) // 2
        y = sh - 120
        self._root.geometry(f"360x72+{x}+{y}")

        self._root.withdraw()

    def show(self) -> None:
        if self._root and not self._visible:
            self._visible = True
            self._fade(0.0, 0.92, step=0.08)

    def hide(self) -> None:
        if self._root and self._visible:
            self._visible = False
            self._stop_pulse()
            self._fade(self._root.attributes("-alpha"), 0.0, step=-0.12)

    def _fade(self, start: float, end: float, step: float) -> None:
        if not self._root:
            return
        current = start
        if abs(step) < 0.001:
            return

        def _tick():
            nonlocal current
            if not self._root:
                return
            current += step
            if (step > 0 and current >= end) or (step < 0 and current <= end):
                self._root.attributes("-alpha", max(0.0, min(1.0, end)))
                if end == 0.0:
                    try:
                        self._root.withdraw()
                    except Exception:
                        pass
                return
            self._root.attributes("-alpha", max(0.0, min(1.0, current)))
            self._root.after(16, _tick)

        self._root.after(16, _tick)

    def update_text(self, text: str) -> None:
        if self._text_label:
            self._text_label.after(
                0, lambda: self._text_label.configure(text=text)
            )

    def set_recording(self, recording: bool) -> None:
        self._recording = recording
        if recording:
            self._start_pulse()
        else:
            self._stop_pulse()
            if self._mic_label:
                self._mic_label.after(
                    0, lambda: self._mic_label.configure(text_color="#6c7086")
                )

    def _start_pulse(self) -> None:
        self._pulse_angle = 0
        self._pulse_tick()

    def _stop_pulse(self) -> None:
        if self._pulse_after_id and self._root:
            self._root.after_cancel(self._pulse_after_id)
            self._pulse_after_id = None

    def _pulse_tick(self) -> None:
        if not self._recording or not self._root:
            return
        self._pulse_angle += 0.15
        brightness = 0.5 + 0.5 * math.sin(self._pulse_angle)
        r = int(243 * brightness + 100 * (1 - brightness))
        g = int(139 * brightness + 80 * (1 - brightness))
        b = int(248 * brightness + 100 * (1 - brightness))
        color = f"#{r:02x}{g:02x}{b:02x}"
        if self._mic_label:
            self._mic_label.configure(text_color=color)
        self._pulse_after_id = self._root.after(30, self._pulse_tick)

    def run(self) -> None:
        if self._root:
            self._root.mainloop()

    def destroy(self) -> None:
        self._stop_pulse()
        if self._root:
            try:
                self._root.after(0, self._root.destroy)
            except Exception:
                pass
