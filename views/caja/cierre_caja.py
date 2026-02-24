"""Daily cash closing dialog — PyQt6."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QScrollArea, QWidget,
)
from PyQt6.QtCore import Qt

from controllers.caja_controller import cerrar
from controllers.pago_controller import pagos_de_caja


class CierreCaja(QDialog):

    def __init__(self, caja: dict, on_cerrada=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cierre de Caja")
        self.resize(540, 660)
        self.setModal(True)
        self._caja       = caja
        self._on_cerrada = on_cerrada
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(20, 16, 20, 8)
        layout.setSpacing(10)
        scroll.setWidget(inner)
        root.addWidget(scroll, 1)

        lbl_title = QLabel("Cierre de Caja")
        lbl_title.setObjectName("title")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(lbl_title)

        caja  = self._caja
        pagos = pagos_de_caja(caja["id"])

        total_capital   = sum(p["monto_capital"]   for p in pagos)
        total_intereses = sum(p["monto_intereses"] for p in pagos)
        total_mora      = sum(p["monto_mora"]      for p in pagos)
        total_cobrado   = sum(p["monto_total"]     for p in pagos)

        # Summary card
        card = QFrame()
        card.setObjectName("card")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(16, 12, 16, 12)
        cl.setSpacing(4)

        datos = [
            ("Fecha",           caja["fecha"]),
            ("Hora Apertura",   caja["hora_apertura"]),
            ("Monto Apertura",  f"RD$ {caja['monto_apertura']:,.2f}"),
            ("Núm. de Cobros",  str(len(pagos))),
            ("Total Capital",   f"RD$ {total_capital:,.2f}"),
            ("Total Intereses", f"RD$ {total_intereses:,.2f}"),
            ("Total Mora",      f"RD$ {total_mora:,.2f}"),
            ("TOTAL COBRADO",   f"RD$ {total_cobrado:,.2f}"),
        ]

        for label, valor in datos:
            row = QWidget()
            row.setStyleSheet("background: transparent;")
            rl = QHBoxLayout(row)
            rl.setContentsMargins(0, 2, 0, 2)
            lbl_k = QLabel(label)
            lbl_k.setObjectName("dim")
            rl.addWidget(lbl_k, 1)
            lbl_v = QLabel(valor)
            if label.startswith("TOTAL"):
                lbl_v.setStyleSheet("font-weight: bold;")
            rl.addWidget(lbl_v)
            cl.addWidget(row)

        layout.addWidget(card)

        # Monto cierre
        lbl_mc = QLabel("Efectivo contado en caja (RD$)")
        layout.addWidget(lbl_mc)

        self._monto_cierre = QLineEdit(f"{caja['monto_apertura'] + total_cobrado:.2f}")
        self._monto_cierre.setFixedHeight(40)
        self._monto_cierre.setStyleSheet("font-size: 15px;")
        layout.addWidget(self._monto_cierre)

        lbl_notas = QLabel("Notas")
        layout.addWidget(lbl_notas)

        self._notas = QLineEdit()
        self._notas.setFixedHeight(34)
        layout.addWidget(self._notas)

        self._lbl_error = QLabel("")
        self._lbl_error.setStyleSheet("color: #DC2626;")
        self._lbl_error.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self._lbl_error)

        # Buttons
        btn_bar = QWidget()
        btn_bar.setStyleSheet("background: transparent;")
        bl = QHBoxLayout(btn_bar)
        bl.setContentsMargins(20, 8, 20, 16)
        bl.setSpacing(8)

        btn_pdf = QPushButton("🖨️  Reporte PDF")
        btn_pdf.setObjectName("btn_secondary")
        btn_pdf.clicked.connect(self._imprimir)
        bl.addWidget(btn_pdf)

        bl.addStretch()

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("btn_secondary")
        btn_cancel.clicked.connect(self.reject)
        bl.addWidget(btn_cancel)

        btn_cerrar = QPushButton("🔒  Confirmar Cierre")
        btn_cerrar.setObjectName("btn_danger")
        btn_cerrar.clicked.connect(self._cerrar)
        bl.addWidget(btn_cerrar)

        root.addWidget(btn_bar)

    def _cerrar(self):
        self._lbl_error.setText("")
        try:
            monto = float(self._monto_cierre.text() or 0)
            notas = self._notas.text().strip()
            cerrar(self._caja["id"], monto, notas)
            cb = self._on_cerrada
            self.accept()
            if cb:
                cb()
        except Exception as e:
            self._lbl_error.setText(str(e))

    def _imprimir(self):
        try:
            from services.pdf_generator import generar_reporte_caja
            import subprocess
            path = generar_reporte_caja(self._caja["fecha"])
            subprocess.Popen(["open", path])
        except Exception as e:
            self._lbl_error.setText(str(e))
