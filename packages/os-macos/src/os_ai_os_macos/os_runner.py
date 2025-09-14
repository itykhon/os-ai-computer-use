from __future__ import annotations

import sys
import time
import pyautogui

from os_ai_os_macos.os_harness import TestWindow, pump_runloop
from os_ai_os_macos.keyboard import press_enter_mac


def run_keyboard() -> int:
    win = TestWindow()
    tx, ty = win.focus_text()
    pyautogui.moveTo(tx, ty, duration=0.2)
    pyautogui.click()
    pump_runloop(0.2)
    txt = "hello"
    pyautogui.write(txt, interval=0.02)
    pump_runloop(0.1)
    press_enter_mac()
    pump_runloop(0.2)
    content = win.get_text()
    print(content)  # debug output
    return 0 if txt in content else 2


def run_click() -> int:
    win = TestWindow()
    x, y = win.click_target_point()
    pyautogui.moveTo(x, y, duration=0.2)
    pyautogui.click()
    pump_runloop(0.2)
    return 0 if getattr(win.click_view, "clicked", False) else 3


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: python -m utils.os_runner [keyboard|click]")
        return 1
    cmd = argv[1]
    if cmd == "keyboard":
        return run_keyboard()
    if cmd == "click":
        return run_click()
    print("unknown cmd")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))


