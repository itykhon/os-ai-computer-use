import importlib.util
import sys
from pathlib import Path

import pytest


def _load_main():
    proj_root = Path(__file__).resolve().parents[1]
    main_path = proj_root / "main.py"
    if str(proj_root) not in sys.path:
        sys.path.insert(0, str(proj_root))
    spec = importlib.util.spec_from_file_location("agent_core_main", str(main_path))
    assert spec and spec.loader, "Failed to load main.py"
    main = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(main)  # type: ignore
    return main


def test_scroll_directions(monkeypatch):
    main = _load_main()

    calls = {
        "moveTo": [],
        "scroll": [],
        "hscroll": [],
    }

    monkeypatch.setattr(main.pyautogui, "moveTo", lambda x, y, **k: calls["moveTo"].append((x, y, k)))
    monkeypatch.setattr(main.pyautogui, "scroll", lambda clicks: calls["scroll"].append(clicks))
    monkeypatch.setattr(main.pyautogui, "hscroll", lambda clicks: calls["hscroll"].append(clicks))

    # down (negative)
    main.handle_computer_action("scroll", {"coordinate": [100, 200], "scroll_direction": "down", "scroll_amount": 3})
    # up (positive)
    main.handle_computer_action("scroll", {"scroll_direction": "up", "scroll_amount": 4})
    # left (negative, hscroll)
    main.handle_computer_action("scroll", {"scroll_direction": "left", "scroll_amount": 5})
    # right (positive, hscroll)
    main.handle_computer_action("scroll", {"scroll_direction": "right", "scroll_amount": 6})

    # Validate
    assert calls["scroll"][0] == -3
    assert calls["scroll"][1] == 4
    assert calls["hscroll"][0] == -5
    assert calls["hscroll"][1] == 6
    assert calls["moveTo"], "Expected moveTo before first scroll when coordinate provided"


@pytest.mark.parametrize(
    "action,button,clicks",
    [
        ("left_click", "left", 1),
        ("double_click", "left", 2),
        ("triple_click", "left", 3),
        ("right_click", "right", 1),
        ("middle_click", "middle", 1),
    ],
)
def test_click_variants(monkeypatch, action, button, clicks):
    main = _load_main()

    calls = {
        "moveTo": [],
        "click": [],
    }

    def moveTo(x, y, **k):
        calls["moveTo"].append((x, y, k))

    def click(**kw):
        calls["click"].append(kw)

    monkeypatch.setattr(main.pyautogui, "moveTo", moveTo)
    monkeypatch.setattr(main.pyautogui, "click", click)

    res = main.handle_computer_action(action, {"coordinate": [321, 654]})

    assert calls["moveTo"], "click with coordinate should move first"
    assert calls["click"], "pyautogui.click should be called"
    kw = calls["click"][0]
    assert kw.get("button") == button
    assert kw.get("clicks") == clicks
    assert any("done" in c.get("text", "") for c in res)


def test_left_mouse_down_up(monkeypatch):
    main = _load_main()

    order = []

    monkeypatch.setattr(main.pyautogui, "moveTo", lambda x, y, **k: order.append(("move", x, y)))
    monkeypatch.setattr(main.pyautogui, "mouseDown", lambda **kw: order.append(("down", kw.get("button"))))
    monkeypatch.setattr(main.pyautogui, "mouseUp", lambda **kw: order.append(("up", kw.get("button"))))

    main.handle_computer_action("left_mouse_down", {"coordinate": [10, 20]})
    main.handle_computer_action("left_mouse_up", {"coordinate": [30, 40]})

    # Expect: move -> down(left) then move -> up(left)
    assert order[0][0] == "move" and order[1] == ("down", "left")
    assert order[2][0] == "move" and order[3] == ("up", "left")


def test_left_click_drag(monkeypatch):
    main = _load_main()

    order = []

    def moveTo(x, y, **k):
        order.append(("move", x, y))

    def mouseDown(**kw):
        order.append(("down", kw.get("button")))

    def mouseUp(**kw):
        order.append(("up", kw.get("button")))

    monkeypatch.setattr(main.pyautogui, "moveTo", moveTo)
    monkeypatch.setattr(main.pyautogui, "mouseDown", mouseDown)
    monkeypatch.setattr(main.pyautogui, "mouseUp", mouseUp)

    res = main.handle_computer_action(
        "left_click_drag",
        {"start": [11, 22], "end": [111, 222]},
    )

    # Expect: move(start) -> down(left) -> move(end) -> up(left)
    assert order == [
        ("move", 11, 22),
        ("down", "left"),
        ("move", 111, 222),
        ("up", "left"),
    ]
    assert any("drag" in c.get("text", "") for c in res)


