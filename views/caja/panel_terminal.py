"""Verifone payment terminal panel — PyQt6 modal dialog."""

import threading
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QWidget,
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject

from services.terminal_pago import TerminalPago
from database.seed import get_config


class _TerminalSignals(QObject):
    done = pyqtSignal(dict)


class PanelTerminal(QDialog):

    def __init__(self, monto: float, referencia_base: str = "",
                 on_aprobado=None, on_rechazado=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Terminal de Pago — Tarjeta")
        self.setFixedSize(500, 600)
        self.setModal(True)

        self._monto        = monto
        self._ref_base     = referencia_base
        self._on_aprobado  = on_aprobado
        self._on_rechazado = on_rechazado
        self._moneda       = get_config("moneda_simbolo") or "RD$"
        self._terminal     = TerminalPago()
        self._signals      = _TerminalSignals()
        self._signals.done.connect(self._mostrar_estado)

        self._build()
        self._iniciar()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Blue header ────────────────────────────────────────
        header = QWidget()
        header.setStyleSheet("background: #2563EB;")
        hl = QVBoxLayout(header)
        hl.setContentsMargins(20, 20, 20, 20)
        hl.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        lbl_top = QLabel("💳  PAGO CON TARJETA")
        lbl_top.setStyleSheet("color: #BFDBFE; font-size: 11px; font-weight: bold; background: transparent;")
        lbl_top.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        hl.addWidget(lbl_top)

        lbl_sub = QLabel("MONTO A COBRAR")
        lbl_sub.setStyleSheet("color: #93C5FD; font-size: 10px; background: transparent;")
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        hl.addWidget(lbl_sub)

        lbl_monto = QLabel(f"{self._moneda} {self._monto:,.2f}")
        lbl_monto.setStyleSheet(
            "color: white; font-size: 48px; font-weight: bold; background: transparent;"
        )
        lbl_monto.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        hl.addWidget(lbl_monto)

        root.addWidget(header)

        # ── Status banner ─────────────────────────────────────
        self._banner = QFrame()
        self._banner.setFixedHeight(44)
        self._banner.setStyleSheet("background: #D97706;")
        bl = QHBoxLayout(self._banner)
        bl.setContentsMargins(0, 0, 0, 0)

        self._lbl_status = QLabel("⏳  Iniciando terminal...")
        self._lbl_status.setStyleSheet("color: white; font-size: 12px; font-weight: bold; background: transparent;")
        self._lbl_status.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        bl.addWidget(self._lbl_status)

        root.addWidget(self._banner)

        # ── Body ──────────────────────────────────────────────
        body = QWidget()
        body.setStyleSheet("background: transparent;")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(20, 16, 20, 16)
        body_layout.setSpacing(12)

        self._lbl_instruccion = QLabel("")
        self._lbl_instruccion.setObjectName("dim")
        self._lbl_instruccion.setWordWrap(True)
        self._lbl_instruccion.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        body_layout.addWidget(self._lbl_instruccion)

        # Display card (shown in DISPLAY mode)
        self._display_card = QFrame()
        self._display_card.setStyleSheet(
            "background: #EFF6FF; border-radius: 16px; border: 2px solid #2563EB;"
        )
        dc_layout = QVBoxLayout(self._display_card)
        dc_layout.setContentsMargins(20, 16, 20, 14)
        dc_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        QLabel("Dígite este monto en el Verifone:").setParent(self._display_card)
        lbl_dc1 = QLabel("Dígite este monto en el Verifone:")
        lbl_dc1.setObjectName("dim")
        lbl_dc1.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        dc_layout.addWidget(lbl_dc1)

        lbl_dc_monto = QLabel(f"{self._moneda} {self._monto:,.2f}")
        lbl_dc_monto.setStyleSheet("color: #2563EB; font-size: 36px; font-weight: bold; background: transparent;")
        lbl_dc_monto.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        dc_layout.addWidget(lbl_dc_monto)

        lbl_ref = QLabel(f"Ref: {self._ref_base}")
        lbl_ref.setObjectName("dim")
        lbl_ref.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        dc_layout.addWidget(lbl_ref)

        body_layout.addWidget(self._display_card)

        # Auth code frame
        codigo_frame = QFrame()
        codigo_frame.setObjectName("card")
        cf_layout = QVBoxLayout(codigo_frame)
        cf_layout.setContentsMargins(16, 14, 16, 10)
        cf_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        lbl_auth = QLabel("Código de Autorización")
        lbl_auth.setObjectName("section")
        lbl_auth.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        cf_layout.addWidget(lbl_auth)

        lbl_auth_sub = QLabel("Ingrese el código que aparece en el comprobante del terminal")
        lbl_auth_sub.setObjectName("dim")
        lbl_auth_sub.setWordWrap(True)
        lbl_auth_sub.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        cf_layout.addWidget(lbl_auth_sub)

        self._entry_codigo = QLineEdit()
        self._entry_codigo.setPlaceholderText("Ej: 123456")
        self._entry_codigo.setFixedHeight(50)
        self._entry_codigo.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self._entry_codigo.setStyleSheet("font-size: 22px; font-weight: bold; border: 2px solid #2563EB;")
        self._entry_codigo.returnPressed.connect(self._aprobar)
        cf_layout.addWidget(self._entry_codigo)

        self._lbl_error = QLabel("")
        self._lbl_error.setStyleSheet("color: #DC2626;")
        self._lbl_error.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        cf_layout.addWidget(self._lbl_error)

        body_layout.addWidget(codigo_frame)

        # Buttons
        btn_bar = QWidget()
        btn_bar.setStyleSheet("background: transparent;")
        btn_layout = QHBoxLayout(btn_bar)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(8)

        btn_cancel = QPushButton("✕  Cancelar")
        btn_cancel.setObjectName("btn_secondary")
        btn_cancel.setFixedHeight(46)
        btn_cancel.setStyleSheet(
            "QPushButton#btn_secondary { color: #DC2626; border: 1px solid #DC2626; }"
        )
        btn_cancel.clicked.connect(self._rechazar)
        btn_layout.addWidget(btn_cancel, 1)

        self._btn_aprobar = QPushButton("✅  Confirmar Aprobado")
        self._btn_aprobar.setObjectName("btn_success")
        self._btn_aprobar.setFixedHeight(46)
        self._btn_aprobar.clicked.connect(self._aprobar)
        btn_layout.addWidget(self._btn_aprobar, 1)

        body_layout.addWidget(btn_bar)
        root.addWidget(body, 1)

    def _iniciar(self):
        def _run():
            resultado = self._terminal.iniciar_pago(self._monto, self._ref_base)
            self._signals.done.emit(resultado)
        threading.Thread(target=_run, daemon=True).start()

    def _mostrar_estado(self, resultado: dict):
        modo = resultado.get("modo", "DISPLAY")
        msg  = resultado.get("msg", "")

        if modo == "SERIAL" and resultado.get("ok"):
            self._banner.setStyleSheet("background: #16A34A;")
            self._lbl_status.setText("📡  Comando enviado al terminal — espere la respuesta")
            self._display_card.hide()
            self._lbl_instruccion.setText(
                "El terminal Verifone recibió el monto automáticamente.\n"
                "Complete la operación en el terminal y luego ingrese\n"
                "el código de autorización del comprobante."
            )
        else:
            if resultado.get("ok") is False:
                self._banner.setStyleSheet("background: #D97706;")
                self._lbl_status.setText("📟  Modo manual — ingrese el monto en el terminal")
                self._lbl_instruccion.setText(
                    f"⚠ {msg}\nDígite el monto manualmente en el Verifone."
                )
            else:
                self._banner.setStyleSheet("background: #2563EB;")
                self._lbl_status.setText("📟  Modo Display — dígite el monto en el terminal")
                self._lbl_instruccion.setText(
                    "Dígite el monto en el Verifone tal como aparece abajo.\n"
                    "Una vez aprobado, ingrese el código de autorización."
                )
        self._entry_codigo.setFocus()

    def _aprobar(self):
        codigo = self._entry_codigo.text().strip()
        self._lbl_error.setText("")
        if not codigo:
            self._lbl_error.setText("⚠ Ingrese el código de autorización primero.")
            self._entry_codigo.setFocus()
            return
        if len(codigo) < 4:
            self._lbl_error.setText("⚠ El código debe tener al menos 4 caracteres.")
            self._entry_codigo.setFocus()
            return
        resultado = self._terminal.confirmar(codigo)
        if resultado.aprobado:
            if self._on_aprobado:
                self._on_aprobado(codigo)
            self.accept()
        else:
            self._lbl_error.setText("❌ Código inválido. Verifique e intente de nuevo.")
            self._entry_codigo.selectAll()
            self._entry_codigo.setFocus()

    def _rechazar(self):
        self._terminal.rechazar()
        if self._on_rechazado:
            self._on_rechazado()
        self.reject()

    def closeEvent(self, event):
        self._rechazar()
        event.accept()
