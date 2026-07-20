"""Insert transcribed text into the active text field using Win32 API."""

import time
import subprocess
import ctypes


VK_CONTROL = 0x11
VK_V = 0x56
INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", ctypes.c_ushort),
        ("wScan", ctypes.c_ushort),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_ulong),
        ("ki", KEYBDINPUT),
        ("padding", ctypes.c_byte * 8),
    ]


def _press(vk):
    inp = INPUT(type=INPUT_KEYBOARD, ki=KEYBDINPUT(wVk=vk))
    ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))


def _release(vk):
    inp = INPUT(type=INPUT_KEYBOARD, ki=KEYBDINPUT(wVk=vk, dwFlags=KEYEVENTF_KEYUP))
    ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))


def _ctrl_v():
    _press(VK_CONTROL)
    _press(VK_V)
    time.sleep(0.02)
    _release(VK_V)
    _release(VK_CONTROL)


class TextInserter:
    def __init__(self, paste_delay: float = 0.3):
        self.paste_delay = paste_delay

    def insert(self, text: str) -> bool:
        if not text:
            return False

        # Give target window time to be ready
        time.sleep(0.15)

        # Method 1: pyperclip + ctypes Ctrl+V
        try:
            return self._insert_via_pyperclip(text)
        except Exception as e:
            print(f"pyperclip failed: {e}")

        # Method 2: PowerShell clipboard + ctypes Ctrl+V
        try:
            return self._insert_via_powershell(text)
        except Exception as e:
            print(f"PowerShell failed: {e}")

        return False

    def _insert_via_pyperclip(self, text: str) -> bool:
        """Set clipboard via pyperclip, paste via ctypes."""
        import pyperclip

        old_clipboard = ""
        try:
            old_clipboard = pyperclip.paste()
        except Exception:
            pass

        pyperclip.copy(text)
        time.sleep(self.paste_delay)

        _ctrl_v()
        time.sleep(0.2)

        try:
            pyperclip.copy(old_clipboard)
        except Exception:
            pass

        return True

    def _insert_via_powershell(self, text: str) -> bool:
        """Set clipboard via PowerShell, paste via ctypes."""
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
        _ctrl_v()
        time.sleep(0.2)
        return True
