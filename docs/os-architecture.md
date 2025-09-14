## OS Ports & Drivers

This repo uses a Ports & Adapters architecture for OS interactions:

- `packages/os` (`os_ai_os`) defines OS-agnostic ports: Mouse, Keyboard, Screen, Overlay, Sound, Permissions and value objects (Point, Size, Capabilities). It also provides `PlatformDrivers` and a `build_platform()` factory loaded via entry points, exposed as `os_ai_os.api.get_drivers()`.
- Platform-specific implementations live in dedicated packages (e.g. `packages/os-macos`), exporting `make_drivers()` via entry point `os_ai_os.drivers:darwin`.
- Core (`packages/core`) depends only on `os_ai_os` and calls `get_drivers()` to access the current platform at runtime.

Key benefits:
- No platform imports in core; Quartz/AppKit/Win32 are isolated in drivers.
- Unified capabilities flags enable graceful degradation across platforms.
- Easy to add new platforms by providing a drivers package and entry point.

## Repository Layout

- `packages/os` (`os_ai_os`):
  - `ports/`: protocols for `Mouse`, `Keyboard`, `Screen`, `Overlay`, `Sound`, `Permissions`, plus `types.py`.
  - `platform/`: `drivers.py` (container), `factory.py` (driver loader), `__init__.py`.
  - `api.py`: `get_drivers()` singleton accessor.
  - `config.py`: OS‑agnostic defaults (e.g., pre‑move highlight duration).

- `packages/os-macos` (`os_ai_os_macos`):
  - `drivers.py`: `make_drivers()` returning implementations.
  - `overlay.py`, `sound.py`, `keyboard.py`: Quartz/AppKit/NSSound helpers.
  - `os_harness.py`, `os_runner.py`: testing harnesses.
  - Entry point: `[project.entry-points."os_ai_os.drivers"].darwin = os_ai_os_macos.drivers:make_drivers`.

- `packages/os-windows` (`os_ai_os_windows`):
  - `drivers.py`: PyAutoGUI implementations for mouse/keyboard/screen; overlay/sound no‑ops.
  - Entry point: `[project.entry-points."os_ai_os.drivers"].windows = os_ai_os_windows.drivers:make_drivers`.

## Capabilities

Drivers expose a `Capabilities` struct used by core to adjust behavior:
- `supports_synthetic_input`: whether synthetic input is allowed.
- `supports_click_through_overlay`: overlay can ignore mouse events.
- `supports_smooth_move`: whether to use tweened motion.
- `dpi_scale`: used for coordinate normalization/hiDPI.
- `screen_recording_available`: whether native screen capture is expected to work.

## Adding a New Platform Driver

1. Create a new package `packages/os-<platform>` with a module `os_ai_os_<platform>.drivers`.
2. Implement classes for `Mouse`, `Keyboard`, `Screen`, `Overlay`, `Sound`, `Permissions`.
3. Implement `make_drivers()` returning `PlatformDrivers` with proper `Capabilities`.
4. Declare an entry point in `pyproject.toml`:
   ```toml
   [project.entry-points."os_ai_os.drivers"]
   <platform> = "os_ai_os_<platform>.drivers:make_drivers"
   ```
5. (Optional) Add unit contract tests that `get_drivers()` loads your driver on that OS (skip on others).

## Core Usage

Core code should always obtain drivers via:
```python
from os_ai_os.api import get_drivers
drivers = get_drivers()
drivers.mouse.move_to(...)
drivers.keyboard.press_enter()
img = drivers.screen.screenshot()
```

This keeps core independent from platform specifics and allows swapping drivers at runtime by OS.


