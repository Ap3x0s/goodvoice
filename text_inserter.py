"""Insert transcribed text into the active text field."""

import time
import pyperclip
import pyautogui


class TextInserter:
    def __init__(self, paste_delay: float = 0.05):
        self.paste_delay = paste_delay

    def insert(self, text: str) -> bool:
        if not text:
            return False

        try:
            old_clipboard = pyperclip.paste()
            pyperclip.copy(text)
            time.sleep(self.paste_delay)
            pyautogui.hotkey("ctrl", "v")
            time.sleep(0.1)
            pyperclip.copy(old_clipboard)
            return True
        except Exception as e:
            print(f"Insert failed: {e}")
            return False
