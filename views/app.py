"""Root application window — PyQt6 QMainWindow with sidebar + stacked content."""

import time
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QStackedWidget, QFrame,
)
from config import APP_TITLE, APP_WIDTH, APP_HEIGHT, APP_MIN_W, APP_MIN_H
from views.sidebar import Sidebar


class App(QMainWindow):

    _REFRESH_TTL = 4   # seconds between auto-refreshes of the same view

    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(APP_WIDTH, APP_HEIGHT)
        self.setMinimumSize(APP_MIN_W, APP_MIN_H)

        self._frames: dict[str, QWidget] = {}
        self._frame_actual: QWidget | None = None
        self._last_refresh: dict[str, float] = {}

        self._build()
        self._navegar("dashboard")

    def _build(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.sidebar = Sidebar(on_navigate=self._navegar)
        main_layout.addWidget(self.sidebar)

        # Thin separator line
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFixedWidth(1)
        sep.setStyleSheet("color: #E2E8F0; background: #E2E8F0;")
        main_layout.addWidget(sep)

        self._stack = QStackedWidget()
        main_layout.addWidget(self._stack, 1)

    # ── Navigation ──────────────────────────────────────────────────────

    def _navegar(self, key: str):
        self.sidebar.marcar(key)

        if key not in self._frames:
            frame = self._crear_frame(key)
            self._frames[key] = frame
            self._stack.addWidget(frame)

        frame = self._frames[key]
        self._stack.setCurrentWidget(frame)
        self._frame_actual = frame

        if hasattr(frame, "refrescar"):
            now   = time.monotonic()
            since = now - self._last_refresh.get(key, 0)
            if since >= self._REFRESH_TTL:
                self._last_refresh[key] = now
                frame.refrescar()

    def _crear_frame(self, key: str) -> QWidget:
        if key == "dashboard":
            from views.dashboard import Dashboard
            return Dashboard(navegar=self._navegar)
        elif key == "clientes":
            from views.clientes.lista_clientes import ListaClientes
            return ListaClientes(navegar=self._navegar)
        elif key == "prestamos":
            from views.prestamos.lista_prestamos import ListaPrestamos
            return ListaPrestamos(navegar=self._navegar)
        elif key == "caja":
            from views.caja.caja_main import CajaMain
            return CajaMain(navegar=self._navegar)
        elif key == "reportes":
            from views.reportes.reportes_main import ReportesMain
            return ReportesMain(navegar=self._navegar)
        elif key == "config":
            from views.configuracion import Configuracion
            return Configuracion(navegar=self._navegar)
        else:
            w = QWidget()
            from PyQt6.QtWidgets import QLabel, QVBoxLayout
            from PyQt6.QtCore import Qt
            lbl = QLabel(f"Módulo: {key}")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            QVBoxLayout(w).addWidget(lbl)
            return w

    # ── Public helpers (called by child views) ──────────────────────────

    def navegar_a(self, key: str, **kwargs):
        self._last_refresh[key] = 0
        self._navegar(key)
        if self._frame_actual and hasattr(self._frame_actual, "set_params"):
            self._frame_actual.set_params(**kwargs)

    def invalidar(self, *keys: str):
        for k in keys:
            self._last_refresh[k] = 0
