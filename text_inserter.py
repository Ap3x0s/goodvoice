"""Insert transcribed text into the active text field."""

import time
import subprocess
import ctypes


class TextInserter:
    def __init__(self, paste_delay: float = 0.15):
        self.paste_delay = paste_delay

    def insert(self, text: str) -> bool:
        if not text:
            return False

        try:
            # Method 1: Win32 clipboard + Ctrl+V
            return self._insert_via_clipboard(text)
        except Exception as e1:
            print(f"Clipboard method failed: {e1}")
            try:
                # Method 2: PowerShell Set-Clipboard + Ctrl+V
                return self._insert_via_powershell(text)
            except Exception as e2:
                print(f"PowerShell method failed: {e2}")
                try:
                    # Method 3: Direct keyboard input
                    return self._insert_via_keyboard(text)
                except Exception as e3:
                    print(f"Keyboard method failed: {e3}")
                    return False

    def _insert_via_clipboard(self, text: str) -> bool:
        """Use Win32 API to set clipboard, then Ctrl+V."""
        import ctypes
        from ctypes import wintypes

        # Set clipboard
        CF_UNICODETEXT = 13
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        user32.OpenClipboard(0)
        user32.EmptyClipboard()

        data = text.encode("utf-16-le") + b"\x00\x00"
        h_mem = kernel32.GlobalAlloc(0x0042, len(data))
        p_mem = kernel32.GlobalLock(h_mem)
        ctypes.memmove(p_mem, data, len(data))
        kernel32.GlobalUnlock(h_mem)
        user32.SetClipboardData(CF_UNICODETEXT, h_mem)
        user32.CloseClipboard()

        time.sleep(self.paste_delay)

        # Simulate Ctrl+V
        self._press_key(0x11)  # VK_CONTROL
        self._press_key(0x56)  # VK_V
        self._release_key(0x56)
        self._release_key(0x11)

        return True

    def _insert_via_powershell(self, text: str) -> bool:
        """Use PowerShell to set clipboard."""
        escaped = text.replace("'", "''")
        cmd = f"Set-Clipboard -Value '{escaped}'"
        subprocess.run(
            ["powershell", "-Command", cmd],
            capture_output=True,
            timeout=5,
        )
        time.sleep(self.paste_delay)

        import pyautogui
        pyautogui.hotkey("ctrl", "v")
        return True

    def _insert_via_keyboard(self, text: str) -> bool:
        """Type text character by character using Win32."""
        import ctypes

        user32 = ctypes.windll.user32

        for char in text:
            # Use SendInput with Unicode
            self._send_unicode_char(char)
            time.sleep(0.01)

        return True

    def _send_unicode_char(self, char: str) -> None:
        """Send a single Unicode character via SendInput."""
        import ctypes
        from ctypes import wintypes

        INPUT_KEYBOARD = 1
        KEYEVENTF_UNICODE = 0x0004

        class KEYBDINPUT(ctypes.Structure):
            _fields_ = [
                ("wVk", wintypes.WORD),
                ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
            ]

        class INPUT(ctypes.Structure):
            _fields_ = [
                ("type", wintypes.DWORD),
                ("ki", KEYBDINPUT),
                ("padding", ctypes.c_byte * 8),
            ]

        scan = ord(char)
        down = INPUT(
            type=INPUT_KEYBOARD,
            ki=KEYBDINPUT(wVk=0, wScan=scan, dwFlags=KEYEVENTF_UNICODE),
        )
        up = INPUT(
            type=INPUT_KEYBOARD,
            ki=KEYBDINPUT(wVk=0, wScan=scan, dwFlags=KEYEVENTF_UNICODE | 0x0002),
        )

        arr = (INPUT * 2)(down, up)
        ctypes.windll.user32.SendInput(2, arr, ctypes.sizeof(INPUT))

    def _press_key(self, vk: int) -> None:
        import ctypes
        from ctypes import wintypes

        INPUT_KEYBOARD = 1
        KEYEVENTF_KEYUP = 0x0002

        class KEYBDINPUT(ctypes.Structure):
            _fields_ = [
                ("wVk", wintypes.WORD),
                ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
            ]

        class INPUT(ctypes.Structure):
            _fields_ = [
                ("type", wintypes.DWORD),
                ("ki", KEYBDINPUT),
                ("padding", ctypes.c_byte * 8),
            ]

        inp = INPUT(
            type=INPUT_KEYBOARD,
            ki=KEYBDINPUT(wVk=vk, wScan=0, dwFlags=0),
        )
        ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))

    def _release_key(self, vk: int) -> None:
        import ctypes
        from ctypes import wintypes

        INPUT_KEYBOARD = 1
        KEYEVENTF_KEYUP = 0x0002

        class KEYBDINPUT(ctypes.Structure):
            _fields_ = [
                ("wVk", wintypes.WORD),
                ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
            ]

        class INPUT(ctypes.Structure):
            _fields_ = [
                ("type", wintypes.DWORD),
                ("ki", KEYBDINPUT),
                ("padding", ctypes.c_byte * 8),
            ]

        inp = INPUT(
            type=INPUT_KEYBOARD,
            ki=KEYBDINPUT(wVk=vk, wScan=0, dwFlags=KEYEVENTF_KEYUP),
        )
        ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
