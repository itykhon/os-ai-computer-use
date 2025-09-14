## OS Ports & Drivers

This repo uses a Ports & Adapters architecture for OS interactions:

- `packages/os` (`os_ai_os`) defines OS-agnostic ports: Mouse, Keyboard, Screen, Overlay, Sound, Permissions and value objects (Point, Size, Capabilities). It also provides `PlatformDrivers` and a `build_platform()` factory loaded via entry points, exposed as `os_ai_os.api.get_drivers()`.
- Platform-specific implementations live in dedicated packages (e.g. `packages/os-macos`), exporting `make_drivers()` via entry point `os_ai_os.drivers:darwin`.
- Core (`packages/core`) depends only on `os_ai_os` and calls `get_drivers()` to access the current platform at runtime.

Key benefits:
- No platform imports in core; Quartz/AppKit/Win32 are isolated in drivers.
- Unified capabilities flags enable graceful degradation across platforms.
- Easy to add new platforms by providing a drivers package and entry point.


