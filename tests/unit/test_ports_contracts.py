import platform

import pytest


@pytest.mark.skipif(platform.system().lower() != "darwin", reason="contracts bound to darwin driver in this repo")
def test_ports_basic_contracts():
    from os_ai_os.api import get_drivers

    drivers = get_drivers()
    # Keyboard
    assert hasattr(drivers.keyboard, "press_enter")
    drivers.keyboard.type_text("abc")
    # Mouse
    assert hasattr(drivers.mouse, "move_to")
    # Overlay
    assert hasattr(drivers.overlay, "highlight")
    # Screen & Size
    size = drivers.screen.size()
    assert isinstance(size.width, int) and size.width > 0
    assert isinstance(size.height, int) and size.height > 0
    # Capabilities present
    assert drivers.capabilities.dpi_scale >= 1.0


