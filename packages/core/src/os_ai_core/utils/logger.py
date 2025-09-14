import logging
import sys


LOGGER_NAME = "agent"


def setup_logging(debug: bool = False) -> logging.Logger:
    """Настраивает консольный логгер с префиксом 🤖 и выводом времени/уровня.

    Все наши логи будут начинаться с "🤖 ". Уровень по умолчанию INFO, при --debug -> DEBUG.
    """
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    # Сброс существующих хендлеров при повторной инициализации
    for h in list(logger.handlers):
        logger.removeHandler(h)

    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setLevel(logging.DEBUG if debug else logging.INFO)
    formatter = logging.Formatter(
        fmt="🤖 %(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Приглушаем шум от сторонних библиотек (если не в debug)
    if not debug:
        logging.getLogger("anthropic").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)

    return logger


def get_logger() -> logging.Logger:
    """Возвращает настроенный логгер приложения."""
    return logging.getLogger(LOGGER_NAME)


