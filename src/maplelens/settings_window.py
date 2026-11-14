"""The Settings window: what the player sets once, in one scrolling page of sections.

The app builds General; each tool builds its own section (`settings_section()`), so no tool
knows about another. Every control applies and saves the moment it changes: no OK button.
Only mouse controls: the window never takes the keyboard from the game.
"""

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from maplelens.overlay import FloatingWindow, setting_box

TITLE = "MapleLens — Settings"
AUTO_UPDATES = "Check for updates automatically"
CHECK_NOW = "Check now"


class GeneralSection(QWidget):
    """The app's own settings, which belong to no tool."""

    def __init__(self):
        super().__init__()
        self._rows = QVBoxLayout(self)
        self._rows.setContentsMargins(0, 0, 0, 0)

    def add_tool_switches(
        self, labels: list[str], states: list[bool], on_change: Callable[[int, bool], None]
    ) -> None:
        """A checkbox per tool, in the tabs' order; `on_change` gets its index and state.
        The last one still on can't be turned off: a box with no tabs shows nothing."""
        self._switches = [
            setting_box(t, on, lambda _: None) for t, on in zip(labels, states, strict=True)
        ]
        for i, box in enumerate(self._switches):
            box.toggled.connect(lambda on, i=i: self._switched(i, on, on_change))
            self._rows.addWidget(box)
        self._guard_last()

    def _switched(self, i: int, on: bool, on_change: Callable[[int, bool], None]) -> None:
        self._guard_last()
        on_change(i, on)

    def _guard_last(self) -> None:
        checked = [b for b in self._switches if b.isChecked()]
        for b in self._switches:
            b.setEnabled(not (len(checked) == 1 and b.isChecked()))

    def add_updates(
        self, auto: bool, set_auto: Callable[[bool], None], check_now: Callable[[], None]
    ) -> None:
        """The automatic update check's checkbox, and a button that checks now (its answer
        shows in the box's notice line). Only the installed app has an update check."""
        row = QHBoxLayout()
        row.addWidget(setting_box(AUTO_UPDATES, auto, set_auto))
        row.addStretch()
        button = QPushButton(CHECK_NOW)
        button.setFocusPolicy(Qt.NoFocus)
        button.clicked.connect(check_now)
        row.addWidget(button)
        self._rows.addLayout(row)


def sections(general: QWidget, tools: list) -> list[tuple[str, QWidget]]:
    """General, then each tool's own section under its tab's name, for tools that have one."""
    out = [("General", general)]
    out += [(t.title, t.settings_section()) for t in tools if hasattr(t, "settings_section")]
    return out


class SettingsWindow(FloatingWindow):
    """One page of (heading, section) pairs, in the order given."""

    def __init__(self, sections: list[tuple[str, QWidget]]):
        super().__init__()
        self.setWindowTitle(TITLE)
        page = QWidget()
        column = QVBoxLayout(page)
        self._sections: dict[str, tuple[QLabel, QWidget]] = {}
        for title, widget in sections:
            head = QLabel(title)
            head.setObjectName("section")
            font = head.font()
            font.setBold(True)
            font.setPointSize(font.pointSize() + 1)
            head.setFont(QFont(font))
            column.addWidget(head)
            column.addWidget(widget)
            column.addSpacing(12)
            self._sections[title] = (head, widget)
        column.addStretch()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(page)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)
        self.resize(380, 460)

    def set_section_enabled(self, title: str, on: bool) -> None:
        """Grey out a section (its tool is off), or bring it back; a missing one is fine."""
        for part in self._sections.get(title, ()):
            part.setEnabled(on)
