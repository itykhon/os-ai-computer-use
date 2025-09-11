import builtins
import types

import importlib
import sys


def _install_quartz_mock(monkeypatch):
    quartz = types.SimpleNamespace()

    calls = {
        "create": [],
        "post": [],
    }

    def CGEventCreateKeyboardEvent(_a, keycode, is_down):
        calls["create"].append((int(keycode), bool(is_down)))
        return object()

    def CGEventPost(_tap, event):
        calls["post"].append(event)

    quartz.CGEventCreateKeyboardEvent = CGEventCreateKeyboardEvent
    quartz.CGEventPost = CGEventPost
    quartz.kCGHIDEventTap = 0

    module = types.ModuleType("Quartz")
    module.CGEventCreateKeyboardEvent = CGEventCreateKeyboardEvent
    module.CGEventPost = CGEventPost
    module.kCGHIDEventTap = 0

    monkeypatch.setitem(sys.modules, "Quartz", module)
    return calls


def test_press_enter_mac_success(monkeypatch):
    calls = _install_quartz_mock(monkeypatch)
    # re-import keyboard with mocked Quartz
    keyboard = importlib.import_module("utils.keyboard")

    keyboard.press_enter_mac()

    # Должно быть 2 нажатия: Return и Keypad Enter (down+up для каждого => 4 create, 4 post)
    assert len(calls["create"]) == 4
    assert len(calls["post"]) == 4

    # Проверяем порядок: down, up для каждого (keycodes 36 и 76)
    keycodes = [kc for kc, _ in calls["create"]]
    assert 36 in keycodes and 76 in keycodes


def test_press_keycode_safe_on_exception(monkeypatch):
    # Quartz поднимет исключение — функция не должна падать
    def raise_exc(*args, **kwargs):
        raise RuntimeError("boom")

    module = types.ModuleType("Quartz")
    module.CGEventCreateKeyboardEvent = raise_exc
    module.CGEventPost = raise_exc
    module.kCGHIDEventTap = 0
    monkeypatch.setitem(sys.modules, "Quartz", module)

    keyboard = importlib.import_module("utils.keyboard")
    # не должно бросить
    keyboard.press_enter_mac()


