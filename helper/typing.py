"""
CharacterTyper module for simulating keyboard typing with different styles
(INSTANT, HUMAN_LIKE, MACHINE_GUN). Works on Windows and X11.
"""

import time
import random
import platform
import threading
import ctypes
import ctypes.wintypes
from enum import Enum, auto

try:
    import Xlib.display
except ImportError:
    Xlib = None


class TypingMode(Enum):
    """Typing behavior modes."""
    INSTANT = auto()
    HUMAN_LIKE = auto()
    MACHINE_GUN = auto()

class KEYBDINPUT(ctypes.Structure):
    """Windows keyboard input struct."""
    _fields_ = [
        ("wVk", ctypes.wintypes.WORD),
        ("wScan", ctypes.wintypes.WORD),
        ("dwFlags", ctypes.wintypes.DWORD),
        ("time", ctypes.wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.wintypes.ULONG)),
    ]

class CharacterTyper:
    """Simulates typing text character by character."""

    def __init__(self):
        self._typing_delay = (0.05, 0.2)
        self._error_rate = 0.005
        self._mode = TypingMode.HUMAN_LIKE
        self._stop_event = threading.Event()
        self._typing_thread = None

        if platform.system() == "Windows":
            self._send_input = self._windows_send_input
        elif Xlib:
            self._display = Xlib.display.Display()
            self._send_input = self._x11_send_input
        else:
            raise RuntimeError("Unsupported platform or missing Xlib.")


    class INPUT(ctypes.Structure):
        """Windows generic input struct."""
        _fields_ = [
            ("input_type", ctypes.wintypes.DWORD),
            ("ki", KEYBDINPUT),
            ("padding", ctypes.c_ubyte * 8),
        ]

    def _windows_send_input(self, char):
        """Send key input on Windows."""
        input_keyboard_const = 1
        keyeventf_unicode_flag = 0x4
        keyeventf_keyup_flag = 0x2

        i = self.INPUT()
        i.input_type = input_keyboard_const

        if char == "\n":
            i.ki.wVk = 0x0D
            i.ki.wScan = 0
            i.ki.dwFlags = 0
        else:
            i.ki.wVk = 0
            i.ki.wScan = ord(char)
            i.ki.dwFlags = keyeventf_unicode_flag

        i.ki.time = 0
        i.ki.dwExtraInfo = None

        ctypes.windll.user32.SendInput(1, ctypes.byref(i), ctypes.sizeof(i))
        time.sleep(0.01)
        i.ki.dwFlags |= keyeventf_keyup_flag
        ctypes.windll.user32.SendInput(1, ctypes.byref(i), ctypes.sizeof(i))

    def _x11_send_input(self, char):
        """Send key input on X11 (Linux)."""
        if char == "\n":
            keysym = 0xFF0D
        else:
            keysym = self._display.keysym(char)
            if keysym == 0:
                keysym = ord(char)

        window = self._display.get_input_focus()._data["focus"]  # pylint: disable=protected-access
        self._display.sync()

        # pylint: disable=protected-access
        window.send_event(
            self._display._key_press_event(
                detail=self._display.keysym_to_keycode(keysym),
                time=0,
                root=self._display.screen().root,
                window=window,
                same_screen=1,
                child=self._display.create_resource_object("window", 0),
                root_x=0,
                root_y=0,
                event_x=0,
                event_y=0,
                state=0,
            ),
            propagate=True,
        )

        time.sleep(0.01)

        window.send_event(
            self._display._key_release_event(
                detail=self._display.keysym_to_keycode(keysym),
                time=0,
                root=self._display.screen().root,
                window=window,
                same_screen=1,
                child=self._display.create_resource_object("window", 0),
                root_x=0,
                root_y=0,
                event_x=0,
                event_y=0,
                state=0,
            ),
            propagate=True,
        )

        self._display.sync()

    def _simulate_typo(self, text, i):
        """Simulate a typo and correction."""
        typo_length = random.randint(1, min(3, len(text) - i))
        typo_chars = []
        for j in range(typo_length):
            if i + j < len(text) and text[i + j].isalpha():
                typo_char = chr(
                    ord(text[i + j]) + random.choice([-2, -1, 1, 2])
                )
                typo_chars.append(typo_char)
            else:
                typo_chars.append(text[i + j])

        for typo_char in typo_chars:
            self._send_input(typo_char)
            time.sleep(random.uniform(*self._typing_delay))
        time.sleep(random.uniform(0.1, 0.3))

        for _ in typo_chars:
            self._send_input("\x08")
            time.sleep(random.uniform(0.05, 0.15))

        for j in range(typo_length):
            if i + j < len(text):
                self._send_input(text[i + j])
                time.sleep(random.uniform(*self._typing_delay))

        return typo_length

    def _simulate_typing(self, text):
        """Simulate typing text with delays and optional typos."""
        last_char = None
        i = 0
        while i < len(text):
            char = text[i]
            if self._stop_event.is_set():
                return

            if random.random() < self._error_rate and char.isalpha():
                i += self._simulate_typo(text, i)
                continue

            self._send_input(char)

            if self._mode == TypingMode.INSTANT:
                pass
            if self._mode == TypingMode.HUMAN_LIKE:
                delay = random.uniform(*self._typing_delay)
                if char in ",;:":
                    delay *= 1.5
                elif char in ".!?":
                    delay *= 2.0
                if char == last_char:
                    delay *= 0.8
                time.sleep(delay)
            if self._mode == TypingMode.MACHINE_GUN:
                time.sleep(self._typing_delay[0])

            last_char = char
            i += 1

    def type_text(self, text):
        """Start typing text asynchronously."""
        if self._typing_thread and self._typing_thread.is_alive():
            self._typing_thread.join()

        self._stop_event.clear()
        self._typing_thread = threading.Thread(
            target=self._simulate_typing, args=(text,), daemon=True
        )
        self._typing_thread.start()

    def stop_typing(self):
        """Stop typing immediately."""
        self._stop_event.set()
        if self._typing_thread:
            self._typing_thread.join()

    def set_typing_speed(self, min_delay=0.05, max_delay=0.2):
        """Set typing speed range (min/max delay)."""
        self._typing_delay = (min_delay, max_delay)

    def set_error_rate(self, error_rate):
        """Set typo probability (0–1)."""
        self._error_rate = max(0, min(1, error_rate))

    def set_typing_mode(self, mode):
        """Set typing mode (INSTANT/HUMAN_LIKE/MACHINE_GUN)."""
        self._mode = mode

    def wait_until_done(self):
        """Block until typing is finished."""
        if self._typing_thread:
            self._typing_thread.join()

    def press_enter(self):
        """Send Enter/Return key."""
        self._send_input("\n")
