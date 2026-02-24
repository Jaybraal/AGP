"""Left navigation sidebar — PyQt6."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
)
from PyQt6.QtCore import Qt
from config import APP_VERSION

MENU_ITEMS = [
    ("🏠", "Inicio",        "dashboard"),
    ("👤", "Clientes",      "clientes"),
    ("📋", "Préstamos",     "prestamos"),
    ("💵", "Caja",          "caja"),
    ("📊", "Reportes",      "reportes"),
    ("⚙",  "Configuración", "config"),
]

_SIDEBAR_BG      = "#1E3A8A"
_BTN_ACTIVE_BG   = "#2563EB"
_BTN_HOVER_BG    = "#1E40AF"
_TEXT_IDLE       = "#BFDBFE"
_TEXT_ACTIVE     = "#FFFFFF"
_SEPARATOR       = "#2D4B9A"


class Sidebar(QWidget):

    def __init__(self, parent=None, on_navigate=None):
        super().__init__(parent)
        self._on_navigate = on_navigate
        self._buttons: dict[str, QPushButton] = {}
        self._activo: str | None = None
        self.setFixedWidth(230)
        self.setObjectName("sidebar")
        self.setStyleSheet(f"""
            #sidebar {{
                background: {_SIDEBAR_BG};
            }}
            #sidebar QPushButton {{
                background: transparent;
                color: {_TEXT_IDLE};
                border: none;
                border-radius: 10px;
                padding: 12px 16px;
                font-size: 13px;
                text-align: left;
            }}
            #sidebar QPushButton:hover {{
                background: {_BTN_HOVER_BG};
            }}
            #sidebar QPushButton[active=true] {{
                background: {_BTN_ACTIVE_BG};
                color: {_TEXT_ACTIVE};
                font-weight: bold;
            }}
        """)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Logo header ────────────────────────────────────────
        header = QWidget()
        header.setStyleSheet("background: transparent;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(20, 24, 20, 16)
        h_layout.setSpacing(12)

        logo_box = QLabel("A")
        logo_box.setFixedSize(44, 44)
        logo_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_box.setStyleSheet(
            "background: #2563EB; border-radius: 10px;"
            "color: white; font-size: 22px; font-weight: bold;"
        )
        h_layout.addWidget(logo_box)

        title_col = QWidget()
        title_col.setStyleSheet("background: transparent;")
        tc_layout = QVBoxLayout(title_col)
        tc_layout.setContentsMargins(0, 0, 0, 0)
        tc_layout.setSpacing(2)

        lbl_agp = QLabel("AGP")
        lbl_agp.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        tc_layout.addWidget(lbl_agp)

        lbl_sub = QLabel("Gestión de Préstamos")
        lbl_sub.setStyleSheet(f"color: {_TEXT_IDLE}; font-size: 9px;")
        tc_layout.addWidget(lbl_sub)

        h_layout.addWidget(title_col, 1)
        layout.addWidget(header)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {_SEPARATOR}; background: {_SEPARATOR}; height: 1px;")
        sep.setFixedHeight(1)
        layout.addWidget(sep)

        # Section label
        sec_lbl = QLabel("  NAVEGACIÓN")
        sec_lbl.setStyleSheet(f"color: {_TEXT_IDLE}; font-size: 9px; font-weight: bold;"
                               "background: transparent; padding: 8px 16px 4px 16px;")
        layout.addWidget(sec_lbl)

        # ── Nav buttons ────────────────────────────────────────
        nav = QWidget()
        nav.setStyleSheet("background: transparent;")
        nav_layout = QVBoxLayout(nav)
        nav_layout.setContentsMargins(10, 0, 10, 0)
        nav_layout.setSpacing(2)

        for icon, label, key in MENU_ITEMS:
            btn = QPushButton(f"  {icon}   {label}")
            btn.setProperty("active", False)
            btn.clicked.connect(lambda checked=False, k=key: self._navegar(k))
            nav_layout.addWidget(btn)
            self._buttons[key] = btn

        nav_layout.addStretch()
        layout.addWidget(nav, 1)

        # ── Bottom version ─────────────────────────────────────
        bottom = QWidget()
        bottom.setStyleSheet("background: transparent;")
        b_layout = QVBoxLayout(bottom)
        b_layout.setContentsMargins(16, 0, 16, 16)
        b_layout.setSpacing(8)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet(f"color: {_SEPARATOR}; background: {_SEPARATOR};")
        sep2.setFixedHeight(1)
        b_layout.addWidget(sep2)

        status_row = QWidget()
        sr_layout = QHBoxLayout(status_row)
        sr_layout.setContentsMargins(0, 0, 0, 0)
        sr_layout.setSpacing(4)

        dot = QLabel("●")
        dot.setStyleSheet("color: #4ADE80; font-size: 10px; background: transparent;")
        sr_layout.addWidget(dot)

        ver = QLabel(f"Sistema v{APP_VERSION}")
        ver.setStyleSheet(f"color: {_TEXT_IDLE}; font-size: 9px; background: transparent;")
        sr_layout.addWidget(ver)
        sr_layout.addStretch()

        b_layout.addWidget(status_row)
        layout.addWidget(bottom)

    # ── Public ──────────────────────────────────────────────────────────

    def _navegar(self, key: str):
        self._marcar(key)
        if self._on_navigate:
            self._on_navigate(key)

    def _marcar(self, key: str):
        if self._activo and self._activo in self._buttons:
            self._buttons[self._activo].setProperty("active", False)
            self._buttons[self._activo].style().unpolish(self._buttons[self._activo])
            self._buttons[self._activo].style().polish(self._buttons[self._activo])
        if key in self._buttons:
            self._buttons[key].setProperty("active", True)
            self._buttons[key].style().unpolish(self._buttons[key])
            self._buttons[key].style().polish(self._buttons[key])
        self._activo = key

    def marcar(self, key: str):
        self._marcar(key)
