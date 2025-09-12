import os, time, base64, argparse, json, sys, logging, random
import httpx
from typing import List, Dict, Any, Tuple
import pyautogui
from config.settings import (
    PYAUTO_PAUSE_SECONDS,
    PYAUTO_FAILSAFE,
    DEFAULT_MOVE_SPEED_PPS,
    DEFAULT_DRAG_SPEED_PPS,
    MIN_MOVE_DURATION,
    MAX_MOVE_DURATION,
    MODEL_NAME,
    COMPUTER_TOOL_TYPE,
    COMPUTER_BETA_FLAG,
    MAX_TOKENS,
    LOGGER_NAME,
    MACOS_ACCESSIBILITY_REQUIRED,
    MACOS_ACCESSIBILITY_PROMPT_ON_MISSING,
    API_MAX_RETRIES,
    API_BACKOFF_BASE_SECONDS,
    API_BACKOFF_MAX_SECONDS,
    API_BACKOFF_JITTER_SECONDS,
    COORD_X_SCALE,
    COORD_Y_SCALE,
    COORD_X_OFFSET,
    COORD_Y_OFFSET,
    POST_MOVE_VERIFY,
    POST_MOVE_TOLERANCE_PX,
    POST_MOVE_CORRECTION_DURATION,
    PREMOVE_HIGHLIGHT_DEFAULT_DURATION,
    COST_INPUT_PER_MTOKENS_USD,
    COST_OUTPUT_PER_MTOKENS_USD,
    VIRTUAL_DISPLAY_ENABLED,
    VIRTUAL_DISPLAY_WIDTH_PX,
    VIRTUAL_DISPLAY_HEIGHT_PX,
    USE_QUARTZ_SCREENSHOT,
    SCREENSHOT_MODE,
    SCREENSHOT_FORMAT,
    SCREENSHOT_JPEG_QUALITY,
    ALLOW_PARALLEL_TOOL_USE,
)

# Доп. конфиг для частых скриншотов после действий
try:
    from config.settings import SCREENSHOT_AFTER_ACTIONS, SCREENSHOT_AFTER_ACTIONS_ACTIONS
except Exception:
    SCREENSHOT_AFTER_ACTIONS = False
    SCREENSHOT_AFTER_ACTIONS_ACTIONS = tuple()

# -------- macOS подготовка экрана --------
# Узнаём размер экрана и используем его в tool-параметрах,
# чтобы координаты от модели совпадали с реальными пикселями.
SCREEN_W, SCREEN_H = pyautogui.size()

# Модельное (виртуальное) разрешение, показываемое инструменту, и динамический скейл координат
if (SCREENSHOT_MODE or "downscale").lower() == "native":
    MODEL_DISPLAY_W = SCREEN_W
    MODEL_DISPLAY_H = SCREEN_H
    DYNAMIC_X_SCALE = 1.0
    DYNAMIC_Y_SCALE = 1.0
else:
    if VIRTUAL_DISPLAY_ENABLED:
        # Безопасное вычисление высоты, если не задана/некорректна: сохраняем соотношение сторон экрана
        try:
            vd_w = int(VIRTUAL_DISPLAY_WIDTH_PX)
        except Exception:
            vd_w = SCREEN_W
        try:
            vd_h = int(VIRTUAL_DISPLAY_HEIGHT_PX)
        except Exception:
            vd_h = 0
        if vd_w <= 0:
            vd_w = SCREEN_W
        if vd_h <= 0:
            # автоподбор высоты под текущий экран
            vd_h = max(1, int(round(float(SCREEN_H) * float(vd_w) / float(SCREEN_W))))
        MODEL_DISPLAY_W = vd_w
        MODEL_DISPLAY_H = vd_h
        try:
            DYNAMIC_X_SCALE = float(SCREEN_W) / float(MODEL_DISPLAY_W)
            DYNAMIC_Y_SCALE = float(SCREEN_H) / float(MODEL_DISPLAY_H)
        except Exception:
            DYNAMIC_X_SCALE = 1.0
            DYNAMIC_Y_SCALE = 1.0
    else:
        MODEL_DISPLAY_W = SCREEN_W
        MODEL_DISPLAY_H = SCREEN_H
        DYNAMIC_X_SCALE = 1.0
        DYNAMIC_Y_SCALE = 1.0

# Безопасная пауза между действиями, чтобы UI успевал обновляться
pyautogui.PAUSE = PYAUTO_PAUSE_SECONDS
pyautogui.FAILSAFE = PYAUTO_FAILSAFE  # угол экрана мышью = аварийная остановка

# ---- Сопоставление аспектов: контентная область (letterbox) для downscale ----
# При даунскейле сохраняем исходный аспект экрана и добавляем «поля», чтобы избежать геометрических искажений.
try:
    if (SCREENSHOT_MODE or "downscale").lower() == "downscale" and VIRTUAL_DISPLAY_ENABLED:
        screen_aspect = float(SCREEN_W) / float(SCREEN_H)
        model_aspect = float(MODEL_DISPLAY_W) / float(MODEL_DISPLAY_H)
        if screen_aspect > model_aspect:
            # Экран шире целевой модели: подгоняем высоту, по бокам полей нет
            MODEL_CONTENT_W = int(MODEL_DISPLAY_W)
            MODEL_CONTENT_H = max(1, int(round(MODEL_DISPLAY_W / screen_aspect)))
            MODEL_LB_OFFSET_X = 0
            MODEL_LB_OFFSET_Y = int((int(MODEL_DISPLAY_H) - MODEL_CONTENT_H) / 2)
        else:
            # Экран уже (или равен): подгоняем ширину, сверху/снизу поля
            MODEL_CONTENT_H = int(MODEL_DISPLAY_H)
            MODEL_CONTENT_W = max(1, int(round(MODEL_DISPLAY_H * screen_aspect)))
            MODEL_LB_OFFSET_Y = 0
            MODEL_LB_OFFSET_X = int((int(MODEL_DISPLAY_W) - MODEL_CONTENT_W) / 2)
    else:
        MODEL_CONTENT_W = int(MODEL_DISPLAY_W)
        MODEL_CONTENT_H = int(MODEL_DISPLAY_H)
        MODEL_LB_OFFSET_X = 0
        MODEL_LB_OFFSET_Y = 0
except Exception:
    MODEL_CONTENT_W = int(MODEL_DISPLAY_W)
    MODEL_CONTENT_H = int(MODEL_DISPLAY_H)
    MODEL_LB_OFFSET_X = 0
    MODEL_LB_OFFSET_Y = 0

try:
    CONTENT_X_SCALE = float(SCREEN_W) / float(MODEL_CONTENT_W)
    CONTENT_Y_SCALE = float(SCREEN_H) / float(MODEL_CONTENT_H)
except Exception:
    CONTENT_X_SCALE = float(SCREEN_W) / float(max(1, int(MODEL_DISPLAY_W)))
    CONTENT_Y_SCALE = float(SCREEN_H) / float(max(1, int(MODEL_DISPLAY_H)))

# -------- утилиты --------
from utils.logger import setup_logging
from utils.logger import get_logger as _get_logger
from utils.overlay import highlight_position, process_overlay_events
from utils.sound import play_click_sound, play_done_sound
from utils.keyboard import press_enter_mac
from utils.conversation_optimizer import ConversationOptimizer
import pyperclip

# Глобально запоминаем путь к последнему сохранённому скриншоту (для дебага)
LAST_SCREENSHOT_PATH: str | None = None

# Плавность перемещений курсора — из конфига

def _resolve_tween(params: Dict[str, Any]):
    """Возвращает функцию твина для анимации перемещений курсора."""
    tween_name = (params.get("tween") or params.get("easing") or "easeInOutQuad").lower()
    mapping = {
        "linear": getattr(pyautogui, "linear", None),
        "easeinoutquad": getattr(pyautogui, "easeInOutQuad", None),
        "easeinquad": getattr(pyautogui, "easeInQuad", None),
        "easeoutquad": getattr(pyautogui, "easeOutQuad", None),
    }
    tween_fn = mapping.get(tween_name)
    return tween_fn or getattr(pyautogui, "easeInOutQuad", None)

def _compute_duration_to(target_x: int, target_y: int, params: Dict[str, Any], *,
                         default: float, speed_pps: float) -> float:
    """Вычисляет длительность перемещения. Приоритет: params.duration -> по расстоянию -> default."""
    try:
        if "duration" in params or "move_duration" in params:
            val = float(params.get("duration", params.get("move_duration")))
            return max(MIN_MOVE_DURATION, min(MAX_MOVE_DURATION, val))
        # По расстоянию с учетом текущей позиции
        cx, cy = pyautogui.position()
        dist = ((target_x - cx) ** 2 + (target_y - cy) ** 2) ** 0.5
        dur = dist / float(speed_pps)
        return max(MIN_MOVE_DURATION, min(MAX_MOVE_DURATION, dur))
    except Exception:
        return default

def _capture_quartz_image():
    try:
        # Попытка захвата через Quartz для скорости и точности
        from Quartz import (
            CGDisplayCreateImage,
            CGMainDisplayID,
            CGImageGetWidth,
            CGImageGetHeight,
            CGImageGetDataProvider,
            CGImageGetBytesPerRow,
            CGDataProviderCopyData,
        )
        from PIL import Image  # type: ignore
        image_ref = CGDisplayCreateImage(CGMainDisplayID())
        if not image_ref:
            return None
        width = int(CGImageGetWidth(image_ref))
        height = int(CGImageGetHeight(image_ref))
        provider = CGImageGetDataProvider(image_ref)
        data = CGDataProviderCopyData(provider)
        buf = bytes(data)
        # macOS обычно BGRA, bytes_per_row может отличаться — используем точный stride из CGImage
        try:
            bytes_per_row = int(CGImageGetBytesPerRow(image_ref))
        except Exception:
            bytes_per_row = width * 4
        try:
            # Используем правильный stride, чтобы избежать "наклонов"/артефактов
            img = Image.frombuffer("RGBA", (width, height), buf, "raw", "BGRA", bytes_per_row, 1)
        except Exception:
            # Fallback: простая конверсия через frombytes (может быть медленнее)
            img = Image.frombytes("RGBA", (width, height), buf, "raw", "BGRA", bytes_per_row, 1)
        return img
    except Exception:
        return None


def b64_image_from_screenshot() -> Dict[str, Any]:
    # Захват экрана (Quartz, затем fallback на PyAutoGUI)
    img = None
    if USE_QUARTZ_SCREENSHOT:
        img = _capture_quartz_image()
    if img is None:
        img = pyautogui.screenshot(region=(0, 0, SCREEN_W, SCREEN_H))  # PIL Image

    try:
        from PIL import Image, ImageOps  # type: ignore
        target_w, target_h = int(MODEL_DISPLAY_W), int(MODEL_DISPLAY_H)
        if (SCREENSHOT_MODE or "downscale").lower() == "downscale":
            # Даунскейлим с сохранением аспекта экрана и добавлением «полей» (letterbox)
            if img.width != SCREEN_W or img.height != SCREEN_H:
                img = img.resize((SCREEN_W, SCREEN_H), resample=getattr(Image, "LANCZOS", None) or Image.BILINEAR)
            # Вписываем контент в MODEL_CONTENT_* и добавляем поля до целевого MODEL_DISPLAY_*
            content = img.resize((MODEL_CONTENT_W, MODEL_CONTENT_H), resample=getattr(Image, "LANCZOS", None) or Image.BILINEAR)
            # Создаём полотно и вклеиваем по смещению
            canvas = Image.new("RGB", (target_w, target_h), (0, 0, 0))
            canvas.paste(content, (MODEL_LB_OFFSET_X, MODEL_LB_OFFSET_Y))
            img = canvas
        else:
            if img.width != target_w or img.height != target_h:
                resample = getattr(Image, "LANCZOS", getattr(Image, "BILINEAR", None))
                img = img.resize((target_w, target_h), resample=resample)
    except Exception:
        pass

    from io import BytesIO
    buf = BytesIO()
    fmt = (SCREENSHOT_FORMAT or "PNG").upper()
    media_type = "image/png" if fmt == "PNG" else "image/jpeg"
    try:
        # Сохранение файла на диск
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            save_dir = os.path.join(base_dir, "screenshots")
            os.makedirs(save_dir, exist_ok=True)
            ts = time.strftime("%Y%m%d_%H%M%S")
            ms = int((time.time() - int(time.time())) * 1000)
            ext = "jpg" if fmt == "JPEG" else "png"
            file_path = os.path.join(save_dir, f"screenshot_{ts}_{ms:03d}.{ext}")
            if fmt == "JPEG":
                img_to_save = img.convert("RGB")
                img_to_save.save(file_path, format="JPEG", quality=int(SCREENSHOT_JPEG_QUALITY or 85))
            else:
                img.save(file_path, format="PNG")
            global LAST_SCREENSHOT_PATH
            LAST_SCREENSHOT_PATH = file_path
            logging.getLogger(LOGGER_NAME).info(f"Saved screenshot: {file_path}")
        except Exception:
            pass

        # Кодирование для tool_result
        if fmt == "JPEG":
            img_enc = img.convert("RGB")
            img_enc.save(buf, format="JPEG", quality=int(SCREENSHOT_JPEG_QUALITY or 85))
        else:
            img.save(buf, format="PNG")
    except Exception:
        # Фоллбек надёжный PNG
        try:
            img.save(buf, format="PNG")
            media_type = "image/png"
        except Exception:
            # Последний шанс — пустой PNG
            return {
                "type": "image",
                "source": {"type": "base64", "media_type": "image/png", "data": ""},
            }

    data = base64.b64encode(buf.getvalue()).decode("ascii")
    return {
        "type": "image",
        "source": {"type": "base64", "media_type": media_type, "data": data},
    }

def clamp_xy(x: int, y: int) -> Tuple[int, int]:
    return max(0, min(x, SCREEN_W - 1)), max(0, min(y, SCREEN_H - 1))


def _apply_calibration(x: int, y: int) -> Tuple[int, int]:
    """Применяет масштаб и оффсеты из конфига, округляя до пикселей."""
    try:
        # Только пользовательская калибровка. Динамический скейл (виртуал->физический)
        # применяем отдельно в _to_screen_xy когда координаты приходят из модельного пространства.
        cx = int(round(x * float(COORD_X_SCALE) + float(COORD_X_OFFSET)))
        cy = int(round(y * float(COORD_Y_SCALE) + float(COORD_Y_OFFSET)))
        return cx, cy
    except Exception:
        return x, y


def _to_screen_xy(x: int, y: int, *, coordinate_space: str | None = None) -> Tuple[int, int]:
    """Преобразует входные координаты в экранные пиксели.

    coordinate_space:
      - "model"  -> сначала масштабируем из модельного пространства (виртуальный дисплей)
      - "screen" -> считаем, что уже в экранных пикселях
      - "auto"   -> эвристика: если координаты выходят за рамки MODEL_DISPLAY_* — трактуем как screen, иначе как model
      - None     -> по умолчанию "screen" (для обратной совместимости и тестов)
    """
    try:
        space = (coordinate_space or "screen").lower()
    except Exception:
        space = "screen"
    sx, sy = int(x), int(y)
    if space == "auto":
        try:
            if int(sx) > int(MODEL_DISPLAY_W) or int(sy) > int(MODEL_DISPLAY_H):
                space = "screen"
            else:
                space = "model"
        except Exception:
            space = "screen"
    if space == "model":
        try:
            # Учитываем letterbox-область модельного изображения: сначала вычитаем смещение полей,
            # затем масштабируем только содержимое без полей, чтобы точка попадала в правильные физические пиксели.
            sx_adj = float(sx) - float(MODEL_LB_OFFSET_X)
            sy_adj = float(sy) - float(MODEL_LB_OFFSET_Y)
            # ограничиваем внутри контентной области
            sx_adj = max(0.0, min(sx_adj, float(MODEL_CONTENT_W) - 1.0))
            sy_adj = max(0.0, min(sy_adj, float(MODEL_CONTENT_H) - 1.0))
            sx = int(round(sx_adj * float(CONTENT_X_SCALE)))
            sy = int(round(sy_adj * float(CONTENT_Y_SCALE)))
        except Exception:
            try:
                sx = int(round(float(sx) * float(DYNAMIC_X_SCALE)))
                sy = int(round(float(sy) * float(DYNAMIC_Y_SCALE)))
            except Exception:
                pass
    sx, sy = _apply_calibration(sx, sy)
    return clamp_xy(sx, sy)

def parse_key_combo(combo: str) -> List[str]:
    """
    Преобразует строки вида 'cmd+l', 'ctrl+shift+t' к названиям клавиш PyAutoGUI.
    """
    mapping = {
        "cmd": "command", "command": "command",
        "ctrl": "ctrl", "control": "ctrl",
        "alt": "option", "option": "option",
        "shift": "shift",
        "enter": "enter", "return": "enter",
        "esc": "esc", "escape": "esc",
        "tab": "tab",
        # добавьте при необходимости
    }
    keys = []
    for k in combo.lower().split("+"):
        k = k.strip()
        keys.append(mapping.get(k, k))  # буквенно-цифровые идут как есть
    return keys

def _with_modifiers(mods: List[str], action_fn):
    mods = [m for m in mods if m]
    try:
        for m in mods:
            pyautogui.keyDown(m)
        return action_fn()
    finally:
        for m in reversed(mods):
            try:
                pyautogui.keyUp(m)
            except Exception:
                pass

def handle_computer_action(action: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Возвращает список контент-блоков для tool_result (текст/картинка).
    Для screenshot возвращаем image; для прочих — текст "ok" (и опционально снимок).
    """
    try:
        logger = logging.getLogger(LOGGER_NAME)
        # Санитизируем параметры для логов (скрываем длинный текст)
        safe_params = dict(params or {})
        if isinstance(safe_params.get("text"), str):
            safe_params["text"] = f"<{len(safe_params['text'])} chars>"
        logger.debug(f"handle_computer_action: action={action} params={safe_params}")

        if action == "screenshot":
            logger.info("Screenshot captured")
            return [b64_image_from_screenshot()]

        if action == "mouse_move":
            x, y = params.get("coordinate", [0, 0])
            coord_space = params.get("coordinate_space")
            x, y = _to_screen_xy(int(x), int(y), coordinate_space=coord_space)
            tween_fn = _resolve_tween(params)
            dur = _compute_duration_to(x, y, params, default=0.35, speed_pps=DEFAULT_MOVE_SPEED_PPS)
            try:
                try:
                    # короткая подсветка точки назначения; не блокируем надолго
                    highlight_position(x, y, duration=PREMOVE_HIGHLIGHT_DEFAULT_DURATION)
                except Exception:
                    pass
                pyautogui.moveTo(x, y, duration=dur, tween=tween_fn)
                # даём оверлею шанс обновиться
                try:
                    process_overlay_events()
                except Exception:
                    pass
                # Пост‑проверка: если система посадила курсор мимо цели — подкорректируем
                if POST_MOVE_VERIFY:
                    try:
                        ax, ay = pyautogui.position()
                        dx, dy = abs(ax - x), abs(ay - y)
                        if dx > POST_MOVE_TOLERANCE_PX or dy > POST_MOVE_TOLERANCE_PX:
                            pyautogui.moveTo(x, y, duration=max(0.0, POST_MOVE_CORRECTION_DURATION), tween=getattr(pyautogui, "linear", None))
                    except Exception:
                        pass
            except pyautogui.FailSafeException:
                logging.getLogger(LOGGER_NAME).warning("PyAutoGUI fail-safe triggered during move; skipping move")
                return [{"type": "text", "text": "move skipped: fail-safe"}]
            logger.info(f"Mouse moved to ({x},{y}) duration={dur:.2f}s")
            if SCREENSHOT_AFTER_ACTIONS and "mouse_move" in SCREENSHOT_AFTER_ACTIONS_ACTIONS:
                return [b64_image_from_screenshot()]
            return [{"type": "text", "text": "ok"}]

        if action in ("left_click", "double_click", "triple_click", "right_click", "middle_click"):
            coord = params.get("coordinate")
            clicks = 1
            button = "left"
            if action == "double_click": clicks = 2
            if action == "triple_click": clicks = 3
            if action == "right_click":  button = "right"
            if action == "middle_click": button = "middle"
            # modifiers support (e.g., shift+click)
            raw_mods = params.get("modifiers") or []
            if isinstance(raw_mods, str):
                raw_mods = [s.strip() for s in raw_mods.split("+") if s.strip()]
            modifiers = parse_key_combo("+".join(raw_mods)) if raw_mods else []
            if coord:
                coord_space = params.get("coordinate_space")
                x, y = _to_screen_xy(int(coord[0]), int(coord[1]), coordinate_space=coord_space)
                tween_fn = _resolve_tween(params)
                dur = _compute_duration_to(x, y, params, default=0.30, speed_pps=DEFAULT_MOVE_SPEED_PPS)
                pyautogui.moveTo(x, y, duration=dur, tween=tween_fn)
                try:
                    def _do():
                        pyautogui.click(x=x, y=y, clicks=clicks, button=button, interval=0.05)
                    _with_modifiers(modifiers, _do)
                except pyautogui.FailSafeException:
                    logging.getLogger(LOGGER_NAME).warning("PyAutoGUI fail-safe triggered during click; skipping click")
                    return [{"type": "text", "text": "click skipped: fail-safe"}]
                try:
                    play_click_sound()
                except Exception:
                    pass
                logger.info(f"{action} at ({x},{y}) move_duration={dur:.2f}s")
            else:
                try:
                    def _do():
                        pyautogui.click(clicks=clicks, button=button, interval=0.05)
                    _with_modifiers(modifiers, _do)
                except pyautogui.FailSafeException:
                    logging.getLogger(LOGGER_NAME).warning("PyAutoGUI fail-safe triggered during click at current position; skipping click")
                    return [{"type": "text", "text": "click skipped: fail-safe"}]
                try:
                    play_click_sound()
                except Exception:
                    pass
                logger.info(f"{action} at current position")
            blocks = []
            if SCREENSHOT_AFTER_ACTIONS and action in SCREENSHOT_AFTER_ACTIONS_ACTIONS:
                blocks.append(b64_image_from_screenshot())
            blocks.append({"type": "text", "text": f"done: {action}"})
            return blocks

        if action in ("left_mouse_down", "left_mouse_up"):
            coord = params.get("coordinate")
            raw_mods = params.get("modifiers") or []
            if isinstance(raw_mods, str):
                raw_mods = [s.strip() for s in raw_mods.split("+") if s.strip()]
            modifiers = parse_key_combo("+".join(raw_mods)) if raw_mods else []
            if coord:
                coord_space = params.get("coordinate_space")
                x, y = _to_screen_xy(int(coord[0]), int(coord[1]), coordinate_space=coord_space)
                tween_fn = _resolve_tween(params)
                dur = _compute_duration_to(x, y, params, default=0.30, speed_pps=DEFAULT_MOVE_SPEED_PPS)
                try:
                    pyautogui.moveTo(x, y, duration=dur, tween=tween_fn)
                except pyautogui.FailSafeException:
                    logging.getLogger(LOGGER_NAME).warning("PyAutoGUI fail-safe triggered during move before mouse down/up; skipping move")
            try:
                def _do():
                    if action == "left_mouse_down":
                        pyautogui.mouseDown(button="left")
                    else:
                        pyautogui.mouseUp(button="left")
                _with_modifiers(modifiers, _do)
            except pyautogui.FailSafeException:
                logging.getLogger(LOGGER_NAME).warning("PyAutoGUI fail-safe triggered during mouse down/up; skipping")
                return [{"type": "text", "text": f"{action} skipped: fail-safe"}]
            logger.info(f"{action} executed")
            blocks = []
            if SCREENSHOT_AFTER_ACTIONS and action in SCREENSHOT_AFTER_ACTIONS_ACTIONS:
                blocks.append(b64_image_from_screenshot())
            blocks.append({"type": "text", "text": f"done: {action}"})
            return blocks

        if action == "left_click_drag":
            # поддерживаем разные варианты полей
            start = params.get("start") or params.get("from") or params.get("source") \
                    or params.get("start_coordinate") or params.get("from_coordinate")
            end   = params.get("end")   or params.get("to")   or params.get("target") \
                    or params.get("end_coordinate")   or params.get("to_coordinate")
            if not (start and end):
                logger.warning("drag skipped: missing start/end")
                return [{"type": "text", "text": "drag skipped: missing start/end"}]
            coord_space = params.get("coordinate_space")
            x1, y1 = _to_screen_xy(int(start[0]), int(start[1]), coordinate_space=coord_space)
            x2, y2 = _to_screen_xy(int(end[0]),   int(end[1]), coordinate_space=coord_space)
            # drag tuning
            hold_before_ms = int(params.get("hold_before_ms", 50))
            hold_after_ms = int(params.get("hold_after_ms", 50))
            steps = max(1, int(params.get("steps", 1)))
            step_delay = max(0.0, float(params.get("step_delay", 0.0)))
            raw_mods = params.get("modifiers") or []
            if isinstance(raw_mods, str):
                raw_mods = [s.strip() for s in raw_mods.split("+") if s.strip()]
            modifiers = parse_key_combo("+".join(raw_mods)) if raw_mods else []
            tween_fn = _resolve_tween(params)
            move_dur = _compute_duration_to(x1, y1, params, default=0.30, speed_pps=DEFAULT_MOVE_SPEED_PPS)
            try:
                pyautogui.moveTo(x1, y1, duration=move_dur, tween=tween_fn)
                def _do_drag():
                    time.sleep(max(0.0, hold_before_ms / 1000.0))
                    pyautogui.mouseDown(button="left")
                    if steps <= 1:
                        drag_dur = _compute_duration_to(x2, y2, params, default=0.40, speed_pps=DEFAULT_DRAG_SPEED_PPS)
                        pyautogui.moveTo(x2, y2, duration=drag_dur, tween=tween_fn)
                    else:
                        for i in range(1, steps + 1):
                            nx = int(round(x1 + (x2 - x1) * (i / float(steps))))
                            ny = int(round(y1 + (y2 - y1) * (i / float(steps))))
                            step_dur = _compute_duration_to(nx, ny, params, default=0.05, speed_pps=DEFAULT_DRAG_SPEED_PPS)
                            pyautogui.moveTo(nx, ny, duration=step_dur, tween=tween_fn)
                            if step_delay > 0:
                                time.sleep(step_delay)
                    time.sleep(max(0.0, hold_after_ms / 1000.0))
                    pyautogui.mouseUp(button="left")
                _with_modifiers(modifiers, _do_drag)
            except pyautogui.FailSafeException:
                logging.getLogger(LOGGER_NAME).warning("PyAutoGUI fail-safe triggered during drag; skipping drag")
                return [{"type": "text", "text": "drag skipped: fail-safe"}]
            logger.info(f"drag {x1},{y1}->{x2},{y2}")
            blocks = []
            if SCREENSHOT_AFTER_ACTIONS and action in SCREENSHOT_AFTER_ACTIONS_ACTIONS:
                blocks.append(b64_image_from_screenshot())
            blocks.append({"type": "text", "text": f"done: {action}"})
            return blocks

        if action == "type":
            text = params.get("text", "")
            # Если есть не-ASCII символы, используем буфер обмена + Cmd+V для надёжного ввода Unicode
            try:
                non_ascii = any(ord(c) > 127 for c in text)
            except Exception:
                non_ascii = False
            if non_ascii:
                try:
                    from config.settings import (
                        TYPING_USE_CLIPBOARD_FOR_NON_ASCII,
                        RESTORE_CLIPBOARD_AFTER_PASTE,
                        PASTE_COPY_DELAY_SECONDS,
                        PASTE_POST_DELAY_SECONDS,
                    )
                    if TYPING_USE_CLIPBOARD_FOR_NON_ASCII:
                        try:
                            prev_clip = pyperclip.paste()
                        except Exception:
                            prev_clip = None
                        try:
                            pyperclip.copy(text)
                            time.sleep(PASTE_COPY_DELAY_SECONDS)
                            # Cmd+V на macOS
                            pyautogui.hotkey("command", "v")
                            time.sleep(PASTE_POST_DELAY_SECONDS)
                        finally:
                            if RESTORE_CLIPBOARD_AFTER_PASTE and prev_clip is not None:
                                try:
                                    pyperclip.copy(prev_clip)
                                except Exception:
                                    pass
                        logger.info(f"Pasted {len(text)} chars via clipboard")
                        return [{"type": "text", "text": f"pasted {len(text)} chars via clipboard"}]
                except Exception:
                    # Fallback на посимвольный ввод
                    pass
            # По умолчанию посимвольная печать (ASCII и fallback)
            pyautogui.write(text, interval=0.02)
            logger.info(f"Typed {len(text)} chars")
            blocks = []
            if SCREENSHOT_AFTER_ACTIONS and action in SCREENSHOT_AFTER_ACTIONS_ACTIONS:
                blocks.append(b64_image_from_screenshot())
            blocks.append({"type": "text", "text": "done: drag"})
            return blocks

        if action in ("key", "hold_key"):
            combo = params.get("key") or params.get("keys") or params.get("combo") or ""
            # Строго нормализуем список клавиш
            try:
                if isinstance(combo, str):
                    norm_keys = [k for k in parse_key_combo(combo) if isinstance(k, str) and k.strip()]
                elif isinstance(combo, (list, tuple)):
                    tmp = []
                    for v in combo:
                        if isinstance(v, str):
                            tmp.extend(parse_key_combo(v))
                        else:
                            s = str(v).strip()
                            if s:
                                tmp.append(s)
                    norm_keys = [k for k in tmp if isinstance(k, str) and k.strip()]
                else:
                    norm_keys = []
            except Exception:
                norm_keys = []

            if not norm_keys:
                # Fallback: если пришёл одиночный символ/строка для печати, используем печать
                fallback_text = params.get("text") or params.get("character")
                if isinstance(fallback_text, str) and fallback_text:
                    pyautogui.write(fallback_text, interval=0.02)
                    logger.info(f"Typed {len(fallback_text)} chars via key-fallback")
                    blocks = []
                    if SCREENSHOT_AFTER_ACTIONS and "key" in SCREENSHOT_AFTER_ACTIONS_ACTIONS:
                        blocks.append(b64_image_from_screenshot())
                    blocks.append({"type": "text", "text": f"typed: {len(fallback_text)} chars"})
                    return blocks
                combo_raw = combo if isinstance(combo, str) else str(combo)
                logger.warning(f"Pressed <empty combo> raw='{combo_raw}'")
                return [{"type": "text", "text": f"error: missing key combo (raw='{combo_raw}')"}]

            # Проверим неизвестные клавиши и красиво залогируем
            try:
                allowed_mods = {"command", "ctrl", "option", "alt", "shift"}
                specials = {"enter", "esc", "escape", "tab", "space", "backspace", "delete", "home", "end", "pageup", "pagedown", "up", "down", "left", "right"}
                letters = {chr(c) for c in range(ord('a'), ord('z') + 1)}
                digits = {str(d) for d in range(0, 10)}
                fkeys = {f"f{i}" for i in range(1, 25)}
                allowed = allowed_mods | specials | letters | digits | fkeys
                unknown = [k for k in norm_keys if k.lower() not in allowed]
                if unknown:
                    combo_raw = combo if isinstance(combo, str) else str(combo)
                    logger.warning(f"Unknown key(s) in combo: {unknown} raw='{combo_raw}'")
                    return [{"type": "text", "text": f"error: unknown key(s) {unknown} (raw='{combo_raw}')"}]
            except Exception:
                pass

            pressed_label = "+".join(norm_keys)
            if action == "hold_key":
                if len(norm_keys) < 2:
                    logger.warning("hold_key requires at least 2 keys (modifiers + key)")
                    return [{"type": "text", "text": "error: hold_key needs modifiers+key"}]
                try:
                    for k in norm_keys[:-1]:
                        pyautogui.keyDown(k)
                    pyautogui.press(norm_keys[-1])
                finally:
                    for k in reversed(norm_keys[:-1]):
                        pyautogui.keyUp(k)
            else:
                if len(norm_keys) == 1 and norm_keys[0] in ("enter", "return"):
                    try:
                        press_enter_mac()
                    except Exception:
                        pyautogui.press("enter")
                else:
                    if len(norm_keys) == 1:
                        pyautogui.press(norm_keys[0])
                    else:
                        pyautogui.hotkey(*norm_keys)
            logger.info(f"Pressed {pressed_label}")
            blocks = []
            if SCREENSHOT_AFTER_ACTIONS and "key" in SCREENSHOT_AFTER_ACTIONS_ACTIONS:
                blocks.append(b64_image_from_screenshot())
            blocks.append({"type": "text", "text": f"pressed: {pressed_label}"})
            return blocks

        if action == "scroll":
            coord = params.get("coordinate")
            direction = (params.get("scroll_direction") or "down").lower()
            amount = int(params.get("scroll_amount", 1))
            if coord:
                coord_space = params.get("coordinate_space")
                x, y = _to_screen_xy(int(coord[0]), int(coord[1]), coordinate_space=coord_space)
                tween_fn = _resolve_tween(params)
                dur = _compute_duration_to(x, y, params, default=0.25, speed_pps=DEFAULT_MOVE_SPEED_PPS)
                try:
                    pyautogui.moveTo(x, y, duration=dur, tween=tween_fn)
                except pyautogui.FailSafeException:
                    logging.getLogger(LOGGER_NAME).warning("PyAutoGUI fail-safe triggered during move before scroll; skipping move")
            # В PyAutoGUI: + вверх, - вниз
            if direction in ("down", "up"):
                clicks = -abs(amount) if direction == "down" else abs(amount)
                try:
                    pyautogui.scroll(clicks)
                except pyautogui.FailSafeException:
                    logging.getLogger(LOGGER_NAME).warning("PyAutoGUI fail-safe triggered during scroll; skipping scroll")
                    return [{"type": "text", "text": "scroll skipped: fail-safe"}]
            elif direction in ("left", "right"):
                clicks = -abs(amount) if direction == "left" else abs(amount)
                try:
                    pyautogui.hscroll(clicks)
                except AttributeError:
                    # Fallback: emulate horizontal scroll via shift+vertical scroll
                    try:
                        pyautogui.keyDown("shift")
                        pyautogui.scroll(clicks)
                    finally:
                        pyautogui.keyUp("shift")
                except pyautogui.FailSafeException:
                    logging.getLogger(LOGGER_NAME).warning("PyAutoGUI fail-safe triggered during hscroll; skipping hscroll")
                    return [{"type": "text", "text": "hscroll skipped: fail-safe"}]
            logger.info(f"Scrolled {direction} {amount}")
            if SCREENSHOT_AFTER_ACTIONS and action in SCREENSHOT_AFTER_ACTIONS_ACTIONS:
                return [b64_image_from_screenshot()]
            return [{"type": "text", "text": "ok"}]

        if action == "wait":
            sec = float(params.get("seconds", 0.2))
            time.sleep(sec)
            logging.getLogger(LOGGER_NAME).info(f"Waited {sec}s")
            return [{"type": "text", "text": "ok"}]

        # по умолчанию — нераспознанный экшен
        logger.warning(f"unknown action '{action}'")
        return [{"type": "text", "text": f"error: unknown action '{action}'"}]

    except Exception as e:
        logging.getLogger(LOGGER_NAME).exception(f"Error executing action '{action}'")
        return [{"type": "text", "text": f"error executing '{action}': {e}"}]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Universal Computer Use agent (macOS).")
    parser.add_argument("--task", type=str, required=False,
                        help="Что сделать при запуске (естественным языком).")
    parser.add_argument("--debug", action="store_true", help="Включить подробные логи (DEBUG)")
    # Legacy flags removed; only new orchestrator path is supported
    parser.add_argument("--provider", type=str, required=False, help="Провайдер LLM: anthropic|openai")
    args = parser.parse_args()

    # Логгер до начала работы
    logger = setup_logging(debug=args.debug)

    logger.info(f"Screen size detected: {SCREEN_W}x{SCREEN_H}; pause={pyautogui.PAUSE}, failsafe={pyautogui.FAILSAFE}")

    if args.task:
        task_text = args.task
    else:
        logger.info("Awaiting task input from stdin...")
        print("Введите задачу (пример: 'Открой Chrome, зайди на google.com, выбери вторую страницу результатов поиска'):")
        task_text = sys.stdin.readline().strip()

    from llm.types import ToolDescriptor
    from di import create_container
    from orchestrator import Orchestrator
    inj = create_container(args.provider)
    from llm.interfaces import LLMClient as _LLMClient
    from tools.registry import ToolRegistry as _ToolRegistry
    client = inj.get(_LLMClient)
    tools = inj.get(_ToolRegistry)
    orch = Orchestrator(client, tools)
    # Build tool descriptors for computer
    tool_descs = [
        ToolDescriptor(
            name="computer",
            kind="computer_use",
            params={
                "type": COMPUTER_TOOL_TYPE,
                "display_width_px": MODEL_DISPLAY_W,
                "display_height_px": MODEL_DISPLAY_H,
            },
        )
    ]
    system_prompt = (
        "You are an expert desktop operator. Use the computer tool to complete the user's task. "
        "ONLY take a screenshot when needed. Prefer keyboard shortcuts. "
        "NEVER send empty key combos; always include a valid key or hotkey like 'cmd+space'. "
        "When using key/hold_key, provide 'key' or 'keys' as a non-empty string (e.g., 'cmd+space', 'ctrl+c'). "
        "For any action with coordinates, set coordinate_space='auto' in tool input."
    )
    msgs = orch.run(task_text, tool_descs, system_prompt, max_iterations=30)
    # Print final assistant text(s)
    final_texts = []
    for m in msgs:
        if getattr(m, "role", None) == "assistant":
            for p in (getattr(m, "content", []) or []):
                try:
                    if getattr(p, "type", None) == "text":
                        final_texts.append(str(getattr(p, "text", "")))
                except Exception:
                    pass
    if final_texts:
        print("\n".join(final_texts).strip())
    try:
        play_done_sound()
    except Exception:
        pass
