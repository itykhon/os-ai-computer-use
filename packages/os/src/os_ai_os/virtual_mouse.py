import time
from typing import Tuple, Optional

from Quartz import (
    CGEventCreateMouseEvent,
    CGEventPost,
    kCGHIDEventTap,
    kCGEventLeftMouseDown,
    kCGEventLeftMouseUp,
    kCGEventRightMouseDown,
    kCGEventRightMouseUp,
    kCGEventOtherMouseDown,
    kCGEventOtherMouseUp,
    kCGEventScrollWheel,
    CGEventSetType,
    CGEventSetIntegerValueField,
    kCGMouseEventButtonNumber,
    CGMainDisplayID,
    CGDisplayHideCursor,
    CGDisplayShowCursor,
)
from AppKit import NSWindow, NSView, NSColor, NSApplication, NSApp, NSBackingStoreBuffered
from AppKit import NSScreen, NSBezierPath
from AppKit import NSStatusWindowLevel, NSScreenSaverWindowLevel
from AppKit import NSWindowCollectionBehaviorCanJoinAllSpaces, NSWindowCollectionBehaviorFullScreenAuxiliary
try:
    from AppKit import NSWindowStyleMaskBorderless as STYLE_BORDERLESS
except Exception:
    from AppKit import NSBorderlessWindowMask as STYLE_BORDERLESS
from Foundation import NSObject, NSRect, NSRunLoop, NSDate

from config.settings import (
    PREMOVE_HIGHLIGHT_ENABLED,
    PREMOVE_HIGHLIGHT_DURATION,
    PREMOVE_HIGHLIGHT_RADIUS,
    PREMOVE_HIGHLIGHT_COLOR,
    PREMOVE_HIGHLIGHT_STROKE_WIDTH,
    PREMOVE_HIGHLIGHT_FILL_COLOR,
    VIRTUAL_CURSOR_SHOW_OVERLAY_CURSOR,
    VIRTUAL_CURSOR_OVERLAY_RADIUS,
    VIRTUAL_CURSOR_OVERLAY_STROKE_WIDTH,
    VIRTUAL_CURSOR_OVERLAY_COLOR,
    VIRTUAL_CURSOR_OVERLAY_FILL_COLOR,
    VIRTUAL_CURSOR_ANIMATE,
    VIRTUAL_CURSOR_ANIMATION_FPS,
)


class VirtualMouse:
    """Отправка событий мыши через Quartz без перемещения системного курсора.

    Ограничения macOS: позиция, в которую попадёт клик, определяется координатами события.
    Поэтому для кликов мы используем CGEventCreateMouseEvent с явными координатами, но 
    не трогаем системный курсор. Для drag моделируем down -> серия кликов/микродвижений -> up.
    """

    def __init__(self):
        # Последняя логическая позиция виртуального курсора (для маркера и drag)
        self._virtual_position: Tuple[int, int] = (0, 0)
        # Оверлей для постоянного маркера и подсветки
        self._overlay_window: Optional[NSWindow] = None
        self._overlay_view: Optional[NSView] = None
        # Состояние подсветки
        self._highlight_active: bool = False
        self._highlight_center: Tuple[int, int] = (0, 0)
        self._highlight_end_ts: float = 0.0

    # --- Позиция виртуального курсора ---
    def set_position(self, x: int, y: int) -> None:
        self._virtual_position = (int(x), int(y))
        self._update_overlay()

    def get_position(self) -> Tuple[int, int]:
        return self._virtual_position

    # --- Клики ---
    def _post_mouse_event(self, event_type: int, x: int, y: int, button_number: int = 0) -> None:
        evt = CGEventCreateMouseEvent(None, event_type, (x, y), button_number)
        # Подстраховка: явно укажем номер кнопки
        CGEventSetIntegerValueField(evt, kCGMouseEventButtonNumber, button_number)
        CGEventPost(kCGHIDEventTap, evt)

    def left_click(self, x: Optional[int] = None, y: Optional[int] = None) -> None:
        px, py = self._virtual_position if x is None or y is None else (int(x), int(y))
        self._post_mouse_event(kCGEventLeftMouseDown, px, py, 0)
        self._post_mouse_event(kCGEventLeftMouseUp, px, py, 0)

    def right_click(self, x: Optional[int] = None, y: Optional[int] = None) -> None:
        px, py = self._virtual_position if x is None or y is None else (int(x), int(y))
        self._post_mouse_event(kCGEventRightMouseDown, px, py, 1)
        self._post_mouse_event(kCGEventRightMouseUp, px, py, 1)

    def middle_click(self, x: Optional[int] = None, y: Optional[int] = None) -> None:
        px, py = self._virtual_position if x is None or y is None else (int(x), int(y))
        self._post_mouse_event(kCGEventOtherMouseDown, px, py, 2)
        self._post_mouse_event(kCGEventOtherMouseUp, px, py, 2)

    # --- Hold / Up ---
    def left_down(self, x: Optional[int] = None, y: Optional[int] = None) -> None:
        px, py = self._virtual_position if x is None or y is None else (int(x), int(y))
        self._post_mouse_event(kCGEventLeftMouseDown, px, py, 0)

    def left_up(self, x: Optional[int] = None, y: Optional[int] = None) -> None:
        px, py = self._virtual_position if x is None or y is None else (int(x), int(y))
        self._post_mouse_event(kCGEventLeftMouseUp, px, py, 0)

    # --- Drag без перемещения системного курсора ---
    def drag(self, start: Tuple[int, int], end: Tuple[int, int], steps: int = 12, delay: float = 0.0) -> None:
        sx, sy = int(start[0]), int(start[1])
        ex, ey = int(end[0]), int(end[1])
        self.set_position(sx, sy)
        self.left_down(sx, sy)
        # Моделируем серию коротких кликов/микроперемещений нажатием и отпусканием на промежуточных точках
        for i in range(1, steps):
            ix = sx + (ex - sx) * i // steps
            iy = sy + (ey - sy) * i // steps
            # для некоторых приложений требуется сгенерировать повторный down на промежуточной точке
            self._post_mouse_event(kCGEventLeftMouseDown, ix, iy, 0)
            if delay:
                time.sleep(delay)
        self.left_up(ex, ey)
        self.set_position(ex, ey)

    # --- Scroll ---
    def scroll(self, vertical: int = 0, horizontal: int = 0) -> None:
        # kCGEventScrollWheel использует величины в «lines». Знак: + вверх, - вниз
        evt = CGEventCreateMouseEvent(None, kCGEventScrollWheel, self._virtual_position, 0)
        CGEventSetType(evt, kCGEventScrollWheel)
        # Поля для скролла: оси 1=вертикаль, 2=горизонталь
        # На уровне простоты используем IntegerValueField, многие примеры обходятся так.
        CGEventSetIntegerValueField(evt, 11, int(vertical))  # kCGScrollWheelEventDeltaAxis1 = 11
        CGEventSetIntegerValueField(evt, 12, int(horizontal))  # kCGScrollWheelEventDeltaAxis2 = 12
        CGEventPost(kCGHIDEventTap, evt)

    # --- Overlay management & pre-move highlight ---
    def _ensure_app(self) -> None:
        try:
            try:
                _ = NSApp()
            except Exception:
                NSApplication.sharedApplication()
            app = NSApp()
            if app is not None:
                try:
                    # 0 = Regular, 1 = Accessory, 2 = Prohibited
                    app.setActivationPolicy_(1)  # Accessory, чтобы не светиться в доке
                except Exception:
                    pass
                try:
                    app.activateIgnoringOtherApps_(True)
                except Exception:
                    pass
        except Exception:
            pass

    def _ensure_overlay(self) -> None:
        try:
            self._ensure_app()
            if self._overlay_window is not None and self._overlay_view is not None:
                return
            screen = NSScreen.mainScreen()
            if screen is None:
                return
            screen_frame = screen.frame()
            window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
                screen_frame,
                STYLE_BORDERLESS,
                NSBackingStoreBuffered,
                False,
            )
            # Максимально поверх всех окон и на всех рабочих столах/Fullscreen
            try:
                window.setLevel_(NSScreenSaverWindowLevel)
            except Exception:
                window.setLevel_(float(1e6))
            window.setOpaque_(False)
            window.setBackgroundColor_(NSColor.clearColor())
            window.setIgnoresMouseEvents_(True)
            try:
                window.setCollectionBehavior_(
                    NSWindowCollectionBehaviorCanJoinAllSpaces | NSWindowCollectionBehaviorFullScreenAuxiliary
                )
            except Exception:
                pass

            vm = self

            class OverlayView(NSView):
                def drawRect_(self, rect):  # type: ignore
                    screen_h = screen_frame.size.height
                    # Прозрачный фон
                    NSColor.clearColor().set()

                    # Persistent virtual cursor marker
                    if VIRTUAL_CURSOR_SHOW_OVERLAY_CURSOR:
                        cx, cy = vm._virtual_position
                        cy = screen_h - cy
                        stroke = NSColor.colorWithCalibratedRed_green_blue_alpha_(
                            VIRTUAL_CURSOR_OVERLAY_COLOR[0] / 255.0,
                            VIRTUAL_CURSOR_OVERLAY_COLOR[1] / 255.0,
                            VIRTUAL_CURSOR_OVERLAY_COLOR[2] / 255.0,
                            VIRTUAL_CURSOR_OVERLAY_COLOR[3] / 255.0,
                        )
                        fill = NSColor.colorWithCalibratedRed_green_blue_alpha_(
                            VIRTUAL_CURSOR_OVERLAY_FILL_COLOR[0] / 255.0,
                            VIRTUAL_CURSOR_OVERLAY_FILL_COLOR[1] / 255.0,
                            VIRTUAL_CURSOR_OVERLAY_FILL_COLOR[2] / 255.0,
                            VIRTUAL_CURSOR_OVERLAY_FILL_COLOR[3] / 255.0,
                        )
                        path = NSBezierPath.bezierPathWithOvalInRect_(NSRect((cx - VIRTUAL_CURSOR_OVERLAY_RADIUS, cy - VIRTUAL_CURSOR_OVERLAY_RADIUS), (2 * VIRTUAL_CURSOR_OVERLAY_RADIUS, 2 * VIRTUAL_CURSOR_OVERLAY_RADIUS)))
                        fill.set()
                        path.fill()
                        stroke.set()
                        path.setLineWidth_(VIRTUAL_CURSOR_OVERLAY_STROKE_WIDTH)
                        path.stroke()

                    # Pre-move highlight ring
                    if vm._highlight_active:
                        hx, hy = vm._highlight_center
                        hy = screen_h - hy
                        ring_stroke = NSColor.colorWithCalibratedRed_green_blue_alpha_(
                            PREMOVE_HIGHLIGHT_COLOR[0] / 255.0,
                            PREMOVE_HIGHLIGHT_COLOR[1] / 255.0,
                            PREMOVE_HIGHLIGHT_COLOR[2] / 255.0,
                            PREMOVE_HIGHLIGHT_COLOR[3] / 255.0,
                        )
                        ring_fill = NSColor.colorWithCalibratedRed_green_blue_alpha_(
                            PREMOVE_HIGHLIGHT_FILL_COLOR[0] / 255.0,
                            PREMOVE_HIGHLIGHT_FILL_COLOR[1] / 255.0,
                            PREMOVE_HIGHLIGHT_FILL_COLOR[2] / 255.0,
                            PREMOVE_HIGHLIGHT_FILL_COLOR[3] / 255.0,
                        )
                        pr = PREMOVE_HIGHLIGHT_RADIUS
                        ring = NSBezierPath.bezierPathWithOvalInRect_(NSRect((hx - pr, hy - pr), (2 * pr, 2 * pr)))
                        ring_fill.set()
                        ring.fill()
                        ring_stroke.set()
                        ring.setLineWidth_(PREMOVE_HIGHLIGHT_STROKE_WIDTH)
                        ring.stroke()

            view = OverlayView.alloc().initWithFrame_(screen_frame)
            window.setContentView_(view)
            window.orderFrontRegardless()
            window.display()
            self._overlay_window = window
            self._overlay_view = view
        except Exception:
            # Безопасно для headless окружений
            pass

    def _update_overlay(self) -> None:
        try:
            self._ensure_overlay()
            if self._overlay_view is not None and self._overlay_window is not None:
                self._overlay_view.setNeedsDisplay_(True)
                self._overlay_window.display()
        except Exception:
            pass

    def highlight_position(self, x: int, y: int, radius: Optional[int] = None, duration: Optional[float] = None) -> None:
        if not PREMOVE_HIGHLIGHT_ENABLED:
            return
        try:
            r = int(radius if radius is not None else PREMOVE_HIGHLIGHT_RADIUS)
            dur = float(duration if duration is not None else PREMOVE_HIGHLIGHT_DURATION)
            self._ensure_overlay()
            self._highlight_active = True
            self._highlight_center = (int(x), int(y))
            self._update_overlay()
            # Прокрутим run loop, чтобы гарантировать отрисовку оверлея
            try:
                deadline = NSDate.dateWithTimeIntervalSinceNow_(dur)
                NSRunLoop.currentRunLoop().runUntilDate_(deadline)
            except Exception:
                time.sleep(dur)
        finally:
            self._highlight_active = False
            self._update_overlay()

    # --- Virtual cursor animation (overlay-only) ---
    def animate_move(self, to_x: int, to_y: int, duration: float) -> None:
        if not VIRTUAL_CURSOR_ANIMATE or duration <= 0:
            self.set_position(to_x, to_y)
            return
        fps = max(10, int(VIRTUAL_CURSOR_ANIMATION_FPS))
        steps = max(1, int(duration * fps))
        from_x, from_y = self._virtual_position
        for i in range(1, steps + 1):
            nx = from_x + (to_x - from_x) * i // steps
            ny = from_y + (to_y - from_y) * i // steps
            self.set_position(nx, ny)
            # Обновляем оверлей и даём шансу перерисоваться
            self._update_overlay()
            delay = max(0.0, duration / steps)
            try:
                deadline = NSDate.dateWithTimeIntervalSinceNow_(delay)
                NSRunLoop.currentRunLoop().runUntilDate_(deadline)
            except Exception:
                time.sleep(delay)

    # --- System cursor visibility helpers ---
    def hide_system_cursor(self) -> None:
        try:
            CGDisplayHideCursor(CGMainDisplayID())
        except Exception:
            pass

    def show_system_cursor(self) -> None:
        try:
            CGDisplayShowCursor(CGMainDisplayID())
        except Exception:
            pass


# Депрекейтед модуль: сохранён ради совместимости импорта
# Экспортируем только функцию подсветки из нового overlay
from os_ai_os_macos.overlay import highlight_position  # type: ignore


