from typing import Optional

import threading
import random
import time
import ctypes

import win32gui
import win32con
import keyboard

from helper.typing import CharacterTyper, TypingMode


class AutoTyper:
    """
    Auto typing utility with multiple modes, speeds and styles.
    """
    def __init__(
        self,
        wordlist: str = "assets/gid.txt",
        filler: str = "assets/filler.txt",
        short: str = "assets/shortwords.txt",
    ) -> None:
        self._wordlist_path = wordlist
        self._filler_path = filler
        self._short_path = short
        self._symbols = ["- ", "# "]
        self._used_lines = set()
        self._modes = ["normal", "ladder", "paragraph", "beef", "demon"]
        self._mode_index = 0
        self._mode = self._modes[self._mode_index]
        self._case_mode = "lower"
        self._is_typing = False
        self._speed_presets = [
            (0.03, 0.10),
            (0.07, 0.2),
            (0.15, 0.25),
            (0.2, 0.5),
        ]
        self._speed_index = 0
        self._typing_modes = list(TypingMode)
        self._typing_mode_index = 1
        self._terminal_visible = True
        self._typer = self._initialize_typer()

    def _initialize_typer(self) -> CharacterTyper:
        """Init CharacterTyper with default speed and mode."""
        typer = CharacterTyper()
        typer.set_typing_speed(*self._speed_presets[self._speed_index])
        typer.set_typing_mode(self._typing_modes[self._typing_mode_index])
        ctypes.windll.kernel32.SetConsoleTitleW("kamo x vatos")
        return typer

    def _get_random_line(self, path: str) -> Optional[str]:
        """Return random line from file or None if missing/empty."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]
            return random.choice(lines) if lines else None
        except FileNotFoundError:
            print(f"File not found: '{path}'")
            return None

    def _handle_typing(
        self,
        text: str,
        transform: Optional[callable] = None,
        hold_shift: bool = False,
    ) -> None:
        """Type given text with case/transform options."""
        time.sleep(0.05)
        if transform:
            text = transform(text)

        if self._case_mode == "upper":
            text = text.upper()
        elif self._case_mode == "lower":
            text = text.lower()

        if hold_shift:
            keyboard.press("shift")

        self._typer.type_text(text)
        self._typer.wait_until_done()

        self._typer.press_enter()

        if hold_shift:
            keyboard.release("shift")

    def _get_allowed_demon_types(self) -> list[str]:
        """Return demon types not yet used (short/middle/long)."""
        all_types = {"short", "middle", "long"}
        used_types = {
            t for t in all_types if f"__demon_{t}__" in self._used_lines
        }
        remaining = list(all_types - used_types)

        if not remaining:
            for t in all_types:
                self._used_lines.discard(f"__demon_{t}__")
            return list(all_types)

        return remaining

    def toggle_terminal_visibility(self) -> None:
        """Toggle terminal window visibility"""
        console_window = win32gui.FindWindow(None, "kamo x vatos")

        if not console_window:
            print("Console window not found! Trying default console...")
            console_window = win32gui.FindWindow("ConsoleWindowClass", None)
            if not console_window:
                print("Could not find any console window!")
                return

        if self._terminal_visible:
            win32gui.ShowWindow(console_window, win32con.SW_HIDE)
            self._terminal_visible = False
        else:
            win32gui.ShowWindow(console_window, win32con.SW_SHOW)
            win32gui.SetForegroundWindow(console_window)
            self._terminal_visible = True

    def toggle_case_mode(self) -> None:
        """Cycle through case modes: upper -> lower"""
        case_modes = ["upper", "lower"]
        current_index = (
            case_modes.index(self._case_mode)
            if self._case_mode in case_modes
            else 0
        )
        self._case_mode = case_modes[(current_index + 1) % len(case_modes)]
        print(f"Case mode set to: {self._case_mode}")

    def cycle_mode(self) -> None:
        """Cycle through content modes (normal/ladder/paragraph/beef)"""
        self._mode_index = (self._mode_index + 1) % len(self._modes)
        self._mode = self._modes[self._mode_index]
        print(f"Content mode set to: {self._mode}")

    def cycle_typing_mode(self) -> None:
        """Cycle through typing styles (INSTANT/HUMAN_LIKE/MACHINE_GUN)"""
        self._typing_mode_index = (self._typing_mode_index + 1) % len(
            self._typing_modes
        )
        self._typer.set_typing_mode(
            self._typing_modes[self._typing_mode_index]
        )
        print(
            f"Typing style set to: {self._typing_modes[self._typing_mode_index].name}"
        )

    def cycle_typing_speed(self) -> None:
        """Cycle through typing speed presets"""
        self._speed_index = (self._speed_index + 1) % len(self._speed_presets)
        min_delay, max_delay = self._speed_presets[self._speed_index]
        self._typer.set_typing_speed(min_delay, max_delay)
        speed_names = ["Fast", "Medium", "Slow", "Very slow"]
        print(f"Typing speed set to: {speed_names[self._speed_index]}")

    def write_pack(self, _: Optional[keyboard.KeyboardEvent] = None) -> None:
        """Trigger typing based on active mode."""
        if self._is_typing:
            return

        self._is_typing = True
        try:
            keyboard.release("tab")
            time.sleep(0.05)

            if self._mode == "normal":
                self._handle_normal_mode()
            elif self._mode == "ladder":
                self._handle_ladder_mode()
            elif self._mode == "paragraph":
                self._handle_paragraph_mode()
            elif self._mode == "beef":
                self._handle_beef_mode()
            elif self._mode == "demon":
                self._handle_demon_mode()
        finally:
            self._is_typing = False

    def _handle_normal_mode(self) -> None:
        """Handle typing in normal mode."""
        source = self._wordlist_path
        choice = random.randint(1, 13)
        if choice == 1:
            source = self._filler_path

        line = self._get_random_line(source)
        if not line or line in self._used_lines:
            return self.write_pack()

        if choice == 2:
            line = random.choice(self._symbols) + line

        self._used_lines.add(line)
        self._handle_typing(line)

    def _handle_ladder_mode(self) -> None:
        """Handle typing in ladder mode (word -> vertical)."""
        line = self._get_random_line(self._wordlist_path)
        if not line or line in self._used_lines:
            return self.write_pack()

        self._used_lines.add(line)
        self._handle_typing(line.replace(" ", "\n"), hold_shift=True)

    def _handle_paragraph_mode(self) -> None:
        """Handle typing in paragraph mode."""
        lines = []
        for _ in range(30):
            line = self._get_random_line(self._wordlist_path)
            if line:
                lines.append(line)

        paragraph = " ".join(lines)
        if lines:
            self._used_lines.add(lines[-1])
        self._handle_typing(paragraph)

    def _handle_beef_mode(self) -> None:
        """Handle typing in beef mode (combine two)."""
        line1 = self._get_random_line(self._wordlist_path)
        line2 = self._get_random_line(self._wordlist_path)

        while not line1 or not line2 or line1 == line2:
            line1 = self._get_random_line(self._wordlist_path)
            line2 = self._get_random_line(self._wordlist_path)

        combined = f"{line1} and {line2}"

        self._used_lines.add(line1)
        self._used_lines.add(line2)

        self._handle_typing(combined)

    def _handle_demon_mode(self) -> None:
        """Handle typing in demon mode."""
        allowed = self._get_allowed_demon_types()
        selected = random.choice(allowed)
        self._used_lines.add(f"__demon_{selected}__")

        short = middle = long = None

        if selected == "short":
            for _ in range(30):
                line = self._get_random_line(self._short_path)
                if line and line not in self._used_lines:
                    short = line
                    self._used_lines.add(line)
                    break

        elif selected == "middle":
            for _ in range(30):
                line = self._get_random_line(self._wordlist_path)
                if line and line not in self._used_lines:
                    middle = line
                    self._used_lines.add(line)
                    break

        elif selected == "long":
            lines = set()
            attempts = 0
            while len(lines) < 4 and attempts < 100:
                line = self._get_random_line(self._wordlist_path)
                if line and line not in self._used_lines:
                    lines.add(line)
                attempts += 1

            if len(lines) == 4:
                long = " and ".join(lines)
                self._used_lines.update(lines)

        parts = [p for p in [short, middle, long] if p]
        if parts:
            combined = " ".join(parts)
            self._handle_typing(combined)


def main() -> None:
    """Main entry: setup hotkeys and run event loop."""
    typer = AutoTyper()
    keyboard.on_press_key("tab", lambda _: typer.write_pack())
    keyboard.on_press_key("caps lock", lambda _: typer.toggle_case_mode())
    keyboard.on_press_key("shift", lambda _: typer.cycle_mode())
    keyboard.on_press_key("ctrl", lambda _: typer.cycle_typing_speed())
    keyboard.on_press_key("alt", lambda _: typer.cycle_typing_mode())
    keyboard.on_press_key("f10", lambda _: typer.toggle_terminal_visibility())

    print("Press Tab to type random lines.")
    print("Press Caps Lock to toggle case mode (upper/lower).")
    print("Press Shift to cycle through content modes.")
    print("Press ctrl to cycle through typing speeds.")
    print(
        "Press alt to cycle through typing styles (INSTANT/HUMAN_LIKE/MACHINE_GUN)."
    )
    print("Press f10 to hide the window.")
    print("Press Esc to exit.")

    exit_event = threading.Event()

    def esc_listener():
        keyboard.on_press_key("esc", lambda _: exit_event.set())

    esc_thread = threading.Thread(target=esc_listener, daemon=True)
    esc_thread.start()

    try:
        while not exit_event.is_set():
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n[INFO] Program terminated by user.")
    finally:
        keyboard.unhook_all()
        print("[INFO] Cleanup complete. Goodbye!")


if __name__ == "__main__":
    main()
