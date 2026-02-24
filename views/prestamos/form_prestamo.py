"""New loan form with live amortization preview — PyQt6."""

from datetime import date
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QTextEdit, QScrollArea, QWidget,
    QFrame, QSplitter,
)
from PyQt6.QtCore import Qt, QTimer

from config import FRECUENCIAS, TIPOS_TASA, TIPOS_AMORT
from controllers.cliente_controller import buscar as buscar_clientes, todos
from controllers.prestamo_controller import previsualizar, crear
from views.components.tabla import Tabla
from views.components.worker import Worker

COLUMNAS_TABLA = [
    ("numero_cuota",      "#",         40),
    ("fecha_vencimiento", "Fecha",    110),
    ("cuota_total",       "Cuota",     90),
    ("capital",           "Capital",   90),
    ("intereses",         "Intereses", 90),
    ("saldo_restante",    "Saldo",     90),
]


class FormPrestamo(QDialog):

    def __init__(self, on_guardado=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nuevo Préstamo")
        self.resize(980, 780)
        self.setModal(True)

        self._on_guardado            = on_guardado
        self._cliente_seleccionado   = None
        self._resultado              = None
        self._worker: Worker | None  = None
        self._search_timer           = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._ejecutar_busqueda_cliente)

        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(8)

        # ── Splitter: left form | right preview ────────────────
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # LEFT
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setFrameShape(QFrame.Shape.NoFrame)
        left_inner = QWidget()
        left_inner.setObjectName("card")
        self._form_layout = QVBoxLayout(left_inner)
        self._form_layout.setContentsMargins(16, 12, 16, 12)
        self._form_layout.setSpacing(4)
        left_scroll.setWidget(left_inner)
        splitter.addWidget(left_scroll)

        # RIGHT
        right = QFrame()
        right.setObjectName("card")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_layout.setSpacing(8)
        self._build_preview(right_layout)
        splitter.addWidget(right)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        root.addWidget(splitter, 1)

        # ── Build form fields ──────────────────────────────────
        self._v: dict[str, QWidget] = {}
        self._build_form()

        # ── Bottom buttons ─────────────────────────────────────
        btn_bar = QWidget()
        btn_bar.setStyleSheet("background: transparent;")
        bl = QHBoxLayout(btn_bar)
        bl.setContentsMargins(0, 0, 0, 0)
        bl.setSpacing(8)

        self._lbl_error = QLabel("")
        self._lbl_error.setStyleSheet("color: #DC2626;")
        bl.addWidget(self._lbl_error, 1)

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("btn_secondary")
        btn_cancel.clicked.connect(self.reject)
        bl.addWidget(btn_cancel)

        btn_save = QPushButton("💾  Guardar Préstamo")
        btn_save.clicked.connect(self._guardar)
        bl.addWidget(btn_save)

        btn_calc = QPushButton("🔢  Calcular")
        btn_calc.setObjectName("btn_success")
        btn_calc.clicked.connect(self._calcular)
        bl.addWidget(btn_calc)

        root.addWidget(btn_bar)

    def _build_form(self):
        fl = self._form_layout

        def sec(t: str):
            lbl = QLabel(t)
            lbl.setObjectName("section")
            fl.addSpacing(8)
            fl.addWidget(lbl)

        def row(label: str, key: str, widget: QWidget):
            r = QWidget()
            r.setStyleSheet("background: transparent;")
            rl = QHBoxLayout(r)
            rl.setContentsMargins(0, 2, 0, 2)
            rl.setSpacing(8)
            lbl = QLabel(label)
            lbl.setFixedWidth(160)
            lbl.setObjectName("dim")
            rl.addWidget(lbl)
            rl.addWidget(widget, 1)
            fl.addWidget(r)
            self._v[key] = widget

        # ── Cliente ────────────────────────────────────────────
        sec("Cliente")

        self._lbl_cliente = QLabel("Ninguno seleccionado")
        self._lbl_cliente.setStyleSheet(
            "background: #F1F5F9; border-radius: 6px; color: #64748B;"
            "padding: 6px 10px;"
        )
        fl.addWidget(self._lbl_cliente)

        self._entry_search = QLineEdit()
        self._entry_search.setPlaceholderText("Buscar cliente...")
        self._entry_search.setFixedHeight(32)
        self._entry_search.textChanged.connect(self._buscar_cliente)
        fl.addWidget(self._entry_search)

        self._lista_clientes = QWidget()
        self._lista_clientes.setStyleSheet("background: #F8FAFC; border-radius: 6px;")
        self._lista_clientes_layout = QVBoxLayout(self._lista_clientes)
        self._lista_clientes_layout.setContentsMargins(4, 4, 4, 4)
        self._lista_clientes_layout.setSpacing(2)
        fl.addWidget(self._lista_clientes)

        # ── Parámetros ─────────────────────────────────────────
        sec("Parámetros del Préstamo")

        entry_monto = QLineEdit()
        entry_monto.setFixedHeight(32)
        row("Monto*", "monto", entry_monto)

        entry_tasa = QLineEdit()
        entry_tasa.setFixedHeight(32)
        row("Tasa de Interés (%)*", "tasa", entry_tasa)

        cb_tipo_tasa = QComboBox()
        cb_tipo_tasa.addItems(TIPOS_TASA)
        cb_tipo_tasa.setCurrentText("MENSUAL")
        row("Tipo de Tasa", "tipo_tasa", cb_tipo_tasa)

        entry_plazo = QLineEdit()
        entry_plazo.setFixedHeight(32)
        row("Plazo (períodos)*", "plazo", entry_plazo)

        cb_frecuencia = QComboBox()
        cb_frecuencia.addItems(FRECUENCIAS)
        cb_frecuencia.setCurrentText("MENSUAL")
        row("Frecuencia de Pago", "frecuencia_pago", cb_frecuencia)

        cb_amort = QComboBox()
        cb_amort.addItems(TIPOS_AMORT)
        cb_amort.setCurrentText("FRANCES")
        row("Tipo Amortización", "tipo_amortizacion", cb_amort)

        entry_fecha = QLineEdit(date.today().isoformat())
        entry_fecha.setFixedHeight(32)
        row("Fecha Inicio (YYYY-MM-DD)*", "fecha_inicio", entry_fecha)

        sec("Notas")
        self._notas = QTextEdit()
        self._notas.setFixedHeight(60)
        fl.addWidget(self._notas)
        fl.addStretch()

    def _build_preview(self, layout: QVBoxLayout):
        lbl = QLabel("Tabla de Amortización")
        lbl.setObjectName("section")
        layout.addWidget(lbl)

        summary = QWidget()
        summary.setStyleSheet("background: transparent;")
        sl = QHBoxLayout(summary)
        sl.setContentsMargins(0, 0, 0, 0)
        sl.setSpacing(12)

        self._lbl_cuota     = QLabel("Cuota: —")
        self._lbl_total     = QLabel("Total: —")
        self._lbl_intereses = QLabel("Intereses: —")
        for w in (self._lbl_cuota, self._lbl_total, self._lbl_intereses):
            sl.addWidget(w)
        sl.addStretch()

        layout.addWidget(summary)

        self._tabla_preview = Tabla(columnas=COLUMNAS_TABLA)
        layout.addWidget(self._tabla_preview, 1)

    # ── Client search ────────────────────────────────────────────────────

    def _buscar_cliente(self, _text: str):
        self._search_timer.stop()
        self._search_timer.start(250)

    def _ejecutar_busqueda_cliente(self):
        termino = self._entry_search.text().strip()
        fn = (lambda: buscar_clientes(termino)) if termino else (lambda: todos()[:20])
        self._worker = Worker(fn)
        self._worker.result.connect(lambda r: self._mostrar_clientes(r[:15]))
        self._worker.start()

    def _mostrar_clientes(self, resultados: list):
        # Clear existing
        for i in reversed(range(self._lista_clientes_layout.count())):
            w = self._lista_clientes_layout.itemAt(i).widget()
            if w:
                w.deleteLater()

        for c in resultados:
            nombre = f"{c['nombres']} {c['apellidos']}  ({c['cedula']})"
            btn = QPushButton(nombre)
            btn.setObjectName("btn_secondary")
            btn.setFixedHeight(28)
            btn.clicked.connect(lambda ch=False, cli=c: self._seleccionar_cliente(cli))
            self._lista_clientes_layout.addWidget(btn)

    def _seleccionar_cliente(self, cliente: dict):
        self._cliente_seleccionado = cliente
        tasa = cliente.get("tasa_sugerida") or 0
        tipo = cliente.get("tipo_tasa_sugerida") or "MENSUAL"
        text = f"✅  {cliente['nombres']} {cliente['apellidos']}  —  {cliente['cedula']}"
        if tasa and float(tasa) > 0:
            text += f"  |  Tasa sugerida: {tasa}% {tipo}"
            self._set_widget_value(self._v["tasa"], str(tasa))
            self._set_widget_value(self._v["tipo_tasa"], tipo)
        self._lbl_cliente.setText(text)
        for i in reversed(range(self._lista_clientes_layout.count())):
            w = self._lista_clientes_layout.itemAt(i).widget()
            if w:
                w.deleteLater()
        self._entry_search.clear()

    # ── Calculate ────────────────────────────────────────────────────────

    def _calcular(self):
        self._lbl_error.setText("")
        self._lbl_cuota.setText("Calculando...")
        self._lbl_total.setText("")
        self._lbl_intereses.setText("")
        datos = self._get_form_data()
        self._worker = Worker(previsualizar, datos)
        self._worker.result.connect(self._mostrar_calculo)
        self._worker.error.connect(lambda msg: self._lbl_error.setText(msg))
        self._worker.start()

    def _mostrar_calculo(self, resultado: dict):
        self._resultado = resultado
        moneda = "RD$"
        self._lbl_cuota.setText(f"Cuota: {moneda} {resultado['cuota_base']:,.2f}")
        self._lbl_total.setText(f"Total: {moneda} {resultado['total_a_pagar']:,.2f}")
        self._lbl_intereses.setText(f"Intereses: {moneda} {resultado['total_intereses']:,.2f}")
        tabla_dicts = [
            {
                "numero_cuota":      f.numero_cuota,
                "fecha_vencimiento": f.fecha_vencimiento.isoformat(),
                "cuota_total":       f"{f.cuota_total:,.2f}",
                "capital":           f"{f.capital:,.2f}",
                "intereses":         f"{f.intereses:,.2f}",
                "saldo_restante":    f"{f.saldo_restante:,.2f}",
            }
            for f in resultado["tabla"]
        ]
        self._tabla_preview.cargar(tabla_dicts)

    # ── Save ─────────────────────────────────────────────────────────────

    def _guardar(self):
        self._lbl_error.setText("")
        if not self._cliente_seleccionado:
            self._lbl_error.setText("Seleccione un cliente.")
            return
        if not self._resultado:
            self._lbl_error.setText("Primero calcule la tabla.")
            return
        datos = self._get_form_data()
        datos["notas"] = self._notas.toPlainText().strip()
        cliente_id = self._cliente_seleccionado["id"]
        self._lbl_error.setText("Guardando...")
        self._worker = Worker(crear, cliente_id, datos)
        self._worker.result.connect(lambda _: self._post_guardar())
        self._worker.error.connect(lambda msg: self._lbl_error.setText(msg))
        self._worker.start()

    def _post_guardar(self):
        if self._on_guardado:
            self._on_guardado()
        self.accept()

    # ── Helpers ──────────────────────────────────────────────────────────

    def _get_form_data(self) -> dict:
        data = {}
        for key, w in self._v.items():
            data[key] = self._get_widget_value(w)
        return data

    def _get_widget_value(self, w: QWidget) -> str:
        if isinstance(w, QLineEdit):
            return w.text()
        if isinstance(w, QComboBox):
            return w.currentText()
        return ""

    def _set_widget_value(self, w: QWidget, val: str):
        if isinstance(w, QLineEdit):
            w.setText(val)
        elif isinstance(w, QComboBox):
            idx = w.findText(val)
            if idx >= 0:
                w.setCurrentIndex(idx)
