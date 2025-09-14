import importlib
import importlib.util
import sys
import types


def _install_quartz_mock(monkeypatch):
    calls = {"events": []}
    module = types.ModuleType("Quartz")

    def CGEventCreateKeyboardEvent(src, keycode, keyDown):
        calls["events"].append(("create", keycode, bool(keyDown)))
        return object()

    def CGEventPost(tap, event):
        calls["events"].append(("post", tap, event))

    module.CGEventCreateKeyboardEvent = CGEventCreateKeyboardEvent
    module.CGEventPost = CGEventPost
    module.kCGHIDEventTap = 0
    monkeypatch.setitem(sys.modules, "Quartz", module)
    return calls


def test_press_enter_mac_success(monkeypatch):
    calls = _install_quartz_mock(monkeypatch)
    # re-import keyboard with mocked Quartz
    keyboard = importlib.import_module("os_ai_os_macos.keyboard")

    keyboard.press_enter_mac()

    # Expect: create keyDown, post, then keyUp, post
    assert ("create", 36, True) in calls["events"] or ("create", 36, 1) in calls["events"]
    assert any(e[0] == "post" for e in calls["events"])  # at least one post


def test_press_keycode_safe_on_exception(monkeypatch):
    # Quartz поднимет исключение — функция не должна падать
    def raise_exc(*args, **kwargs):
        raise RuntimeError("boom")

    module = types.ModuleType("Quartz")
    module.CGEventCreateKeyboardEvent = raise_exc
    module.CGEventPost = raise_exc
    module.kCGHIDEventTap = 0
    monkeypatch.setitem(sys.modules, "Quartz", module)

    keyboard = importlib.import_module("os_ai_os_macos.keyboard")

    # Не должно бросить исключение
    keyboard._press_keycode_safe(36)


