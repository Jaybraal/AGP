"""Reusable search bar with debounce — PyQt6."""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton, QLabel
from PyQt6.QtCore import QTimer


class SearchBar(QWidget):
    """
    Search bar that fires on_search(text) after debounce_ms ms of inactivity.
    """

    def __init__(self, parent=None, placeholder: str = "Buscar...",
                 on_search=None, debounce_ms: int = 300):
        super().__init__(parent)
        self._on_search  = on_search
        self._debounce   = debounce_ms
        self._timer      = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._fire)
        self._build(placeholder)

    def _build(self, placeholder: str):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        icon = QLabel("🔍")
        layout.addWidget(icon)

        self._entry = QLineEdit()
        self._entry.setPlaceholderText(placeholder)
        self._entry.setFixedHeight(38)
        self._entry.setMinimumWidth(300)
        self._entry.textChanged.connect(self._on_change)
        layout.addWidget(self._entry)

        btn_clear = QPushButton("✕")
        btn_clear.setFixedSize(30, 30)
        btn_clear.setObjectName("btn_secondary")
        btn_clear.clicked.connect(self.limpiar)
        layout.addWidget(btn_clear)

    def _on_change(self, _text: str):
        self._timer.stop()
        self._timer.start(self._debounce)

    def _fire(self):
        if self._on_search:
            self._on_search(self._entry.text())

    def limpiar(self):
        self._entry.clear()
        if self._on_search:
            self._on_search("")

    def valor(self) -> str:
        return self._entry.text()
