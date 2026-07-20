"""Floating HUD window using CustomTkinter."""

import customtkinter as ctk


class HUDWindow:
    def __init__(self):
        self._root = None
        self._text_label = None
        self._status_label = None
        self._visible = False

    def create(self) -> None:
        """Create the HUD window (must be called from main thread)."""
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self._root = ctk.CTk()
        self._root.title("GoodVoice")
        self._root.geometry("400x120")
        self._root.attributes("-topmost", True)
        self._root.attributes("-alpha", 0.85)
        self._root.overrideredirect(True)
        self._root.configure(fg_color="#1a1a2e")

        # Center on screen
        self._root.update_idletasks()
        w, h = 400, 120
        x = (self._root.winfo_screenwidth() - w) // 2
        y = (self._root.winfo_screenheight() - h) // 2
        self._root.geometry(f"{w}x{h}+{x}+{y}")

        # Status indicator
        self._status_label = ctk.CTkLabel(
            self._root,
            text="● Готов к записи",
            font=ctk.CTkFont(size=14),
            text_color="#4CAF50",
        )
        self._status_label.pack(pady=(15, 5))

        # Transcription text
        self._text_label = ctk.CTkLabel(
            self._root,
            text="",
            font=ctk.CTkFont(size=16),
            wraplength=360,
            justify="left",
        )
        self._text_label.pack(padx=20, pady=5, fill="both", expand=True)

        # Hide initially
        self._root.withdraw()

    def show(self) -> None:
        """Show the HUD window."""
        if self._root:
            self._root.after(0, self._root.deiconify)
            self._visible = True

    def hide(self) -> None:
        """Hide the HUD window."""
        if self._root:
            self._root.after(0, self._root.withdraw)
            self._visible = False

    def update_text(self, text: str) -> None:
        """Update the transcription text."""
        if self._text_label:
            self._text_label.after(
                0, lambda: self._text_label.configure(text=text)
            )

    def set_recording(self, recording: bool) -> None:
        """Update recording status indicator."""
        if self._status_label:
            if recording:
                self._status_label.after(
                    0,
                    lambda: self._status_label.configure(
                        text="● Запись...", text_color="#f44336"
                    ),
                )
            else:
                self._status_label.after(
                    0,
                    lambda: self._status_label.configure(
                        text="● Готов к записи", text_color="#4CAF50"
                    ),
                )

    def run(self) -> None:
        """Run the HUD main loop (blocking)."""
        if self._root:
            self._root.mainloop()

    def destroy(self) -> None:
        """Destroy the HUD window."""
        if self._root:
            self._root.after(0, self._root.destroy)
