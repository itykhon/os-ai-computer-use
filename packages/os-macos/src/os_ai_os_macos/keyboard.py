# macOS virtual key codes
_VK_RETURN = 36            # Main Return key
_VK_KEYPAD_ENTER = 76      # Keypad Enter


def _press_keycode_safe(keycode: int) -> None:
    try:
        # Lazy import to make unit tests patchable by monkeypatching sys.modules["Quartz"]
        from Quartz import CGEventCreateKeyboardEvent, CGEventPost, kCGHIDEventTap
        down = CGEventCreateKeyboardEvent(None, keycode, True)
        up = CGEventCreateKeyboardEvent(None, keycode, False)
        CGEventPost(kCGHIDEventTap, down)
        CGEventPost(kCGHIDEventTap, up)
    except Exception:
        # Fallback is silent; caller may try alternative
        pass


def press_enter_mac() -> None:
    """Reliably press the Return/Enter on macOS using Quartz events.

    Tries the main Return key first, then the Keypad Enter as a fallback.
    """
    _press_keycode_safe(_VK_RETURN)
    _press_keycode_safe(_VK_KEYPAD_ENTER)


