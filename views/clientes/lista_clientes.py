"""Client list screen — PyQt6."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
)
from controllers.cliente_controller import buscar, todos
from views.components.tabla import Tabla
from views.components.search_bar import SearchBar
from views.components.worker import Worker

COLUMNAS = [
    ("cedula",             "Cédula / Doc.",     130),
    ("nombres",            "Nombres",           160),
    ("apellidos",          "Apellidos",         160),
    ("telefono_principal", "Teléfono",          120),
    ("ciudad",             "Ciudad",             90),
    ("calificacion",       "Calific.",            80),
]


class ListaClientes(QWidget):

    def __init__(self, navegar=None, parent=None):
        super().__init__(parent)
        self._navegar = navegar
        self._worker: Worker | None = None
        self._build()
        self.refrescar()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 16)
        layout.setSpacing(0)

        # ── Header ─────────────────────────────────────────────
        hdr = QWidget()
        hdr.setStyleSheet("background: transparent;")
        hdr_layout = QHBoxLayout(hdr)
        hdr_layout.setContentsMargins(0, 0, 0, 8)

        left = QWidget()
        left.setStyleSheet("background: transparent;")
        ll = QVBoxLayout(left)
        ll.setContentsMargins(0, 0, 0, 0)
        ll.setSpacing(2)

        lbl_title = QLabel("Clientes")
        lbl_title.setObjectName("title")
        ll.addWidget(lbl_title)

        self._lbl_count = QLabel("")
        self._lbl_count.setObjectName("subtitle")
        ll.addWidget(self._lbl_count)

        hdr_layout.addWidget(left, 1)

        btn_nuevo = QPushButton("➕  Nuevo Cliente")
        btn_nuevo.setFixedHeight(42)
        btn_nuevo.clicked.connect(self._nuevo)
        hdr_layout.addWidget(btn_nuevo)

        layout.addWidget(hdr)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #E2E8F0;")
        layout.addWidget(sep)
        layout.addSpacing(14)

        # ── Toolbar ────────────────────────────────────────────
        toolbar = QWidget()
        toolbar.setStyleSheet("background: transparent;")
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(0, 0, 0, 10)
        tb_layout.setSpacing(6)

        self._search = SearchBar(
            placeholder="Buscar por nombre, cédula o teléfono...",
            on_search=self._buscar,
            debounce_ms=300,
        )
        tb_layout.addWidget(self._search)
        tb_layout.addStretch()

        btn_editar = QPushButton("✏️  Editar")
        btn_editar.setObjectName("btn_secondary")
        btn_editar.setFixedHeight(38)
        btn_editar.clicked.connect(self._editar)
        tb_layout.addWidget(btn_editar)

        btn_perfil = QPushButton("👤  Ver Perfil")
        btn_perfil.setFixedHeight(38)
        btn_perfil.clicked.connect(self._ver_perfil)
        tb_layout.addWidget(btn_perfil)

        layout.addWidget(toolbar)

        # ── Table ──────────────────────────────────────────────
        self._tabla = Tabla(columnas=COLUMNAS, on_select=self._on_select)
        layout.addWidget(self._tabla, 1)

    # ── Threading ───────────────────────────────────────────────────────

    def refrescar(self):
        self._lbl_count.setText("Cargando...")
        self._worker = Worker(todos)
        self._worker.result.connect(self._mostrar)
        self._worker.start()

    def _mostrar(self, datos: list):
        self._tabla.cargar(datos)
        n = len(datos)
        self._lbl_count.setText(
            f"{n} cliente{'s' if n != 1 else ''} encontrado{'s' if n != 1 else ''}"
        )

    def _buscar(self, termino: str):
        if termino.strip():
            self._worker = Worker(buscar, termino)
        else:
            self._worker = Worker(todos)
        self._worker.result.connect(self._mostrar)
        self._worker.start()

    # ── Callbacks ───────────────────────────────────────────────────────

    def _on_select(self, row: dict):
        pass

    def _nuevo(self):
        from views.clientes.form_cliente import FormCliente
        dlg = FormCliente(on_guardado=self.refrescar, parent=self)
        dlg.exec()

    def _ver_perfil(self):
        sel = self._tabla.seleccionado()
        if not sel:
            return
        from views.clientes.perfil_cliente import PerfilCliente
        dlg = PerfilCliente(cliente_id=sel["id"], navegar=self._navegar, parent=self)
        dlg.exec()

    def _editar(self):
        sel = self._tabla.seleccionado()
        if not sel:
            return
        from views.clientes.form_cliente import FormCliente
        dlg = FormCliente(cliente_id=sel["id"], on_guardado=self.refrescar, parent=self)
        dlg.exec()
