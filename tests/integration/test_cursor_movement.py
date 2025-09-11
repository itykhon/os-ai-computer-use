import os
import time
import math
import platform
from pathlib import Path
import sys
import importlib.util

import pytest
import pyautogui


def _dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


@pytest.mark.skipif(platform.system() != "Darwin", reason="Mac-only GUI test")
@pytest.mark.skipif(os.environ.get("RUN_CURSOR_TESTS") != "1", reason="Set RUN_CURSOR_TESTS=1 to enable GUI cursor tests")
def test_mouse_move_hits_target_within_tolerance():
    # Load project main.py explicitly to avoid site-packages name collision
    proj_root = Path(__file__).resolve().parents[2]
    main_path = proj_root / "main.py"
    if str(proj_root) not in sys.path:
        sys.path.insert(0, str(proj_root))
    spec = importlib.util.spec_from_file_location("agent_core_main", str(main_path))
    assert spec and spec.loader, "Failed to create spec for main.py"
    main = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(main)  # type: ignore

    screen_w, screen_h = pyautogui.size()
    center = (screen_w // 2, screen_h // 2)
    safe = lambda x, y: (max(20, min(screen_w - 20, x)), max(20, min(screen_h - 20, y)))

    targets = [
        center,
        safe(center[0] + 120, center[1]),
        safe(center[0], center[1] + 140),
        safe(50, 50),
    ]

    original_pos = pyautogui.position()
    try:
        for (tx, ty) in targets:
            main.handle_computer_action(
                "mouse_move",
                {"coordinate": [tx, ty], "coordinate_space": "screen", "duration": 0.45, "tween": "linear"},
            )
            time.sleep(0.08)  # give post-correction a moment
            pos = pyautogui.position()
            tol = max(3, int(getattr(main, "POST_MOVE_TOLERANCE_PX", 2)) + 1)
            assert _dist((pos.x, pos.y), (tx, ty)) <= tol, f"Cursor at {(pos.x, pos.y)} != {(tx, ty)} within tol {tol}"
    finally:
        try:
            pyautogui.moveTo(original_pos.x, original_pos.y, duration=0.30)
        except Exception:
            pass


@pytest.mark.skipif(platform.system() != "Darwin", reason="Mac-only GUI test")
@pytest.mark.skipif(os.environ.get("RUN_CURSOR_TESTS") != "1", reason="Set RUN_CURSOR_TESTS=1 to enable GUI cursor tests")
def test_mouse_move_respects_calibration_offsets():
    proj_root = Path(__file__).resolve().parents[2]
    main_path = proj_root / "main.py"
    if str(proj_root) not in sys.path:
        sys.path.insert(0, str(proj_root))
    spec = importlib.util.spec_from_file_location("agent_core_main", str(main_path))
    assert spec and spec.loader, "Failed to create spec for main.py"
    main = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(main)  # type: ignore

    screen_w, screen_h = pyautogui.size()
    center = (screen_w // 2, screen_h // 2)

    # Keep within screen after applying offsets
    def clamp(x, y):
        return (max(0, min(screen_w - 1, x)), max(0, min(screen_h - 1, y)))

    orig_x_off = getattr(main, "COORD_X_OFFSET", 0)
    orig_y_off = getattr(main, "COORD_Y_OFFSET", 0)
    orig_x_scale = getattr(main, "COORD_X_SCALE", 1.0)
    orig_y_scale = getattr(main, "COORD_Y_SCALE", 1.0)

    # Small, visible offsets that won't push us out of bounds
    try:
        main.COORD_X_OFFSET = 7
        main.COORD_Y_OFFSET = -5
        main.COORD_X_SCALE = 1.0
        main.COORD_Y_SCALE = 1.0

        base_x, base_y = center
        expected_x = int(round(base_x * main.COORD_X_SCALE + main.COORD_X_OFFSET))
        expected_y = int(round(base_y * main.COORD_Y_SCALE + main.COORD_Y_OFFSET))
        expected_x, expected_y = clamp(expected_x, expected_y)

        original_pos = pyautogui.position()
        try:
            main.handle_computer_action(
                "mouse_move",
                {"coordinate": [base_x, base_y], "coordinate_space": "screen", "duration": 0.45, "tween": "linear"},
            )
            time.sleep(0.08)
            pos = pyautogui.position()
            tol = max(3, int(getattr(main, "POST_MOVE_TOLERANCE_PX", 2)) + 1)
            assert _dist((pos.x, pos.y), (expected_x, expected_y)) <= tol, (
                f"Calibrated move mismatch: got {(pos.x, pos.y)}, expected {(expected_x, expected_y)} within tol {tol}"
            )
        finally:
            try:
                pyautogui.moveTo(original_pos.x, original_pos.y, duration=0.30)
            except Exception:
                pass
    finally:
        # restore original calibration
        main.COORD_X_OFFSET = orig_x_off
        main.COORD_Y_OFFSET = orig_y_off
        main.COORD_X_SCALE = orig_x_scale
        main.COORD_Y_SCALE = orig_y_scale


