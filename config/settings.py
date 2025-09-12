"""Глобальные константы и настройки приложения."""

from typing import Tuple

# PyAutoGUI base timings
PYAUTO_PAUSE_SECONDS: float = 0.05
PYAUTO_FAILSAFE: bool = True

# Mouse animation defaults
DEFAULT_MOVE_SPEED_PPS: float = 1200.0
DEFAULT_DRAG_SPEED_PPS: float = 1000.0
MIN_MOVE_DURATION: float = 0.30
MAX_MOVE_DURATION: float = 1.5

# LLM / Tools (provider-agnostic defaults)
# Provider selection: "anthropic" | "openai"
LLM_PROVIDER: str = "anthropic"

# Anthropic defaults
MODEL_NAME: str = "claude-sonnet-4-20250514"
COMPUTER_TOOL_TYPE: str = "computer_20250124"
COMPUTER_BETA_FLAG: str = "computer-use-2025-01-24"

# OpenAI defaults (for Computer Use / o4-mini / gpt-4.1, etc.)
OPENAI_MODEL_NAME: str = "o4-mini"

MAX_TOKENS: int = 1500

# Logging
LOGGER_NAME: str = "agent"

# macOS Accessibility
MACOS_ACCESSIBILITY_REQUIRED: bool = True
MACOS_ACCESSIBILITY_PROMPT_ON_MISSING: bool = True

# HTTP 429 retry/backoff
API_MAX_RETRIES: int = 5
API_BACKOFF_BASE_SECONDS: float = 3.0
API_BACKOFF_MAX_SECONDS: float = 30.0
API_BACKOFF_JITTER_SECONDS: float = 0.5

# Tool use parallelism
ALLOW_PARALLEL_TOOL_USE: bool = False  # set True to let the model request parallel tool_use

# API request timeouts (seconds)
API_REQUEST_TIMEOUT_SECONDS: float = 20.0

# Conversation optimization
SIMPLE_STEP_MAX_TOKENS: int = 600      # для простых шагов (клик/скролл/короткий ввод)
HISTORY_MAX_MESSAGES: int = 14         # держим последние N сообщений в истории
HISTORY_SUMMARY_MAX_CHARS: int = 800   # предел символов для текстовой сводки старых сообщений


# Coordinate calibration (for Retina/offset tweaks)
COORD_X_SCALE: float = 1.0
COORD_Y_SCALE: float = 1.0
COORD_X_OFFSET: int = 0
COORD_Y_OFFSET: int = 0

# Post-move verification/correction
POST_MOVE_VERIFY: bool = True
POST_MOVE_TOLERANCE_PX: int = 2
POST_MOVE_CORRECTION_DURATION: float = 0.05

# Typing settings (Unicode handling)
TYPING_USE_CLIPBOARD_FOR_NON_ASCII: bool = True
RESTORE_CLIPBOARD_AFTER_PASTE: bool = True
PASTE_COPY_DELAY_SECONDS: float = 0.05
PASTE_POST_DELAY_SECONDS: float = 0.05

# Pre-move highlight circle overlay
PREMOVE_HIGHLIGHT_ENABLED: bool = True
PREMOVE_HIGHLIGHT_DURATION: float = 4
PREMOVE_HIGHLIGHT_RADIUS: int = 36
PREMOVE_HIGHLIGHT_COLOR: Tuple[int, int, int, int] = (255, 0, 0, 255)
PREMOVE_HIGHLIGHT_STROKE_WIDTH: float = 8.0
PREMOVE_HIGHLIGHT_FILL_COLOR: Tuple[int, int, int, int] = (255, 0, 0, 220)

# Non-blocking short pre-move highlight default (used by main)
PREMOVE_HIGHLIGHT_DEFAULT_DURATION: float = 0.20

# Virtual display presented to the model (recommended ≤ 1280x800)
VIRTUAL_DISPLAY_ENABLED: bool = True
VIRTUAL_DISPLAY_WIDTH_PX: int = 1024
VIRTUAL_DISPLAY_HEIGHT_PX: int = None

# Screenshot capture settings
USE_QUARTZ_SCREENSHOT: bool = True  # try Quartz/CGDisplayCreateImage; fallback to PyAutoGUI
SCREENSHOT_MODE: str = "downscale"  # "downscale" | "native" (native is heavier)
SCREENSHOT_FORMAT: str = "JPEG"      # "PNG" | "JPEG"
SCREENSHOT_JPEG_QUALITY: int = 50    # used when SCREENSHOT_FORMAT == "JPEG"

# Screenshot cadence (enable to append screenshots after actions for better context tracking)
SCREENSHOT_AFTER_ACTIONS: bool = True
SCREENSHOT_AFTER_ACTIONS_ACTIONS: Tuple[str, ...] = (
    "key",
    "left_click",
    "double_click",
    "triple_click",
    "right_click",
    "middle_click",
    "left_mouse_down",
    "left_mouse_up",
    "left_click_drag",
    "scroll",
    "type",
    "mouse_move",
)


# Sound settings
CLICK_SOUND_ENABLED: bool = True
CLICK_SOUND_PATH: str = "assets/sounds/mouse_click.mp3"
CLICK_SOUND_VOLUME: float = 0.7  # 0.0 - 1.0

# Done sound
DONE_SOUND_ENABLED: bool = True
DONE_SOUND_PATH: str = "assets/sounds/done.mp3"
DONE_SOUND_VOLUME: float = 0.9  # 0.0 - 1.0


# Cost estimation (USD per 1M tokens) — adjust to your Anthropic pricing
# Defaults reflect typical Sonnet pricing; update as needed.
COST_INPUT_PER_MTOKENS_USD: float = 3.0
COST_OUTPUT_PER_MTOKENS_USD: float = 15.0

# Long-context pricing (Sonnet 4 with 1M context)
LONG_CONTEXT_INPUT_TOKENS_THRESHOLD: int = 200_000
COST_INPUT_PER_MTOKENS_USD_LONG_CONTEXT: float = 6.0
COST_OUTPUT_PER_MTOKENS_USD_LONG_CONTEXT: float = 22.5


# Usage logging
USAGE_LOG_EACH_ITERATION: bool = True  # логировать usage/cost после каждого запроса к модели

