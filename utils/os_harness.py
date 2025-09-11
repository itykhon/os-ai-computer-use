from __future__ import annotations

import time
from typing import Tuple

from AppKit import (
    NSApp,
    NSApplication,
    NSWindow,
    NSView,
    NSTextView,
    NSScrollView,
    NSColor,
    NSScreen,
    NSBackingStoreBuffered,
)
try:
    from AppKit import NSWindowStyleMaskTitled as STYLE_TITLED
except Exception:
    from AppKit import NSTitledWindowMask as STYLE_TITLED
from Foundation import NSMakeRect, NSDate, NSRunLoop
import objc


def pump_runloop(seconds: float) -> None:
    try:
        deadline = NSDate.dateWithTimeIntervalSinceNow_(seconds)
        NSRunLoop.currentRunLoop().runUntilDate_(deadline)
    except Exception:
        time.sleep(seconds)


class ClickCaptureView(NSView):
    def initWithFrame_(self, frame):  # type: ignore
        self = objc.super(ClickCaptureView, self).initWithFrame_(frame)
        if self is None:
            return None
        self.clicked = False
        self.last_pos = (0, 0)
        return self

    def mouseDown_(self, event):  # type: ignore
        p = self.convertPoint_fromView_(event.locationInWindow(), None)
        self.clicked = True
        self.last_pos = (float(p.x), float(p.y))

    def drawRect_(self, rect):  # type: ignore
        NSColor.whiteColor().set()
        rect.fill()


class TestWindow:
    def __init__(self, width: int = 400, height: int = 300, x: int | None = None, y: int | None = None):
        self._ensure_app()
        screen = NSScreen.mainScreen()
        sframe = screen.frame()
        # Place window near top-left to simplify screen coord math
        w, h = float(width), float(height)
        if x is None:
            x = 50
        if y is None:
            # Position from bottom: screen_h - top_margin - h
            y = int(sframe.size.height - 100 - h)
        frame = NSMakeRect(float(x), float(y), w, h)
        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(frame, STYLE_TITLED, NSBackingStoreBuffered, False)
        self.window.setTitle_("OS Harness Test Window")
        self.window.setBackgroundColor_(NSColor.whiteColor())
        # Text view for keyboard tests
        self.text_scroll = NSScrollView.alloc().initWithFrame_(NSMakeRect(10, 60, w - 20, h - 70))
        self.text_view = NSTextView.alloc().initWithFrame_(self.text_scroll.contentView().frame())
        self.text_view.setRichText_(False)
        self.text_view.setEditable_(True)
        self.text_view.setString_("")
        self.text_scroll.setDocumentView_(self.text_view)
        # Click capture area at bottom
        self.click_view = ClickCaptureView.alloc().initWithFrame_(NSMakeRect(10, 10, 120, 40))
        self.window.contentView().addSubview_(self.text_scroll)
        self.window.contentView().addSubview_(self.click_view)
        self.window.makeKeyAndOrderFront_(None)
        try:
            NSApp.activateIgnoringOtherApps_(True)
        except Exception:
            pass
        pump_runloop(0.2)

    def _ensure_app(self) -> None:
        try:
            _ = NSApp()
        except Exception:
            NSApplication.sharedApplication()

    def get_text(self) -> str:
        return str(self.text_view.string())

    def focus_text(self) -> Tuple[int, int]:
        # Click center of text view to focus it; returns screen coords (pyautogui)
        frame = self.window.frame()
        tv_frame = self.text_scroll.frame()
        local_x = float(tv_frame.origin.x + tv_frame.size.width / 2.0)
        local_y = float(tv_frame.origin.y + tv_frame.size.height / 2.0)
        return self.local_to_screen_px(local_x, local_y)

    def click_target_point(self) -> Tuple[int, int]:
        # Point inside click_view
        frame = self.click_view.frame()
        local_x = float(frame.origin.x + frame.size.width / 2.0)
        local_y = float(frame.origin.y + frame.size.height / 2.0)
        return self.local_to_screen_px(local_x, local_y)

    def local_to_screen_px(self, lx: float, ly: float) -> Tuple[int, int]:
        screen = NSScreen.mainScreen()
        sframe = screen.frame()
        wframe = self.window.frame()
        # Cocoa origin (0,0) bottom-left; pyautogui origin top-left
        sx = int(round(wframe.origin.x + lx))
        sy_cocoa = wframe.origin.y + ly
        py_y = int(round(sframe.size.height - sy_cocoa))
        return sx, py_y


