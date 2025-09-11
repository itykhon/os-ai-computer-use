import os
from typing import Optional

from config.settings import (
    CLICK_SOUND_ENABLED,
    CLICK_SOUND_PATH,
    CLICK_SOUND_VOLUME,
    DONE_SOUND_ENABLED,
    DONE_SOUND_PATH,
    DONE_SOUND_VOLUME,
)
from utils.logger import get_logger

try:
    # macOS-native playback via AppKit (supports mp3)
    from AppKit import NSSound  # type: ignore
    _HAVE_APPKIT = True
except Exception:
    _HAVE_APPKIT = False

_cached_click: Optional[object] = None  # NSSound
_cached_done: Optional[object] = None   # NSSound


def _resolve_path(path: str) -> str:
    if os.path.isabs(path):
        return path
    # project_root = parent of utils directory
    project_root = os.path.dirname(os.path.dirname(__file__))
    return os.path.join(project_root, path)


def _load_nssound(abs_path: str, volume: float) -> Optional[object]:
    if not _HAVE_APPKIT:
        return None
    if not os.path.isfile(abs_path):
        return None
    try:
        snd = NSSound.alloc().initWithContentsOfFile_byReference_(abs_path, True)  # type: ignore
        if snd is None:
            return None
        # volume 0.0 - 1.0
        vol = max(0.0, min(1.0, float(volume)))
        try:
            snd.setVolume_(vol)  # type: ignore
        except Exception:
            pass
        return snd
    except Exception:
        return None


def play_click_sound() -> None:
    """Проигрывает звук клика, если включено и доступно. Неблокирующе."""
    if not CLICK_SOUND_ENABLED:
        return
    logger = get_logger()
    abs_path = _resolve_path(CLICK_SOUND_PATH)

    if _HAVE_APPKIT:
        global _cached_click
        # Не кэшируем один объект, чтобы повторный проигрыш не зависал.
        # Некоторые версии NSSound требуют новый экземпляр для надежного повтора.
        snd = _load_nssound(abs_path, CLICK_SOUND_VOLUME)
        if snd is None:
            return
        try:
            snd.play()  # type: ignore
        except Exception:
            logger.debug("Click sound playback failed (ignored)")
        return

    # Fallbacks (none configured) — quietly ignore
    # Optionally, you could implement 'afplay' subprocess call on macOS here.
    return


def play_done_sound() -> None:
    """Проигрывает финальный звук завершения, если включено и доступно. Неблокирующе."""
    if not DONE_SOUND_ENABLED:
        return
    logger = get_logger()
    abs_path = _resolve_path(DONE_SOUND_PATH)

    if _HAVE_APPKIT:
        global _cached_done
        snd = _load_nssound(abs_path, DONE_SOUND_VOLUME)
        if snd is None:
            return
        try:
            snd.play()  # type: ignore
        except Exception:
            logger.debug("Done sound playback failed (ignored)")
        return

    return


