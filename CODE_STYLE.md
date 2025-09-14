# Code Style

This project targets Python 3.12+ and prioritizes clarity, correctness, and maintainability.

## Formatting
- Use Black for formatting (recommend line length 100):
  - `pip install black`
  - `black --line-length 100 .`
- Imports: let Black handle; if you prefer, use isort with Black profile.

## Linting
- Use Ruff for fast linting:
  - `pip install ruff`
  - `ruff check .`
  - `ruff format .` (optional formatter alternative)
- Keep warnings minimal; prefer fixing over silencing.

## Typing
- Public APIs and module boundaries must use type hints.
- Avoid `Any` and unchecked casts; prefer precise types.
- Use `from __future__ import annotations` in new modules.

## Structure & Architecture
- OS‑agnostic core depends on ports only (see `docs/os-architecture.md`).
- Platform specifics live in dedicated packages (`@os-macos`, `@os-windows`).
- Keep platform imports out of core modules.

## Control Flow & Errors
- Use guard clauses and early returns; avoid deep nesting (>3 levels).
- Handle edge cases first; never swallow exceptions silently.
- Log meaningful context on errors.

## Logging
- Use the central logger: `logging.getLogger(LOGGER_NAME)`.
- Keep logs high-signal and structured; avoid noisy prints.

## Comments & Docs
- Use concise comments to explain "why", not "how".
- Prefer docstrings for public functions/classes (Google style is fine).

## Tests
- Add unit tests for logic; integration tests for OS interactions where applicable.
- Run:
  - `make test`
  - `RUN_CURSOR_TESTS=1 make itest` (macOS GUI)

## Commits
- Prefer Conventional Commits (e.g., `feat:`, `fix:`, `docs:`).
- Keep commits small and focused.


