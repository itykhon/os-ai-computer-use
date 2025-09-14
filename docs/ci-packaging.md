## CI packaging & publishing

Recommended steps for mono-repo:

1) Build wheels per package:
   - `packages/os`: `python -m build` or `uv build`
   - `packages/os-macos`: `python -m build`
   - `packages/core`: `python -m build`

2) Versioning: bump via CI job or commit tag; ensure inter-package constraints are updated.

3) Publish to internal index (or PyPI) with token secrets.

4) Matrix by OS for tests:
   - macOS runner installs both `os_ai_os` and `os_ai_os_macos` and runs integration_os tests
   - Linux/Windows runners install only `os_ai_os` and run unit tests

5) Entry points: verify `os_ai_os_macos` declares `os_ai_os.drivers: darwin` and that import works.


