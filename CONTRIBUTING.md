# Contributing Guide

Thanks for your interest in contributing! This guide explains how to work with the codebase and submit changes.

## Getting Started
- Fork the repository and create a feature branch from `main`.
- Use Python 3.12+ and a virtual environment.
- Install dependencies: `make install` or local editable installs with `make dev-install`.
- Read `README.md` and `docs/os-architecture.md` for an overview.

## Development Workflow
1. Implement changes following `CODE_STYLE.md`.
2. Add/update tests:
   - Unit tests: `make test`
   - Integration (macOS GUI): `RUN_CURSOR_TESTS=1 make itest`
3. Ensure all tests pass locally.
4. Submit a Pull Request with a clear description and motivation.

## Code Style & Linting
- Format with Black (line length 100) or Ruff formatter.
- Run Ruff: `ruff check .` and address warnings.
- Use type hints for public functions and modules.

## Architecture Rules
- Core must depend only on OS ports (`@os`); platform specifics live in `@os-macos` / `@os-windows`.
- Avoid importing platform APIs in core modules.
- Keep new features covered by unit tests and, if needed, integration tests.

## Commit Messages
- Prefer Conventional Commits (e.g., `feat:`, `fix:`, `docs:`, `refactor:`).
- Keep commits small and focused.

## CI & Packaging
- See `docs/ci-packaging.md` for packaging, artifacts, and release notes.
- Windows integration is best on a self-hosted runner; see `docs/windows-integration-testing.md`.

## Reporting Issues
- Use GitHub Issues. Include steps to reproduce, expected/actual behavior, logs, and environment details.

## License
- By contributing, you agree your contributions are licensed under the repository's Apache 2.0 license.

Thanks for contributing! 🚀
