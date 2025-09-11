PY?=$(shell which python)
PIP?=$(shell which pip)

.PHONY: venv install lint test unit itest itest-local keyboard click macos-perms macos-open-accessibility macos-open-input-monitoring macos-open-screen-recording

venv:
	@echo "(optional) manage your venv outside Makefile"

install:
	$(PY) -m pip install -r requirements.txt

lint:
	pytest -q -k "not integration_os"

test unit:
	pytest -q tests/unit

# Integration OS tests (macOS GUI). Requires Accessibility permissions.
itest:
	RUN_CURSOR_TESTS=1 pytest -q -s tests/integration

# Run OS harness manually without pytest
itest-local-keyboard:
	$(PY) -m utils.os_runner keyboard || true

itest-local-click:
	$(PY) -m utils.os_runner click || true

# Open macOS privacy panes for granting permissions
macos-open-accessibility:
	open "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"

macos-open-input-monitoring:
	open "x-apple.systempreferences:com.apple.preference.security?Privacy_ListenEvent"

macos-open-screen-recording:
	open "x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture"

macos-perms: macos-open-accessibility macos-open-input-monitoring macos-open-screen-recording


