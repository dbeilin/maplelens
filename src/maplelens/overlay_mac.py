"""macOS: MapleLens's own windows float over the game without taking the keyboard from it."""

import objc
from AppKit import (
    NSApplication,
    NSApplicationActivationPolicyAccessory,
    NSEvent,
    NSEventMaskMouseEntered,
    NSEventMaskMouseExited,
    NSEventMaskMouseMoved,
    NSEventTypeMouseEntered,
    NSEventTypeMouseExited,
    NSEventTypeMouseMoved,
    NSPanel,
    NSPopUpMenuWindowLevel,
    NSWindowStyleMaskNonactivatingPanel,
)
from PySide6.QtCore import QCoreApplication, QEvent, QPoint, QPointF, Qt
from PySide6.QtGui import QCursor, QEnterEvent, QGuiApplication, QMouseEvent, QWindow
from PySide6.QtWidgets import QWidget

_monitors: list = []  # kept: macOS drops a monitor once nothing holds it


def _ns_window(win_id: int):
    return objc.objc_object(c_void_p=win_id).window()  # a winId is an NSView


def make_panel(widget: QWidget) -> None:
    """Keep the widget's window visible while the game is active, and out of the keyboard."""
    window = _ns_window(int(widget.winId()))
    if window is None:
        return
    if isinstance(window, NSPanel):
        window.setStyleMask_(window.styleMask() | NSWindowStyleMaskNonactivatingPanel)
        window.setBecomesKeyOnlyIfNeeded_(True)  # clicks and drags leave the keyboard alone
    window.setHidesOnDeactivate_(False)
    # The game lifts its window to level 26 while it's active; stay above it, below menus.
    window.setLevel_(NSPopUpMenuWindowLevel - 1)


def make_accessory() -> None:
    """No Dock icon or app menu, also for a plain python process (run from source).

    Only the policy: it never brings MapleLens or any other app to the front.
    """
    NSApplication.sharedApplication().setActivationPolicy_(NSApplicationActivationPolicyAccessory)


def hover(window: QWindow, kind: QEvent.Type, at: QPoint | None = None) -> None:
    """The pointer entered `window`, moved in it (to the global point `at`) or left it: Enter,
    MouseMove or Leave. Qt's widget side turns them into the rows' enter and leave."""
    if kind == QEvent.Leave:
        QCoreApplication.sendEvent(window, QEvent(QEvent.Leave))
        return
    where = QPointF(at)
    local = window.mapFromGlobal(where)
    if kind == QEvent.Enter:
        event = QEnterEvent(local, local, where)
    else:
        event = QMouseEvent(kind, local, where, Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    QCoreApplication.sendEvent(window, event)


def forward_hover() -> None:
    """Hover while the game is in front. Qt drops the pointer's moves, enters and exits
    whenever MapleLens isn't the active app, which it never is during play, though macOS
    still hands them to the app: pass them on to the window ourselves. Only the app's own
    events, as they arrive; while it's active Qt has them already."""
    kinds = {
        NSEventTypeMouseEntered: QEvent.Enter,
        NSEventTypeMouseMoved: QEvent.MouseMove,
        NSEventTypeMouseExited: QEvent.Leave,
    }

    def seen(event):
        if not NSApplication.sharedApplication().isActive():
            number = event.windowNumber()
            for window in QGuiApplication.topLevelWindows():
                if window.isVisible() and _ns_window(int(window.winId())).windowNumber() == number:
                    hover(window, kinds[event.type()], QCursor.pos())
                    break
        return event

    mask = NSEventMaskMouseEntered | NSEventMaskMouseMoved | NSEventMaskMouseExited
    _monitors.append(NSEvent.addLocalMonitorForEventsMatchingMask_handler_(mask, seen))


def release_keyboard() -> None:
    """Step back if typing made MapleLens the active app; macOS hands the keyboard back."""
    app = NSApplication.sharedApplication()
    if app.isActive():
        app.deactivate()  # activation returns to the previous app; nothing touches the game
