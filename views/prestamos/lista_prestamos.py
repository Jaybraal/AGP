"""Loan list screen — PyQt6."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QComboBox,
)
from controllers.prestamo_controller import listar, buscar
from views.components.tabla import Tabla
from views.components.search_bar import SearchBar
from views.components.worker import Worker

COLUMNAS = [
    ("numero_prestamo",   "Número",        130),
    ("nombres",           "Cliente",       180),
    ("monto_principal",   "Capital",        90),
    ("saldo_capital",     "Saldo",          90),
    ("cuota_base",        "Cuota",          90),
    ("frecuencia_pago",   "Frecuencia",     90),
    ("fecha_vencimiento", "Vencimiento",   110),
    ("estado",            "Estado",         90),
]

ESTADOS = ["Todos", "ACTIVO", "AL_DIA", "VENCIDO", "CANCELADO"]


class ListaPrestamos(QWidget):

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

        lbl_title = QLabel("Préstamos")
        lbl_title.setObjectName("title")
        ll.addWidget(lbl_title)

        self._lbl_count = QLabel("")
        self._lbl_count.setObjectName("subtitle")
        ll.addWidget(self._lbl_count)

        hdr_layout.addWidget(left, 1)

        btn_nuevo = QPushButton("➕  Nuevo Préstamo")
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
            placeholder="Buscar por número, nombre, cédula...",
            on_search=self._buscar,
        )
        tb_layout.addWidget(self._search)

        lbl_estado = QLabel("Estado:")
        lbl_estado.setObjectName("dim")
        tb_layout.addWidget(lbl_estado)

        self._cb_estado = QComboBox()
        self._cb_estado.addItems(ESTADOS)
        self._cb_estado.setFixedWidth(140)
        self._cb_estado.currentTextChanged.connect(lambda _: self.refrescar())
        tb_layout.addWidget(self._cb_estado)

        tb_layout.addStretch()

        btn_detalle = QPushButton("📋  Ver Detalle")
        btn_detalle.setObjectName("btn_secondary")
        btn_detalle.setFixedHeight(38)
        btn_detalle.clicked.connect(self._ver_detalle)
        tb_layout.addWidget(btn_detalle)

        btn_cobrar = QPushButton("💵  Cobrar")
        btn_cobrar.setObjectName("btn_success")
        btn_cobrar.setFixedHeight(38)
        btn_cobrar.clicked.connect(lambda: self._navegar("caja") if self._navegar else None)
        tb_layout.addWidget(btn_cobrar)

        layout.addWidget(toolbar)

        # ── Table ──────────────────────────────────────────────
        self._tabla = Tabla(columnas=COLUMNAS)
        layout.addWidget(self._tabla, 1)

    # ── Threading ───────────────────────────────────────────────────────

    def refrescar(self):
        self._lbl_count.setText("Cargando...")
        estado = self._cb_estado.currentText()
        fn = listar if estado == "Todos" else lambda: listar(estado=estado)
        self._worker = Worker(fn)
        self._worker.result.connect(self._mostrar)
        self._worker.start()

    def _mostrar(self, datos: list):
        self._tabla.cargar(datos)
        n = len(datos)
        self._lbl_count.setText(
            f"{n} préstamo{'s' if n != 1 else ''} encontrado{'s' if n != 1 else ''}"
        )

    def _buscar(self, termino: str):
        if termino.strip():
            self._worker = Worker(buscar, termino)
        else:
            self._worker = Worker(listar)
        self._worker.result.connect(self._mostrar)
        self._worker.start()

    # ── Callbacks ───────────────────────────────────────────────────────

    def _nuevo(self):
        from views.prestamos.form_prestamo import FormPrestamo
        dlg = FormPrestamo(on_guardado=self.refrescar, parent=self)
        dlg.exec()

    def _ver_detalle(self):
        sel = self._tabla.seleccionado()
        if not sel:
            return
        from views.prestamos.detalle_prestamo import DetallePrestamo
        dlg = DetallePrestamo(prestamo_id=sel["id"], parent=self)
        dlg.exec()
