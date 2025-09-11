import os
import sys


# Ensure project root is on sys.path so `import utils.*` works when running from tests/
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def pytest_collection_modifyitems(session, config, items):
    # Mark integration tests collected under tests/integration as such
    for item in items:
        if "/tests/integration/" in str(getattr(item, "fspath", "")):
            item.add_marker("integration")


