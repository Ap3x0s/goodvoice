"""Floating HUD window — modern minimalist design."""

import customtkinter as ctk
import math
import threading


class HUDWindow:
    def __init__(self):
        self._root = None
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
        self._root.overrideredirect(True)
        self._root.configure(fg_color="#1e1e2e")
        self._root.resizable(False, False)

        # Mic icon
        self._mic_label = ctk.CTkLabel(
            self._root,
            text="\u25cf",
            font=ctk.CTkFont(size=22),
            text_color="#6c7086",
            width=40,
        )
        self._mic_label.place(x=18, y=25)

        # Transcription text
        self._text_label = ctk.CTkLabel(
            self._root,
            text="\u0413\u043e\u0442\u043e\u0432",
            font=ctk.CTkFont(family="Segoe UI", size=15),
            text_color="#cdd6f4",
            anchor="w",
            width=280,
        )
        self._text_label.place(x=58, y=24)

        # Center-bottom on screen
        self._root.update_idletasks()
        sw = self._root.winfo_screenwidth()
        sh = self._root.winfo_screenheight()
        x = (sw - 360) // 2
        y = sh - 120
        self._root.geometry(f"360x72+{x}+{y}")

        # Start hidden
        self._root.withdraw()
        self._root.update()

    def show(self) -> None:
        if self._root and not self._visible:
            self._visible = True
            try:
                self._root.deiconify()
                self._root.lift()
                self._root.focus_force()
                self._root.update()
            except Exception as e:
                print(f"HUD show error: {e}")

    def hide(self) -> None:
        if self._root and self._visible:
            self._visible = False
            self._stop_pulse()
            try:
                self._root.withdraw()
                self._root.update()
            except Exception as e:
                print(f"HUD hide error: {e}")

    def update_text(self, text: str) -> None:
        if self._text_label:
            try:
                self._text_label.configure(text=text)
                self._root.update()
            except Exception:
                pass

    def set_recording(self, recording: bool) -> None:
        self._recording = recording
        if recording:
            self._start_pulse()
        else:
            self._stop_pulse()
            if self._mic_label:
                try:
                    self._mic_label.configure(text_color="#6c7086")
                except Exception:
                    pass

    def _start_pulse(self) -> None:
        self._pulse_angle = 0
        self._pulse_tick()

    def _stop_pulse(self) -> None:
        self._recording = False
        if self._pulse_after_id and self._root:
            try:
                self._root.after_cancel(self._pulse_after_id)
            except Exception:
                pass
            self._pulse_after_id = None

    def _pulse_tick(self) -> None:
        if not self._recording or not self._root:
            return
        self._pulse_angle += 0.18
        brightness = 0.5 + 0.5 * math.sin(self._pulse_angle)
        r = int(243 * brightness + 100 * (1 - brightness))
        g = int(139 * brightness + 80 * (1 - brightness))
        b = int(248 * brightness + 100 * (1 - brightness))
        color = f"#{r:02x}{g:02x}{b:02x}"
        try:
            self._mic_label.configure(text_color=color)
        except Exception:
            pass
        self._pulse_after_id = self._root.after(30, self._pulse_tick)

    def run(self) -> None:
        if self._root:
            self._root.mainloop()

    def destroy(self) -> None:
        self._stop_pulse()
        if self._root:
            try:
                self._root.destroy()
            except Exception:
                pass
