from __future__ import annotations

import sys


def main(argv: list[str]) -> int:
    try:
        from os_ai_os_macos.os_runner import main as mac_main  # type: ignore
    except Exception:
        print("os_runner is only available on macOS in this project setup")
        return -1
    return mac_main(argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))


