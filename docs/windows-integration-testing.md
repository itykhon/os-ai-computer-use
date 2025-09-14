## Windows integration testing options

1) GitHub Actions Windows runner
   - Use `runs-on: windows-latest` to run unit tests and headless checks.
   - GUI automation (PyAutoGUI) is limited on hosted runners (no desktop session). Treat as unit-only.

2) Self-hosted Windows runner
   - Provision a Windows 11 VM or physical machine.
   - Configure as GitHub Actions self-hosted runner.
   - Enable an interactive desktop session (auto-logon) so PyAutoGUI can interact with the desktop.
   - Install dependencies and grant required permissions (UAC prompts off or run as admin).

3) Local VM
   - Use Parallels/VMware/VirtualBox.
   - Run tests manually with `pytest -q` inside the VM. For more realism, write small harness apps (Win32 Forms) to click/type.

4) RDP session caveat
   - Some input APIs behave differently over RDP. Prefer local console or tools like psexec to spawn tests in Session 1.

5) Suggested split
   - CI on windows-latest: unit+contract tests only (no real GUI).
   - Nightly on self-hosted Windows: full integration suite (click/move/type against harness UI).


