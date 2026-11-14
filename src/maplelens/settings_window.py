"""The Settings window: what the player sets once, in one scrolling page of sections.

The app builds General; each tool builds its own section (`settings_section()`), so no tool
knows about another. Every control applies and saves the moment it changes: no OK button.
Only mouse controls: the window never takes the keyboard from the game.
"""

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLabel, QScrollArea, QVBoxLayout, QWidget

from maplelens.overlay import FloatingWindow

TITLE = "MapleLens — Settings"


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
