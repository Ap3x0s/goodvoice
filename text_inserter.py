"""Insert transcribed text into the active text field."""

import time
import subprocess


class TextInserter:
    def __init__(self, paste_delay: float = 0.15):
        self.paste_delay = paste_delay

    def insert(self, text: str) -> bool:
        if not text:
            return False

        # Method 1: pyperclip + pyautogui (most reliable)
        try:
            return self._insert_via_pyperclip(text)
        except Exception as e1:
            print(f"pyperclip failed: {e1}")

        # Method 2: PowerShell clipboard
        try:
            return self._insert_via_powershell(text)
        except Exception as e2:
            print(f"PowerShell failed: {e2}")

        # Method 3: type character by character
        try:
            return self._insert_via_typing(text)
        except Exception as e3:
            print(f"Typing failed: {e3}")
            return False

    def _insert_via_pyperclip(self, text: str) -> bool:
        """Use pyperclip + Ctrl+V."""
        import pyperclip
        import pyautogui

        old_clipboard = ""
        try:
            old_clipboard = pyperclip.paste()
        except Exception:
            pass

        pyperclip.copy(text)
        time.sleep(self.paste_delay)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.1)

        try:
            pyperclip.copy(old_clipboard)
        except Exception:
            pass

        return True

    def _insert_via_powershell(self, text: str) -> bool:
        """Use PowerShell to set clipboard, then Ctrl+V."""
        import pyautogui

        escaped = text.replace("'", "''")
        cmd = f"Set-Clipboard -Value '{escaped}'"
        subprocess.run(
            ["powershell", "-Command", cmd],
            capture_output=True,
            timeout=5,
        )
        time.sleep(self.paste_delay)
        pyautogui.hotkey("ctrl", "v")
        return True

    def _insert_via_typing(self, text: str) -> bool:
        """Type text using pyautogui.write."""
        import pyautogui

        pyautogui.write(text, interval=0.02)
        return True
