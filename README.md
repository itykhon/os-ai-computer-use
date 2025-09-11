# macOS Desktop Agent Core

Локальный агент для автоматизации действий на macOS с использованием Anthropic Computer Use (Claude). Агент умеет:

- двигать и кликать системным курсором с плавной анимацией
- выполнять drag-and-drop (с тонкой настройкой шагов/задержек)
- нажимать сочетания клавиш, надёжный Enter через Quartz
- делать скриншоты (Quartz или PyAutoGUI), сохранять их на диск и возвращать в tool_result
- рисовать «подсветку» цели перед перемещением (overlay поверх всех окон)
- вести подробные логи, оценивать стоимость токенов, обрабатывать 429 (retry)

Проект рассчитан на локальный запуск и удобную интеграцию с Flutter как GUI (см. `docs/flutter.md`).

---

## Быстрый старт

Требования:
- macOS 13+
- Python 3.12+
- Доступ к антропику (переменная окружения `ANTHROPIC_API_KEY`)

Установка:
```bash
# (опционально) создать и активировать venv
python -m venv .venv && source .venv/bin/activate

# установить зависимости
make install
```

Разрешения macOS (GUI‑автоматизация требует прав):
```bash
# откроет панели System Settings → Privacy & Security
make macos-perms
```
Включите разрешения как минимум для вашего терминала (Terminal/iTerm) и для Python из текущего venv в разделах:
- Accessibility
- Input Monitoring
- Screen Recording

Запуск агента:
```bash
export ANTHROPIC_API_KEY=sk-ant-...
python main.py --debug --task "Open Safari, search for 'macOS automation', scroll, make a screenshot"
```

Полезные make-команды:
```bash
make install               # зависимости
make test                  # юнит‑тесты
RUN_CURSOR_TESTS=1 make itest  # интеграционные GUI‑тесты (требуют разрешений)
make itest-local-keyboard  # ручной прогон клавиатуры
make itest-local-click     # ручной прогон кликов/drag
```

---

## Основные возможности

- Плавное перемещение курсора: твины, длительности зависят от расстояния
- Подсветка цели перед перемещением: overlay‑окна поверх всех Spaces/Fullscreen
- Клики с модификаторами: `modifiers: "cmd+shift"` для кликов и down/up
- Управление drag:
  - `hold_before_ms`, `hold_after_ms`: задержки до/после удержания
  - `steps`, `step_delay`: пошаговый drag для сложных UI (таблицы, dnd‑гриды)
- Нажатие клавиш и хоткеев: `key`, `hold_key`; надёжный Enter через Quartz (`utils/keyboard.py`)
- Скриншоты: Quartz‑захват или PyAutoGUI; downscale к «модельному» разрешению
- Логи и стоимость: учёт токенов, суммарная стоимость; гибкая обработка 429

---

## Конфигурация (config/settings.py)

Ключевые параметры (неполный список):
- Координаты/калибровка
  - `COORD_X_SCALE`, `COORD_Y_SCALE`, `COORD_X_OFFSET`, `COORD_Y_OFFSET`
  - Пост‑коррекция позиции: `POST_MOVE_VERIFY`, `POST_MOVE_TOLERANCE_PX`, `POST_MOVE_CORRECTION_DURATION`
- Скриншоты
  - `USE_QUARTZ_SCREENSHOT`, `SCREENSHOT_MODE` (native|downscale)
  - `VIRTUAL_DISPLAY_ENABLED`, `VIRTUAL_DISPLAY_WIDTH_PX`, `VIRTUAL_DISPLAY_HEIGHT_PX`
  - `SCREENSHOT_FORMAT` (PNG|JPEG), `SCREENSHOT_JPEG_QUALITY`
- Подсветка
  - `PREMOVE_HIGHLIGHT_ENABLED`, `PREMOVE_HIGHLIGHT_DEFAULT_DURATION`, `PREMOVE_HIGHLIGHT_RADIUS` и цвета
- Модель/инструмент
  - `MODEL_NAME`, `COMPUTER_TOOL_TYPE`, `COMPUTER_BETA_FLAG`, `MAX_TOKENS`
  - `ALLOW_PARALLEL_TOOL_USE` — параллельные tool_use от модели (по умолчанию выключено)

См. файл для полного списка и комментариев.

---

## API действий (tool input)

Агент ожидает от модели блок с полем `action` и параметрами:

- Перемещение курсора
```json
{"action":"mouse_move","coordinate":[x,y],"coordinate_space":"auto|screen|model","duration":0.35,"tween":"linear"}
```
- Клики
```json
{"action":"left_click","coordinate":[x,y],"modifiers":"cmd+shift"}
```
- Нажатие/удержание
```json
{"action":"key","key":"cmd+l"}
{"action":"hold_key","key":"ctrl+shift+t"}
```
- Drag‑and‑drop
```json
{
  "action":"left_click_drag",
  "start":[x1,y1],
  "end":[x2,y2],
  "modifiers":"shift",
  "hold_before_ms":80,
  "hold_after_ms":80,
  "steps":4,
  "step_delay":0.02
}
```
- Скролл
```json
{"action":"scroll","coordinate":[x,y],"scroll_direction":"down|up|left|right","scroll_amount":3}
```
- Ввод текста
```json
{"action":"type","text":"Hello, world!"}
```
- Скриншот
```json
{"action":"screenshot"}
```

Ответы приходят как список контент‑блоков tool_result (text/image). Скриншоты возвращаются в base64.

---

## Тесты

Юнит‑тесты (без реального GUI):
```bash
make test
```
Интеграционные (реальные OS‑тесты, только macOS):
```bash
export RUN_CURSOR_TESTS=1
make itest
```
Если macOS блокирует автоматизацию (нет прав), тесты будут `skipped`. Выдайте права через `make macos-perms` и повторите.

---

## Интеграция с Flutter

Рекомендуемая архитектура — Flutter как чистый GUI, Python‑сервис локально:
- Транспорт: WebSocket + JSON‑RPC для чата/команд, REST для файлов
- Потоки: скриншоты (JPEG/PNG), логи, события действий
- Примерная схема указана в `docs/flutter.md`

---

## Контрибьютинг

- Форк → ветка feature/… → PR
- Код‑стайл: читаемый, явные имена, без глубоких вложенностей
- Тесты: добавляйте юнит‑тесты к логике и, при необходимости, интеграционные
- Перед PR:
```bash
make test
RUN_CURSOR_TESTS=1 make itest   # опционально, если обновляли GUI‑взаимодействия
```
- Сообщения коммитов — понятные и атомарные

---

## Лицензия

Код распространяется под лицензией **Apache License 2.0**. Файл `NOTICE` обязателен к сохранению при распространении.

- См. `LICENSE` и `NOTICE` в корне репозитория.

---

## Траблшутинг

- «Cursor/keyboard не работает»: проверьте выдачу прав в System Settings → Privacy & Security (Accessibility, Input Monitoring, Screen Recording) для терминала и текущего Python.
- «Интеграционные тесты падают/skip»: перезапустите терминал, убедитесь, что используете тот же `python` (см. `which python`, `python -c 'import sys; print(sys.executable)'`).
- «Скриншоты пустые/без overlay»: включите Screen Recording для терминала, проверьте `USE_QUARTZ_SCREENSHOT`.

---

## Контакты

Issues/PR — в этом репозитории. Атрибуция указана в `NOTICE`.


## TODO

- Кэширование промпта: использовать Prompt Caching для системного промпта/общих инструкций, чтобы не платить за них каждый раз (см. раздел Prompt caching в доках Anthropic).

- Кадрирование скриншотов: добавить действие screenshot_region (x,y,w,h) и просить модель снимать только локальную область (таблица/диалог), а не весь экран.

- Переключение модели: если позволяет сценарий, рассмотреть Sonnet 3.7 (часто дешевле на вход) вместо полноразмерного Claude 4 для рутинных шагов; «думать» включать точечно.





- 1) Да. Мы можем обязать модель на каждом шаге отдавать компактный «контекстный блок» (state + step) — либо как отдельный text-блок JSON, либо прямо в tool_use.input (доп. поля). В system_prompt задаём контракт, например:
  - state_update: {app, url, focus, modal, auth, last_screenshot?}
  - step_log: {action, target, intent, result, retry?, error?}
  - лимиты: ≤ 400–600 символов, без base64/скринов. Модель будет следовать этому в каждом tool_use (см. agent loop в доке Anthropic Computer Use [ссылка](https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/computer-use-tool)).

- 2) Отдельный дешёвый summarizer — хорошая альтернатива/усиление. Делать периодический вызов лёгкой модели (например, «haiku») для сжатия «старшего хвоста» сообщений в наш целевой формат (state + steps). Стоимость одной сводки обычно меньше, чем постоянная «думательная» нагрузка основной модели, а основной диалог остаётся чистым и коротким.

Рекомендую гибрид:
- Контракт на «state_update + step_log» в каждом шаге (почти нулевой оверхед).
- Периодическая свёртка истории дешёвой моделью (каждые N итераций/по превышению длины) в долговременный summary, который подмешиваем в system и обрезаем хвост.

Готов внедрить:
- Обновлю system_prompt с жёстким контрактом по полям/лимитам.
- Добавлю класс Summarizer (например, `utils/summarizers/llm_summarizer.py`) с вызовом дешёвой модели и интегрирую его в `ConversationOptimizer` (триггеры: длина/интервал).