"""Floating HUD — SuperDictate-inspired minimalist capsule."""

import customtkinter as ctk
import math


class HUDWindow:
    """Small animated pill that shows dictation status and result."""

    W = 320
    H = 56
    RADIUS = 28  # half-height = perfect pill
    BG = "#181825"
    BG_RECORDING = "#1e1e2e"
    TEXT_DIM = "#6c7086"
    TEXT_NORMAL = "#cdd6f4"
    TEXT_BRIGHT = "#f5e0dc"
    ACCENT = "#f38ba8"      # pink
    ACCENT2 = "#fab387"     # peach
    ACCENT3 = "#a6e3a1"     # green

    def __init__(self):
        self._root = None
        self._canvas = None
        self._text_var = None
        self._visible = False
        self._recording = False
        self._wave_phase = 0.0
        self._anim_id = None

    def create(self) -> None:
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self._root = ctk.CTk()
        self._root.title("GoodVoice")
        self._root.geometry(f"{self.W}x{self.H}")
        self._root.attributes("-topmost", True)
        self._root.overrideredirect(True)
        self._root.configure(fg_color="black")
        self._root.resizable(False, False)

        # Canvas for custom drawing
        self._canvas = ctk.CTkCanvas(
            self._root,
            width=self.W,
            height=self.H,
            highlightthickness=0,
            bg="black",
        )
        self._canvas.pack(fill="both", expand=True)

        # Text variable
        self._text_var = ctk.StringVar(value="Right Ctrl")

        # Text label
        self._text_label = ctk.CTkLabel(
            self._root,
            textvariable=self._text_var,
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color=self.TEXT_NORMAL,
        )
        self._text_label.place(relx=0.5, rely=0.5, anchor="center")

        # Position: bottom center
        self._root.update_idletasks()
        sw = self._root.winfo_screenwidth()
        sh = self._root.winfo_screenheight()
        x = (sw - self.W) // 2
        y = sh - 100
        self._root.geometry(f"{self.W}x{self.H}+{x}+{y}")

        self._root.withdraw()
        self._root.update()

    def show(self) -> None:
        if self._root and not self._visible:
            self._visible = True
            try:
                self._root.deiconify()
                self._root.lift()
                self._root.update()
            except Exception:
                pass

    def hide(self) -> None:
        if self._root and self._visible:
            self._visible = False
            self._stop_anim()
            try:
                self._root.withdraw()
                self._root.update()
            except Exception:
                pass

    def update_text(self, text: str) -> None:
        if self._text_var:
            try:
                self._text_var.set(text)
                self._root.update()
            except Exception:
                pass

    def set_recording(self, recording: bool) -> None:
        self._recording = recording
        if recording:
            self._wave_phase = 0.0
            self._text_label.configure(text_color=self.ACCENT)
            self._start_anim()
        else:
            self._stop_anim()
            self._text_label.configure(text_color=self.TEXT_NORMAL)
            self._draw_pill(self.BG)

    def set_ready(self) -> None:
        self._stop_anim()
        if self._text_label:
            self._text_label.configure(text_color=self.TEXT_DIM)

    # --- Pill drawing ---

    def _draw_pill(self, bg_color: str) -> None:
        c = self._canvas
        c.delete("pill")
        w, h, r = self.W, self.H, self.RADIUS

        # Filled pill
        c.create_oval(0, 0, r * 2, h, fill=bg_color, outline="", tags="pill")
        c.create_oval(w - r * 2, 0, w, h, fill=bg_color, outline="", tags="pill")
        c.create_rectangle(r, 0, w - r, h, fill=bg_color, outline="", tags="pill")

    # --- Animation ---

    def _start_anim(self) -> None:
        self._draw_pill(self.BG_RECORDING)
        self._anim_tick()

    def _stop_anim(self) -> None:
        self._recording = False
        if self._anim_id and self._root:
            try:
                self._root.after_cancel(self._anim_id)
            except Exception:
                pass
            self._anim_id = None

    def _anim_tick(self) -> None:
        if not self._recording or not self._root:
            return

        self._wave_phase += 0.2
        self._draw_wave()
        self._anim_id = self._root.after(33, self._anim_tick)

    def _draw_wave(self) -> None:
        c = self._canvas
        c.delete("wave")

        num = 5
        bar_w = 4
        gap = 4
        start_x = 20
        base_y = self.H // 2 + 8
        max_h = 18

        for i in range(num):
            phase = self._wave_phase + i * 0.7
            h = abs(math.sin(phase)) * 0.7 + abs(math.sin(phase * 1.8)) * 0.3
            bar_h = max(3, int(h * max_h))

            x1 = start_x + i * (bar_w + gap)
            y1 = base_y - bar_h
            x2 = x1 + bar_w
            y2 = base_y

            # Color: pink with varying intensity
            intensity = 0.5 + 0.5 * h
            r = int(243 * intensity + 100 * (1 - intensity))
            g = int(139 * intensity + 80 * (1 - intensity))
            b = int(248 * intensity + 120 * (1 - intensity))
            color = f"#{r:02x}{g:02x}{b:02x}"

            c.create_rectangle(x1, y1, x2, y2, fill=color, outline="", tags="wave")

    def run(self) -> None:
        if self._root:
            self._root.mainloop()

    def destroy(self) -> None:
        self._stop_anim()
        if self._root:
            try:
                self._root.destroy()
            except Exception:
                pass
