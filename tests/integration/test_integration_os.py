import os
import sys
import subprocess
import platform

import pytest


RUN_OS = os.environ.get("RUN_CURSOR_TESTS") == "1"
IS_DARWIN = sys.platform == "darwin" and platform.system().lower() == "darwin"

pytestmark = pytest.mark.skipif(not (RUN_OS and IS_DARWIN), reason="Set RUN_CURSOR_TESTS=1 and run on macOS to execute OS tests")


def _run_os(cmd: list[str]) -> subprocess.CompletedProcess:
    python = sys.executable
    return subprocess.run([python, "-m", "utils.os_runner", *cmd], cwd=os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")), capture_output=True, text=True)


def test_keyboard_enter_and_typing():
    proc = _run_os(["keyboard"])
    if proc.returncode < 0:
        pytest.skip(f"OS blocked GUI automation (rc={proc.returncode}). Enable Accessibility for Python and retry.\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}")
    assert proc.returncode == 0, f"keyboard run failed rc={proc.returncode}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"


def test_mouse_click_area():
    proc = _run_os(["click"])
    if proc.returncode < 0:
        pytest.skip(f"OS blocked GUI automation (rc={proc.returncode}). Enable Accessibility for Python and retry.\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}")
    assert proc.returncode == 0, f"click run failed rc={proc.returncode}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"


