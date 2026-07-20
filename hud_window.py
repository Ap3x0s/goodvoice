"""Floating HUD — modern animated capsule design like SuperDictate."""

import customtkinter as ctk
import math
import threading


class HUDWindow:
    def __init__(self):
        self._root = None
        self._canvas = None
        self._text_label = None
        self._status_label = None
        self._visible = False
        self._recording = False
        self._pulse_angle = 0.0
        self._wave_angles = [0.0, 0.8, 1.6, 2.4, 3.2]
        self._anim_id = None
        self._W = 420
        self._H = 80

    def create(self) -> None:
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self._root = ctk.CTk()
        self._root.title("GoodVoice")
        self._root.geometry(f"{self._W}x{self._H}")
        self._root.attributes("-topmost", True)
        self._root.overrideredirect(True)
        self._root.configure(fg_color="#11111b")
        self._root.resizable(False, False)

        # Main canvas for drawing
        self._canvas = ctk.CTkCanvas(
            self._root,
            width=self._W,
            height=self._H,
            highlightthickness=0,
            bg="#11111b",
        )
        self._canvas.pack(fill="both", expand=True)

        # Draw rounded pill background
        self._draw_pill()

        # Status text (left side)
        self._status_label = ctk.CTkLabel(
            self._root,
            text="\u25cf  Готов",
            font=ctk.CTkFont(family="Segoe UI Semibold", size=13),
            text_color="#585b70",
            anchor="w",
        )
        self._status_label.place(x=58, y=12)

        # Main text (center)
        self._text_label = ctk.CTkLabel(
            self._root,
            text="Нажмите Right Ctrl",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color="#bac2de",
            anchor="w",
        )
        self._text_label.place(x=58, y=38)

        # Center-bottom on screen
        self._root.update_idletasks()
        sw = self._root.winfo_screenwidth()
        sh = self._root.winfo_screenheight()
        x = (sw - self._W) // 2
        y = sh - 140
        self._root.geometry(f"{self._W}x{self._H}+{x}+{y}")

        self._root.withdraw()
        self._root.update()

    def _draw_pill(self) -> None:
        """Draw rounded rectangle pill background."""
        c = self._canvas
        w, h = self._W, self._H
        r = 20  # corner radius
        # Pill outline glow
        for i in range(3):
            offset = i
            color = "#1e1e2e" if i == 0 else "#181825" if i == 1 else "#11111b"
            c.create_arc(
                offset, offset, r * 2 + offset, h - offset,
                start=90, extent=90, fill=color, outline="", style="pieslice"
            )
            c.create_arc(
                w - r * 2 - offset, offset, w - offset, h - offset,
                start=0, extent=90, fill=color, outline="", style="pieslice"
            )
            c.create_arc(
                offset, offset, r * 2 + offset, h - offset,
                start=90, extent=90, fill=color, outline="", style="pieslice"
            )
            c.create_arc(
                w - r * 2 - offset, offset, w - offset, h - offset,
                start=0, extent=90, fill=color, outline="", style="pieslice"
            )
            c.create_rectangle(
                r + offset, offset, w - r - offset, h - offset,
                fill=color, outline=""
            )
            c.create_rectangle(
                offset, r + offset, w - offset, h - r - offset,
                fill=color, outline=""
            )

    def show(self) -> None:
        if self._root and not self._visible:
            self._visible = True
            try:
                self._root.deiconify()
                self._root.lift()
                self._root.focus_force()
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
        if self._text_label:
            try:
                self._text_label.configure(text=text)
                self._root.update()
            except Exception:
                pass

    def set_recording(self, recording: bool) -> None:
        self._recording = recording
        if recording:
            self._pulse_angle = 0.0
            self._wave_angles = [0.0, 0.8, 1.6, 2.4, 3.2]
            if self._status_label:
                self._status_label.configure(
                    text="\u25cf  Запись",
                    text_color="#f38ba8"
                )
            if self._text_label:
                self._text_label.configure(text="Говорите...")
            self._start_anim()
        else:
            self._stop_anim()
            if self._status_label:
                self._status_label.configure(
                    text="\u25cf  Обработка",
                    text_color="#fab387"
                )

    def set_ready(self) -> None:
        self._stop_anim()
        if self._status_label:
            self._status_label.configure(
                text="\u25cf  Готов",
                text_color="#585b70"
            )

    # --- Animation loop ---

    def _start_anim(self) -> None:
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

        self._pulse_angle += 0.12
        for i in range(len(self._wave_angles)):
            self._wave_angles[i] += 0.18 + i * 0.04

        # Draw wave bars on canvas
        try:
            self._draw_wave_bars()
        except Exception:
            pass

        self._anim_id = self._root.after(33, self._anim_tick)  # ~30fps

    def _draw_wave_bars(self) -> None:
        """Draw animated equalizer bars."""
        c = self._canvas
        # Delete old bars
        c.delete("wave")

        num_bars = 5
        bar_w = 6
        gap = 5
        total_w = num_bars * bar_w + (num_bars - 1) * gap
        start_x = 18
        base_y = self._H // 2 + 10
        max_h = 28

        for i in range(num_bars):
            angle = self._wave_angles[i]
            # Combine multiple sine waves for organic look
            h = abs(math.sin(angle)) * 0.6 + abs(math.sin(angle * 2.3)) * 0.25 + abs(math.sin(angle * 0.7)) * 0.15
            bar_h = max(4, int(h * max_h))

            x1 = start_x + i * (bar_w + gap)
            y1 = base_y - bar_h
            x2 = x1 + bar_w
            y2 = base_y

            # Color gradient from pink to mauve
            progress = h
            r = int(243 * progress + 166 * (1 - progress))
            g = int(139 * progress + 139 * (1 - progress))
            b = int(248 * progress + 229 * (1 - progress))
            color = f"#{r:02x}{g:02x}{b:02x}"

            c.create_rectangle(
                x1, y1, x2, y2,
                fill=color, outline="", tags="wave"
            )

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
