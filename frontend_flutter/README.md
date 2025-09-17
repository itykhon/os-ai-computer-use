OS AI Frontend (Flutter)
========================

<img width="605" height="669" alt="image" src="https://github.com/user-attachments/assets/37b23301-250a-49e7-89c3-648cc543e09a" />


Realtime desktop agent UI for OS AI. Connects to the local backend via WebSocket (JSON‑RPC) and REST for files. Shows thoughts, actions (with icons and badges), screenshots (zoomable), iterative usage, connection status, and total cost/tokens.

Features
--------
- Provider‑agnostic LLM display: logs, actions, screenshots, usage
- Action badges with icons for common `@os/` actions (click, move, type, wait, screenshot)
- Connection status (connecting/connected/offline/error) + network awareness
- Theme toggle (light/dark) using `ThemeExtensions`
- “Thinking…” placeholder while a job is running
- “Stop” button to cancel running jobs
- Context preservation: last N user/assistant text pairs sent to backend
- Screenshots: 150×150 preview with Zoom in/out to full width
- Cumulative usage: shows per‑iteration and Σ totals (USD and tokens)

Architecture & Stack
--------------------
- Flutter + MobX + Provider
- WebSocket (`web_socket_channel`) + JSON‑RPC 2.0 to backend
- REST (`dio`) for file upload and health
- Theming: `ThemeData` with `AppThemeColors` and `AppThemeStyles` (`ThemeExtensions`)
- Connectivity: `connectivity_plus` (graceful fallback if plugin not available)

Platform Support (OS Drivers)
-----------------------------
- macOS: Supported today via `packages/os-macos/` (AppKit overlay, Quartz screenshot, robust Enter, sounds)
- Windows: Implemented via `packages/os-windows/` (mouse/keyboard/screen with PyAutoGUI); overlay/sound minimal. Needs integration testing before claiming parity

Backend Requirements
--------------------
Run the local backend first. See repo root `README.md` and `docs/backend-jsonrpc.md`.

Quick backend start (dev):
```bash
# in repo root (ensure Python 3.12+ and deps installed)
export ANTHROPIC_API_KEY=sk-ant-...
os-ai-backend   # or: python main.py --provider anthropic --debug
```

Backend config exposed to frontend:
- `/healthz` returns subset including `history_pairs_limit` used by the chat context size

Running the Frontend
--------------------
Dev run:
```bash
flutter pub get
flutter run -d macos   # or your target device
```

Production build (examples):
```bash
# macOS desktop app
flutter build macos

# Web (optional)
flutter build web
```

Environment & Config
--------------------
- Default backend WS: `ws://127.0.0.1:8765/ws?token=secret`
- Default REST base: `http://127.0.0.1:8765`
- You can change host/port/token in `AppConfig` (UI can be wired later)

Screens & Widgets
-----------------
- `ChatScreen`: header (status, running indicator, theme toggle), messages list, input composer
- `ChatMessagesList`: renders thoughts, actions (badges), screenshots (zoomable), usage, text
- `ChatInputComposer`: text input, Send, Stop (visible only while running), attach file

Notes
-----
- All UI strings are in English
- No dependency on GoogleFonts; colors and styles via theme extensions
- Avoid using `Colors.black` directly; always use `context.themeColors`/`context.theme`

