import sys

import pytest


@pytest.fixture
def qt(monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])


def _titles(win):
    from PySide6.QtWidgets import QLabel

    return [w.text() for w in win.findChildren(QLabel) if w.objectName() == "section"]


def test_the_window_stacks_its_sections_under_their_headings(qt):
    from PySide6.QtWidgets import QLabel

    from maplelens.settings_window import TITLE, SettingsWindow

    win = SettingsWindow([("General", QLabel("g")), ("Path", QLabel("p"))])
    assert win.windowTitle() == TITLE == "MapleLens — Settings"
    assert _titles(win) == ["General", "Path"]


def test_the_window_floats_over_the_game_without_taking_focus(qt):
    from PySide6.QtCore import Qt

    from maplelens.settings_window import SettingsWindow

    win = SettingsWindow([])
    assert win.windowType() == Qt.Tool
    assert win.testAttribute(Qt.WA_ShowWithoutActivating)
    assert not win.testAttribute(Qt.WA_QuitOnClose)
    if sys.platform != "darwin":  # the Mac's panel does this itself, in native_setup
        assert win.windowFlags() & Qt.WindowStaysOnTopHint
        assert win.windowFlags() & Qt.WindowDoesNotAcceptFocus


def test_opening_twice_gives_one_window(qt):
    from maplelens import app
    from maplelens.overlay import Box
    from maplelens.settings_window import SettingsWindow

    box = Box("t", {}, lambda: None)
    box.add_menu_item("Quit MapleLens", lambda: None)
    win = SettingsWindow([])
    app.add_settings(box, win)
    (item,) = [a for a in box.actions() if a.text() == "Settings…"]
    item.trigger()
    item.trigger()
    assert win.isVisible()
    assert [w for w in qt.topLevelWidgets() if isinstance(w, SettingsWindow) and w.isVisible()] == [
        win
    ]
    win.close()


def test_settings_comes_just_before_hide(qt):
    from maplelens import app
    from maplelens.overlay import Box
    from maplelens.settings_window import SettingsWindow

    class Tray:
        def __init__(self):
            self.activated = type("S", (), {"connect": lambda *_: None})()

    box = Box("t", {}, lambda: None)
    box.add_menu_item("Quit MapleLens", lambda: None)
    app.add_settings(box, SettingsWindow([]))
    app.add_hide(box, app.Layer(), Tray())
    app.add_about(box, None)
    assert [a.text() for a in box.actions()] == [
        "Settings…",
        "Hide MapleLens",
        "About MapleLens",
        "Quit MapleLens",
    ]


def test_closing_settings_does_not_quit(qt):
    from PySide6.QtCore import QTimer

    from maplelens.settings_window import SettingsWindow

    win = SettingsWindow([])
    win.open()
    survived = []
    QTimer.singleShot(0, win.close)
    QTimer.singleShot(200, lambda: survived.append(1))
    QTimer.singleShot(300, qt.quit)  # exec() must still be running at 200 ms
    qt.exec()
    assert survived == [1]


def test_a_click_reaches_a_control_in_the_window(qt):
    from PySide6.QtCore import QPoint, Qt
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QCheckBox

    from maplelens.settings_window import SettingsWindow

    box = QCheckBox("on")
    win = SettingsWindow([("General", box)])
    win.open()
    # on the box itself: a checkbox stretched across the page ignores its empty middle
    QTest.mouseClick(box, Qt.LeftButton, pos=QPoint(6, box.height() // 2))
    assert box.isChecked()
    win.close()
