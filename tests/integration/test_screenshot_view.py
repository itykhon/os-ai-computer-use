import os
import platform
import importlib
import base64
from io import BytesIO

import pytest
from PIL import Image


@pytest.mark.integration_os
@pytest.mark.skipif(platform.system() != "Darwin", reason="Mac-only GUI test")
@pytest.mark.skipif(os.environ.get("RUN_CURSOR_TESTS") != "1", reason="Set RUN_CURSOR_TESTS=1 to enable GUI screenshot test")
def test_screenshot_saves_and_prints_path():
    # Импортируем основной модуль и вызываем screenshot action через тот же код, что использует агент
    main = importlib.import_module("main")
    blocks = main.handle_computer_action("screenshot", {})
    assert isinstance(blocks, list) and len(blocks) == 1
    blk = blocks[0]
    assert blk.get("type") == "image"
    src = blk.get("source") or {}
    assert src.get("type") == "base64"
    data_b64 = src.get("data")
    assert isinstance(data_b64, str) and len(data_b64) > 0

    # Файл, сохранённый в коде, должен существовать
    path = getattr(main, "LAST_SCREENSHOT_PATH", None)
    assert isinstance(path, str) and len(path) > 0, "LAST_SCREENSHOT_PATH is empty"
    assert os.path.exists(path), f"Screenshot file not found: {path}"

    # Сверяем размеры base64-изображения и сохранённого файла
    raw = base64.b64decode(data_b64.encode("ascii"))
    with Image.open(BytesIO(raw)) as im_buf:
        with Image.open(path) as im_file:
            assert im_buf.size == im_file.size

    # Печатаем путь, чтобы можно было открыть из терминала (pytest -s)
    print(f"Screenshot saved: {path}")
    print(f"Open with: open '{path}'")


