"""Loan detail dialog with amortization table and payment history — PyQt6."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QFrame,
)
from PyQt6.QtCore import Qt

from config import ESTADO_COLORS
from controllers.prestamo_controller import obtener, cuotas as get_cuotas
from controllers.pago_controller import historial_pagos_prestamo
from views.components.tabla import Tabla
from views.components.worker import Worker

COLS_CUOTAS = [
    ("numero_cuota",      "#",           40),
    ("fecha_vencimiento", "Vencimiento", 110),
    ("cuota_total",       "Cuota",        90),
    ("capital",           "Capital",      90),
    ("intereses",         "Intereses",    90),
    ("saldo_restante",    "Saldo",        90),
    ("estado",            "Estado",       90),
]

COLS_PAGOS = [
    ("fecha_pago",      "Fecha",       100),
    ("numero_recibo",   "Recibo",      120),
    ("numero_cuota",    "Cuota#",       60),
    ("monto_capital",   "Capital",      90),
    ("monto_intereses", "Intereses",    90),
    ("monto_mora",      "Mora",         80),
    ("monto_total",     "Total",        90),
    ("metodo_pago",     "Método",       90),
]


class DetallePrestamo(QDialog):

    def __init__(self, prestamo_id: int, parent=None):
        super().__init__(parent)
        self._prestamo_id = prestamo_id
        self._cuotas_data: list = []
        self._worker: Worker | None = None

        prestamo = obtener(prestamo_id)
        if not prestamo:
            self.done(0)
            return

        self._prestamo = prestamo
        self.setWindowTitle(f"Detalle Préstamo: {prestamo['numero_prestamo']}")
        self.resize(920, 720)
        self.setModal(True)

        self._build_skeleton()
        self._cargar_datos()

    def _build_skeleton(self):
        p = self._prestamo
        color = ESTADO_COLORS.get(p["estado"], "#2563EB")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)
        scroll.setWidget(inner)
        root.addWidget(scroll, 1)

        # ── Header ─────────────────────────────────────────────
        hdr = QFrame()
        hdr.setObjectName("card")
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(16, 10, 16, 10)

        lbl_num = QLabel(p["numero_prestamo"])
        lbl_num.setStyleSheet("font-size: 16px; font-weight: bold;")
        hl.addWidget(lbl_num, 1)

        lbl_estado = QLabel(p["estado"])
        lbl_estado.setStyleSheet(f"color: {color}; font-weight: bold;")
        hl.addWidget(lbl_estado)

        layout.addWidget(hdr)

        # ── Summary ────────────────────────────────────────────
        info_frame = QFrame()
        info_frame.setObjectName("card")
        info_layout = QHBoxLayout(info_frame)
        info_layout.setContentsMargins(16, 12, 16, 12)
        info_layout.setSpacing(16)

        datos = [
            ("Cliente",          f"{p['nombres']} {p['apellidos']}"),
            ("Capital Original", f"{p['monto_principal']:,.2f}"),
            ("Saldo Actual",     f"{p['saldo_capital']:,.2f}"),
            ("Cuota",            f"{p['cuota_base']:,.2f}"),
            ("Tasa",             f"{p['tasa_interes']}% {p['tipo_tasa']}"),
            ("Frecuencia",       p["frecuencia_pago"]),
            ("Inicio",           p["fecha_inicio"]),
            ("Vencimiento",      p["fecha_vencimiento"]),
            ("Total Intereses",  f"{p['total_intereses']:,.2f}"),
            ("Total a Pagar",    f"{p['total_a_pagar']:,.2f}"),
        ]

        # Two-column grid
        col_widgets = [QWidget(), QWidget()]
        for cw in col_widgets:
            cw.setStyleSheet("background: transparent;")
            QVBoxLayout(cw).setContentsMargins(0, 0, 0, 0)

        for i, (label, valor) in enumerate(datos):
            col = i % 2
            f = QWidget()
            f.setStyleSheet("background: transparent;")
            fl = QHBoxLayout(f)
            fl.setContentsMargins(0, 4, 0, 4)
            fl.setSpacing(8)
            lbl_k = QLabel(label + ":")
            lbl_k.setObjectName("dim")
            fl.addWidget(lbl_k)
            lbl_v = QLabel(valor)
            lbl_v.setStyleSheet("font-weight: bold;")
            fl.addWidget(lbl_v)
            col_widgets[col].layout().addWidget(f)

        for cw in col_widgets:
            cw.layout().addStretch()
            info_layout.addWidget(cw, 1)

        layout.addWidget(info_frame)

        # ── Amortization table ─────────────────────────────────
        amort_hdr = QWidget()
        amort_hdr.setStyleSheet("background: transparent;")
        ah = QHBoxLayout(amort_hdr)
        ah.setContentsMargins(0, 4, 0, 2)

        lbl_amort = QLabel("Tabla de Amortización")
        lbl_amort.setObjectName("section")
        ah.addWidget(lbl_amort, 1)

        btn_export = QPushButton("📥  Exportar Excel")
        btn_export.setObjectName("btn_secondary")
        btn_export.setFixedHeight(32)
        btn_export.clicked.connect(self._exportar_amortizacion)
        ah.addWidget(btn_export)

        layout.addWidget(amort_hdr)

        self._tabla_cuotas = Tabla(columnas=COLS_CUOTAS, height=220)
        layout.addWidget(self._tabla_cuotas)

        lbl_pagos = QLabel("Historial de Pagos")
        lbl_pagos.setObjectName("section")
        layout.addWidget(lbl_pagos)

        self._tabla_pagos = Tabla(columnas=COLS_PAGOS, height=180)
        layout.addWidget(self._tabla_pagos)

        self._lbl_cargando = QLabel("Cargando datos...")
        self._lbl_cargando.setObjectName("dim")
        layout.addWidget(self._lbl_cargando)

        layout.addStretch()

        # Close button
        btn_close = QPushButton("Cerrar")
        btn_close.setObjectName("btn_secondary")
        btn_close.clicked.connect(self.accept)
        root.addWidget(btn_close)

    def _cargar_datos(self):
        def _fetch():
            cuotas = get_cuotas(self._prestamo_id)
            pagos  = historial_pagos_prestamo(self._prestamo_id)
            return cuotas, pagos

        self._worker = Worker(_fetch)
        self._worker.result.connect(lambda r: self._mostrar_datos(*r))
        self._worker.start()

    def _mostrar_datos(self, cuotas: list, pagos: list):
        self._cuotas_data = cuotas
        self._tabla_cuotas.cargar([{**c,
            "cuota_total":    f"{c['cuota_total']:,.2f}",
            "capital":        f"{c['capital']:,.2f}",
            "intereses":      f"{c['intereses']:,.2f}",
            "saldo_restante": f"{c['saldo_restante']:,.2f}",
        } for c in cuotas])
        self._tabla_pagos.cargar(pagos)
        self._lbl_cargando.setText("")

    def _exportar_amortizacion(self):
        try:
            from services.excel_exporter import exportar_amortizacion
            import subprocess
            path = exportar_amortizacion(self._prestamo, self._cuotas_data)
            subprocess.Popen(["open", path])
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", str(e))
