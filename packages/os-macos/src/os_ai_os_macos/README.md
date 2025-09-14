macOS drivers package
=====================

This package implements macOS-specific drivers for the OS ports defined in os_ai_os:
- Mouse (PyAutoGUI-based)
- Keyboard (Quartz enter key helper)
- Screen (PyAutoGUI screenshot, can be extended to Quartz)
- Overlay (AppKit overlay renderer)
- Sound (NSSound playback)
- Permissions (stubs, can be extended to TCC checks)

Entry point is declared under os_ai_os.drivers:darwin to allow automatic loading via os_ai_os.api.get_drivers().


