import os
import time
import threading
import math
import platform

import pytest
import pyautogui
from PIL import Image
import subprocess
import tempfile


def _dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _count_red_pixels(img, cx, cy, radius, r_min=120, dominance=1.6):
    px = img.load()
    w, h = img.size
    count = 0
    x0 = max(0, cx - radius)
    y0 = max(0, cy - radius)
    x1 = min(w - 1, cx + radius)
    y1 = min(h - 1, cy + radius)
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            try:
                r, g, b = px[x, y][:3]
            except Exception:
                r, g, b = px[x, y]
            if r >= r_min and r >= g * dominance and r >= b * dominance:
                count += 1
    return count


def _screencap_region(x0, y0, x1, y1):
    try:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=True) as tmp:
            path = tmp.name
            w = max(1, x1 - x0)
            h = max(1, y1 - y0)
            subprocess.run(["screencapture", "-x", "-t", "png", "-R", f"{x0},{y0},{w},{h}", path], check=True)
            img = Image.open(path).convert("RGB")
            return img
    except Exception:
        pass
    region = (x0, y0, max(1, x1 - x0), max(1, y1 - y0))
    return pyautogui.screenshot(region=region).convert("RGB")


@pytest.mark.skipif(platform.system() != "Darwin", reason="Mac-only GUI test")
def test_overlay_highlight_visible_near_target_or_mirrored():
    from config.settings import PREMOVE_HIGHLIGHT_RADIUS
    from utils.overlay import highlight_position, get_highlight_state

    screen_w, screen_h = pyautogui.size()
    target = (screen_w // 2, screen_h // 2)

    t = threading.Thread(target=lambda: highlight_position(target[0], target[1], radius=PREMOVE_HIGHLIGHT_RADIUS, duration=0.8))
    t.daemon = True
    t.start()

    deadline = time.time() + 0.8
    while time.time() < deadline:
        active, center = get_highlight_state()
        if active:
            break
        time.sleep(0.02)

    radius = PREMOVE_HIGHLIGHT_RADIUS + 24
    x0 = max(0, target[0] - radius)
    y0 = max(0, target[1] - radius)
    x1 = min(screen_w, target[0] + radius)
    y1 = min(screen_h, target[1] + radius)
    # Try capturing overlay window directly; fallback to full screenshot region
    try:
        from utils.overlay import capture_overlay_region
        img = capture_overlay_region(x0, y0, x1, y1)
    except Exception:
        img = None
    if img is None:
        img = _screencap_region(x0, y0, x1, y1)
    red_count_target = _count_red_pixels(img, radius, radius, PREMOVE_HIGHLIGHT_RADIUS + 6)

    mirrored = (target[0], screen_h - target[1])
    my0 = max(0, mirrored[1] - radius)
    my1 = min(screen_h, mirrored[1] + radius)
    try:
        mimg = capture_overlay_region(x0, my0, x1, my1)
    except Exception:
        mimg = None
    if mimg is None:
        mimg = _screencap_region(x0, my0, x1, my1)
    red_count_target = max(
        red_count_target,
        _count_red_pixels(img, radius, radius, PREMOVE_HIGHLIGHT_RADIUS + 12),
    )
    red_count_mirrored = _count_red_pixels(mimg, radius, radius, PREMOVE_HIGHLIGHT_RADIUS + 6)
    red_count_mirrored = max(
        red_count_mirrored,
        _count_red_pixels(mimg, radius, radius, PREMOVE_HIGHLIGHT_RADIUS + 12),
    )

    t.join(timeout=1.0)

    # Diagnostic print to help understand failures
    try:
        from utils.overlay import _overlay
        dbg = getattr(_overlay, "_last_debug", None)
        print(f"[overlay debug] {dbg}")
    except Exception:
        pass

    assert max(red_count_target, red_count_mirrored) >= 5, (
        f"Overlay not visible near target={target} (count={red_count_target}) "
        f"nor mirrored={mirrored} (count={red_count_mirrored})"
    )


@pytest.mark.skipif(platform.system() != "Darwin", reason="Mac-only GUI test")
def test_overlay_highlight_alignment_exact():
    from config.settings import PREMOVE_HIGHLIGHT_RADIUS
    from utils.overlay import highlight_position

    screen_w, screen_h = pyautogui.size()
    target = (min(screen_w - 40, max(40, screen_w // 3)), min(screen_h - 40, max(40, screen_h // 3)))

    t = threading.Thread(target=lambda: highlight_position(target[0], target[1], radius=PREMOVE_HIGHLIGHT_RADIUS, duration=0.8))
    t.daemon = True
    t.start()
    time.sleep(0.15)

    # Prefer overlay-only capture to avoid background noise
    try:
        from utils.overlay import capture_overlay_region
        radius = PREMOVE_HIGHLIGHT_RADIUS + 24
        x0 = max(0, target[0] - radius)
        y0 = max(0, target[1] - radius)
        x1 = min(screen_w, target[0] + radius)
        y1 = min(screen_h, target[1] + radius)
        img = capture_overlay_region(x0, y0, x1, y1)
    except Exception:
        img = None
    if img is None:
        img = pyautogui.screenshot()
    red_count = _count_red_pixels(img, target[0], target[1], PREMOVE_HIGHLIGHT_RADIUS + 6)
    t.join(timeout=1.0)
    try:
        from utils.overlay import _overlay
        dbg = getattr(_overlay, "_last_debug", None)
        print(f"[overlay debug] {dbg}")
    except Exception:
        pass

    assert red_count >= 50, f"Overlay not aligned at target={target}; red_count={red_count}"


