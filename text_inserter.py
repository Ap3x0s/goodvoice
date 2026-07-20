"""Insert transcribed text into the active text field."""

import time
import subprocess


class TextInserter:
    def __init__(self, paste_delay: float = 0.5):
        self.paste_delay = paste_delay

    def insert(self, text: str) -> bool:
        if not text:
            return False

        # Give target window time to receive focus
        time.sleep(0.2)

        # Method 1: PowerShell clipboard + Ctrl+V
        try:
            return self._insert_via_powershell(text)
        except Exception as e:
            print(f"PowerShell failed: {e}")

        # Method 2: pyperclip + Ctrl+V
        try:
            return self._insert_via_pyperclip(text)
        except Exception as e:
            print(f"pyperclip failed: {e}")

        # Method 3: type character by character
        try:
            return self._insert_via_typing(text)
        except Exception as e:
            print(f"Typing failed: {e}")
            return False

    def _insert_via_powershell(self, text: str) -> bool:
        """Use PowerShell to set clipboard, then Ctrl+V."""
        import pyautogui

        escaped = text.replace("'", "''")
        cmd = f"Set-Clipboard -Value '{escaped}'"
        result = subprocess.run(
            ["powershell", "-Command", cmd],
            capture_output=True,
            timeout=5,
        )
        if result.returncode != 0:
            raise RuntimeError(f"PowerShell error: {result.stderr}")

        time.sleep(self.paste_delay)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.3)
        return True

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
        time.sleep(0.3)

        try:
            pyperclip.copy(old_clipboard)
        except Exception:
            pass

        return True

    def _insert_via_typing(self, text: str) -> bool:
        """Type text using pyautogui."""
        import pyautogui
        pyautogui.write(text, interval=0.02)
        return True
