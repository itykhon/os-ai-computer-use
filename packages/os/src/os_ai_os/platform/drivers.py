from __future__ import annotations

from dataclasses import dataclass
from ..ports.mouse import Mouse
from ..ports.keyboard import Keyboard
from ..ports.screen import Screen
from ..ports.overlay import Overlay
from ..ports.sound import Sound
from ..ports.permissions import Permissions
from ..ports.types import Capabilities


@dataclass
class PlatformDrivers:
    mouse: Mouse
    keyboard: Keyboard
    screen: Screen
    overlay: Overlay
    permissions: Permissions
    sound: Sound
    capabilities: Capabilities


