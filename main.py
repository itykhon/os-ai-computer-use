# Compatibility shim for legacy tests expecting functions in main.
# New architecture implements logic in os_ai_core.tools.computer.

import os
import sys
import glob

# Ensure all workspace package sources are importable when running directly
_ROOT = os.path.dirname(os.path.abspath(__file__))
for _src_dir in glob.glob(os.path.join(_ROOT, "packages", "*", "src")):
    if _src_dir not in sys.path:
        sys.path.insert(0, _src_dir)

from os_ai_core.tools import computer as _computer  # real implementation
from os_ai_os_macos.keyboard import press_enter_mac as _press_enter_mac

# Expose pyautogui used by the computer tool so test monkeypatching affects real calls
pyautogui = _computer.pyautogui  # type: ignore


def press_enter_mac():
    return _press_enter_mac()


def handle_computer_action(action, params):  # type: ignore
    # Ensure computer module uses (possibly monkeypatched) press_enter_mac from this module
    _computer.press_enter_mac = press_enter_mac  # type: ignore
    return _computer.handle_computer_action(action, params)


if __name__ == "__main__":
    from os_ai_cli.main import main as cli_main
    raise SystemExit(cli_main())



