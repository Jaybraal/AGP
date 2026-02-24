"""Quick payment screen — PyQt6 (core daily module)."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QScrollArea, QRadioButton, QButtonGroup,
    QDialog,
)
from PyQt6.QtCore import Qt, QTimer

from controllers.prestamo_controller import buscar as buscar_prestamos
from controllers.pago_controller import (
    calcular_pago_cuota_normal, cobrar_cuota_normal,
    calcular_cancelacion, cobrar_cancelacion_total,
)
from database.seed import get_config
from views.components.modal_confirm import confirmar
from views.components.worker import Worker


class CobroRapido(QWidget):

    def __init__(self, caja: dict, navegar=None, parent=None):
        super().__init__(parent)
        self._caja                   = caja
        self._navegar                = navegar
        self._prestamo_seleccionado  = None
        self._cuota_info             = None
        self._moneda                 = get_config("moneda_simbolo") or "RD$"
        self._worker: Worker | None  = None
        self._search_timer           = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._ejecutar_busqueda)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header bar ─────────────────────────────────────────
        hdr = QFrame()
        hdr.setObjectName("card")
        hdr.setStyleSheet("QFrame#card { border-radius: 0; }")
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(16, 8, 16, 8)

        lbl_caja = QLabel(
            f"💵  Caja del {self._caja['fecha']}  |  "
            f"Abierta: {self._caja['hora_apertura']}"
        )
        lbl_caja.setStyleSheet("font-size: 13px; font-weight: bold;")
        hl.addWidget(lbl_caja)

        self._lbl_cobrado = QLabel(
            f"Cobrado: {self._moneda} {self._caja['total_cobrado']:,.2f}"
        )
        self._lbl_cobrado.setStyleSheet("color: #16A34A; font-size: 12px;")
        hl.addWidget(self._lbl_cobrado)

        hl.addStretch()

        btn_cerrar = QPushButton("🔒  Cerrar Caja")
        btn_cerrar.setObjectName("btn_danger")
        btn_cerrar.setFixedHeight(34)
        btn_cerrar.clicked.connect(self._cerrar_caja)
        hl.addWidget(btn_cerrar)

        root.addWidget(hdr)

        # ── Two-column body ────────────────────────────────────
        body = QWidget()
        body.setStyleSheet("background: transparent;")
        bl = QHBoxLayout(body)
        bl.setContentsMargins(16, 12, 16, 12)
        bl.setSpacing(12)

        self._build_search_panel(bl)
        self._build_cobro_panel(bl)

        root.addWidget(body, 1)

    # ── Left: Search ────────────────────────────────────────────────────

    def _build_search_panel(self, parent_layout: QHBoxLayout):
        left = QFrame()
        left.setObjectName("card")
        ll = QVBoxLayout(left)
        ll.setContentsMargins(16, 16, 16, 12)
        ll.setSpacing(8)

        lbl = QLabel("Buscar Préstamo")
        lbl.setObjectName("section")
        ll.addWidget(lbl)

        self._entry_search = QLineEdit()
        self._entry_search.setPlaceholderText("Número préstamo, nombre o cédula...")
        self._entry_search.setFixedHeight(40)
        self._entry_search.setStyleSheet("font-size: 13px;")
        self._entry_search.textChanged.connect(self._on_search)
        ll.addWidget(self._entry_search)

        # Results list (scrollable)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._results_widget = QWidget()
        self._results_widget.setStyleSheet("background: transparent;")
        self._results_layout = QVBoxLayout(self._results_widget)
        self._results_layout.setContentsMargins(0, 0, 0, 0)
        self._results_layout.setSpacing(4)
        self._results_layout.addStretch()
        scroll.setWidget(self._results_widget)
        ll.addWidget(scroll, 1)

        parent_layout.addWidget(left, 1)

    def _on_search(self, _text: str):
        self._search_timer.stop()
        self._search_timer.start(220)

    def _ejecutar_busqueda(self):
        termino = self._entry_search.text().strip()
        self._clear_results()
        if not termino:
            return
        self._worker = Worker(buscar_prestamos, termino)
        self._worker.result.connect(self._on_busqueda_result)
        self._worker.start()

    def _on_busqueda_result(self, r: list):
        self._mostrar_resultados(r[:20])

    def _clear_results(self):
        for i in reversed(range(self._results_layout.count())):
            item = self._results_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()

    def _mostrar_resultados(self, resultados: list):
        self._clear_results()
        for p in resultados:
            color_estado = {
                "ACTIVO": "#2563EB",
                "VENCIDO": "#DC2626",
                "AL_DIA": "#16A34A",
            }.get(p["estado"], "#64748B")

            card = QFrame()
            card.setObjectName("card")
            card.setStyleSheet(
                "QFrame#card { border-radius: 8px; } "
                "QFrame#card:hover { background: #EFF6FF; }"
            )
            cl = QVBoxLayout(card)
            cl.setContentsMargins(10, 8, 10, 8)
            cl.setSpacing(4)

            top = QWidget()
            top.setStyleSheet("background: transparent;")
            tl = QHBoxLayout(top)
            tl.setContentsMargins(0, 0, 0, 0)

            lbl_num = QLabel(p["numero_prestamo"])
            lbl_num.setStyleSheet("font-weight: bold;")
            tl.addWidget(lbl_num, 1)

            lbl_estado = QLabel(p["estado"])
            lbl_estado.setStyleSheet(f"color: {color_estado};")
            tl.addWidget(lbl_estado)

            cl.addWidget(top)

            lbl_info = QLabel(
                f"{p['nombres']} {p['apellidos']}  |  "
                f"Saldo: {self._moneda} {p['saldo_capital']:,.2f}"
            )
            lbl_info.setObjectName("dim")
            cl.addWidget(lbl_info)

            btn_sel = QPushButton("Seleccionar")
            btn_sel.setFixedHeight(28)
            btn_sel.clicked.connect(lambda ch=False, pr=p: self._seleccionar_prestamo(pr))
            cl.addWidget(btn_sel, 0, Qt.AlignmentFlag.AlignRight)

            self._results_layout.insertWidget(self._results_layout.count() - 1, card)

    # ── Right: Payment panel ────────────────────────────────────────────

    def _build_cobro_panel(self, parent_layout: QHBoxLayout):
        self._right = QFrame()
        self._right.setObjectName("card")
        self._right_layout = QVBoxLayout(self._right)
        self._right_layout.setContentsMargins(16, 16, 16, 16)
        self._right_layout.setSpacing(8)
        self._mostrar_placeholder()
        parent_layout.addWidget(self._right, 1)

    def _mostrar_placeholder(self):
        self._clear_right()
        lbl = QLabel("← Busca y selecciona un préstamo")
        lbl.setObjectName("dim")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._right_layout.addWidget(lbl, 1, Qt.AlignmentFlag.AlignCenter)

    def _clear_right(self):
        for i in reversed(range(self._right_layout.count())):
            item = self._right_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()

    def _seleccionar_prestamo(self, prestamo: dict):
        self._prestamo_seleccionado = prestamo
        self._clear_right()
        self._build_panel_cobro()

    def _build_panel_cobro(self):
        p = self._prestamo_seleccionado

        lbl_title = QLabel("Cobrar Cuota")
        lbl_title.setObjectName("section")
        self._right_layout.addWidget(lbl_title)

        # Loan summary
        info = QFrame()
        info.setStyleSheet("background: #EFF6FF; border-radius: 8px; border: 1px solid #E2E8F0;")
        il = QVBoxLayout(info)
        il.setContentsMargins(12, 8, 12, 8)
        il.setSpacing(2)

        lbl_p = QLabel(f"{p['numero_prestamo']}  |  {p['nombres']} {p['apellidos']}")
        lbl_p.setStyleSheet("font-weight: bold;")
        il.addWidget(lbl_p)

        lbl_saldo = QLabel(f"Saldo capital: {self._moneda} {p['saldo_capital']:,.2f}")
        lbl_saldo.setObjectName("dim")
        il.addWidget(lbl_saldo)

        self._right_layout.addWidget(info)

        # Payment type
        lbl_tipo = QLabel("Tipo de Pago")
        self._right_layout.addWidget(lbl_tipo)

        tipo_row = QWidget()
        tipo_row.setStyleSheet("background: transparent;")
        tr = QHBoxLayout(tipo_row)
        tr.setContentsMargins(0, 0, 0, 0)
        tr.setSpacing(16)

        self._tipo_group = QButtonGroup(self)
        rb_normal = QRadioButton("Cuota Normal")
        rb_normal.setChecked(True)
        rb_normal.setStyleSheet("background: transparent;")
        rb_cancel = QRadioButton("Cancelación Total")
        rb_cancel.setStyleSheet("background: transparent;")
        self._tipo_group.addButton(rb_normal, 0)
        self._tipo_group.addButton(rb_cancel, 1)
        rb_normal.toggled.connect(self._actualizar_calculo)

        tr.addWidget(rb_normal)
        tr.addWidget(rb_cancel)
        tr.addStretch()
        self._right_layout.addWidget(tipo_row)

        # Breakdown frame
        self._breakdown = QFrame()
        self._breakdown.setStyleSheet(
            "background: #F8FAFC; border-radius: 8px; border: 1px solid #E2E8F0;"
        )
        self._breakdown_layout = QVBoxLayout(self._breakdown)
        self._breakdown_layout.setContentsMargins(12, 8, 12, 8)
        self._breakdown_layout.setSpacing(4)
        self._right_layout.addWidget(self._breakdown)

        # Payment method
        lbl_metodo = QLabel("Método de Pago")
        self._right_layout.addWidget(lbl_metodo)

        metodo_widget = QWidget()
        metodo_widget.setStyleSheet("background: transparent;")
        ml = QVBoxLayout(metodo_widget)
        ml.setContentsMargins(0, 0, 0, 0)
        ml.setSpacing(4)

        self._metodo_group = QButtonGroup(self)
        metodos = [
            ("💵 Efectivo",      "EFECTIVO"),
            ("💳 Tarjeta/POS",   "TARJETA"),
            ("🏦 Transferencia", "TRANSFERENCIA"),
            ("📄 Cheque",        "CHEQUE"),
        ]
        for i, (label, val) in enumerate(metodos):
            rb = QRadioButton(label)
            rb.setProperty("value", val)
            rb.setStyleSheet("background: transparent;")
            if i == 0:
                rb.setChecked(True)
            self._metodo_group.addButton(rb, i)
            ml.addWidget(rb)

        self._right_layout.addWidget(metodo_widget)

        lbl_ref = QLabel("Referencia (si aplica)")
        self._right_layout.addWidget(lbl_ref)

        self._ref_entry = QLineEdit()
        self._ref_entry.setFixedHeight(32)
        self._right_layout.addWidget(self._ref_entry)

        self._lbl_error = QLabel("")
        self._lbl_error.setStyleSheet("color: #DC2626;")
        self._right_layout.addWidget(self._lbl_error)

        self._btn_cobrar = QPushButton("✅  Registrar Pago")
        self._btn_cobrar.setObjectName("btn_success")
        self._btn_cobrar.setFixedHeight(44)
        self._btn_cobrar.setStyleSheet(
            "QPushButton#btn_success { font-size: 13px; font-weight: bold; }"
        )
        self._btn_cobrar.clicked.connect(self._registrar_pago)
        self._right_layout.addWidget(self._btn_cobrar)

        self._actualizar_calculo()

    def _actualizar_calculo(self):
        self._clear_breakdown()
        self._cuota_info = None
        lbl = QLabel("Calculando...")
        lbl.setObjectName("dim")
        lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self._breakdown_layout.addWidget(lbl)

        p = self._prestamo_seleccionado
        tipo_id = self._tipo_group.checkedId()
        tipo = "CUOTA_NORMAL" if tipo_id == 0 else "CANCELACION_TOTAL"
        self._worker = Worker(self._calcular_bg, p["id"], tipo)
        self._worker.result.connect(self._on_calculo_result)
        self._worker.error.connect(self._mostrar_error_calc)
        self._worker.start()

    def _on_calculo_result(self, r):
        self._mostrar_calculo(r[0], r[1])

    def _calcular_bg(self, prestamo_id: int, tipo: str):
        if tipo == "CUOTA_NORMAL":
            info = calcular_pago_cuota_normal(prestamo_id)
        else:
            info = calcular_cancelacion(prestamo_id)
        return info, tipo

    def _clear_breakdown(self):
        for i in reversed(range(self._breakdown_layout.count())):
            item = self._breakdown_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()

    def _mostrar_calculo(self, info: dict, tipo: str):
        self._clear_breakdown()
        self._cuota_info = info
        m = self._moneda

        if tipo == "CUOTA_NORMAL":
            cuota = info["cuota"]
            cap_pend = round(cuota["capital"]   - cuota["capital_pagado"],   2)
            int_pend = round(cuota["intereses"] - cuota["intereses_pagados"], 2)
            filas = [
                ("Cuota #",     str(cuota["numero_cuota"])),
                ("Vencimiento", cuota["fecha_vencimiento"]),
                ("Capital",     f"{m} {cap_pend:,.2f}"),
                ("Intereses",   f"{m} {int_pend:,.2f}"),
                ("Mora",        f"{m} {cuota['monto_mora']:,.2f}  ({cuota['dias_mora']} días)"),
                ("TOTAL",       f"{m} {cuota['total_a_cobrar']:,.2f}"),
            ]
        else:
            cancel = info["cancelacion"]
            filas = [
                ("Capital",           f"{m} {cancel['capital']:,.2f}"),
                ("Intereses Pend.",   f"{m} {cancel['intereses_pendientes']:,.2f}"),
                ("Mora Total",        f"{m} {cancel['mora_total']:,.2f}"),
                ("TOTAL CANCELACIÓN", f"{m} {cancel['total']:,.2f}"),
            ]

        for label, valor in filas:
            row = QWidget()
            row.setStyleSheet("background: transparent;")
            rl = QHBoxLayout(row)
            rl.setContentsMargins(0, 2, 0, 2)
            lbl_k = QLabel(label)
            lbl_k.setObjectName("dim")
            rl.addWidget(lbl_k, 1)
            bold = label.startswith("TOTAL")
            lbl_v = QLabel(valor)
            if bold:
                lbl_v.setStyleSheet("font-weight: bold; color: #D97706;")
            rl.addWidget(lbl_v)
            self._breakdown_layout.addWidget(row)

    def _mostrar_error_calc(self, msg: str):
        self._clear_breakdown()
        lbl = QLabel(msg)
        lbl.setStyleSheet("color: #DC2626;")
        lbl.setWordWrap(True)
        self._breakdown_layout.addWidget(lbl)

    # ── Payment ──────────────────────────────────────────────────────────

    def _registrar_pago(self):
        self._lbl_error.setText("")
        if not self._cuota_info:
            self._lbl_error.setText("No hay cuota calculada.")
            return

        tipo_id = self._tipo_group.checkedId()
        tipo    = "CUOTA_NORMAL" if tipo_id == 0 else "CANCELACION_TOTAL"
        metodo  = self._metodo_group.checkedButton().property("value")

        if metodo == "TARJETA":
            if tipo == "CUOTA_NORMAL":
                monto = self._cuota_info["cuota"]["total_a_cobrar"]
            else:
                monto = self._cuota_info["cancelacion"]["total"]
            self._abrir_terminal(monto, tipo)
            return

        self._ejecutar_cobro(tipo, metodo, self._ref_entry.text().strip())

    def _abrir_terminal(self, monto: float, tipo_cobro: str):
        from views.caja.panel_terminal import PanelTerminal
        p = self._prestamo_seleccionado

        def on_aprobado(codigo: str):
            self._ejecutar_cobro(tipo_cobro, "TARJETA", f"AUTH:{codigo}")

        def on_rechazado():
            self._lbl_error.setText("Pago rechazado en terminal.")

        dlg = PanelTerminal(
            monto=monto,
            referencia_base=p.get("numero_prestamo", ""),
            on_aprobado=on_aprobado,
            on_rechazado=on_rechazado,
            parent=self,
        )
        dlg.exec()

    def _ejecutar_cobro(self, tipo: str, metodo: str, ref: str):
        p = self._prestamo_seleccionado
        if tipo == "CUOTA_NORMAL":
            cuota = self._cuota_info["cuota"]
            total = cuota["total_a_cobrar"]
            msg   = f"¿Registrar pago de {self._moneda} {total:,.2f}?"
            confirmar(self, "Confirmar Pago", msg, "Registrar",
                      on_confirmado=lambda: self._cobro_bg("CUOTA_NORMAL", metodo, ref))
        else:
            cancel = self._cuota_info["cancelacion"]
            total  = cancel["total"]
            msg    = f"¿Cancelar total por {self._moneda} {total:,.2f}? Esta acción cerrará el préstamo."
            confirmar(self, "Confirmar Cancelación", msg, "Cancelar Préstamo",
                      on_confirmado=lambda: self._cobro_bg("CANCELACION_TOTAL", metodo, ref))

    def _cobro_bg(self, tipo: str, metodo: str, ref: str):
        p = self._prestamo_seleccionado
        if not p or not self._cuota_info:
            return
        self._btn_cobrar.setEnabled(False)
        self._btn_cobrar.setText("Procesando...")

        def _run():
            if tipo == "CUOTA_NORMAL":
                cuota     = self._cuota_info["cuota"]
                resultado = cobrar_cuota_normal(
                    prestamo_id=p["id"], cuota_id=cuota["id"],
                    metodo_pago=metodo, referencia_pago=ref,
                )
                return "normal", resultado
            else:
                cobrar_cancelacion_total(p["id"], metodo_pago=metodo, referencia_pago=ref)
                return "cancelacion", None

        self._worker = Worker(_run)
        self._worker.result.connect(self._post_cobro)
        self._worker.error.connect(self._post_cobro_error)
        self._worker.start()

    def _post_cobro(self, resultado: tuple):
        tipo, data = resultado
        self._btn_cobrar.setEnabled(True)
        self._btn_cobrar.setText("✅  Registrar Pago")
        self._refrescar_header()
        if tipo == "normal":
            self._mostrar_recibo(data)
            self._actualizar_calculo()
        else:
            self._mostrar_placeholder()
            self._entry_search.clear()
            self._prestamo_seleccionado = None

    def _post_cobro_error(self, msg: str):
        self._btn_cobrar.setEnabled(True)
        self._btn_cobrar.setText("✅  Registrar Pago")
        self._lbl_error.setText(msg)

    def _refrescar_header(self):
        caja_id = self._caja["id"]
        def _bg():
            from models.caja import obtener_caja
            return obtener_caja(caja_id)
        w = Worker(_bg)
        w.result.connect(self._on_header_refresh)
        w.start()

    def _on_header_refresh(self, caja):
        if caja:
            self._caja = caja

    def _mostrar_recibo(self, pago: dict):
        dlg = _ReciboDialog(pago=pago, moneda=self._moneda, parent=self)
        dlg.exec()

    def _cerrar_caja(self):
        from views.caja.cierre_caja import CierreCaja
        dlg = CierreCaja(caja=self._caja, on_cerrada=self._on_caja_cerrada, parent=self)
        dlg.exec()

    def _on_caja_cerrada(self):
        parent = self.parent()
        if hasattr(parent, "refrescar"):
            parent.refrescar()


# ── Receipt dialog ─────────────────────────────────────────────────────────────

class _ReciboDialog(QDialog):

    def __init__(self, pago: dict, moneda: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Recibo de Pago")
        self.setFixedSize(400, 380)
        self.setModal(True)
        self._build(pago, moneda)

    def _build(self, pago: dict, moneda: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        lbl_ok = QLabel("✅  Pago Registrado")
        lbl_ok.setStyleSheet("color: #16A34A; font-size: 16px; font-weight: bold;")
        lbl_ok.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(lbl_ok)

        lbl_rec = QLabel(f"Recibo: {pago['numero_recibo']}")
        lbl_rec.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(lbl_rec)

        card = QFrame()
        card.setObjectName("card")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(12, 12, 12, 12)
        cl.setSpacing(4)

        for label, val in [
            ("Capital",   f"{moneda} {pago['monto_capital']:,.2f}"),
            ("Intereses", f"{moneda} {pago['monto_intereses']:,.2f}"),
            ("Mora",      f"{moneda} {pago['monto_mora']:,.2f}"),
            ("TOTAL",     f"{moneda} {pago['monto_total']:,.2f}"),
        ]:
            row = QWidget()
            row.setStyleSheet("background: transparent;")
            rl = QHBoxLayout(row)
            rl.setContentsMargins(0, 0, 0, 0)
            rl.addWidget(QLabel(label))
            lbl_v = QLabel(val)
            if label == "TOTAL":
                lbl_v.setStyleSheet("font-weight: bold;")
            rl.addWidget(lbl_v, 0, Qt.AlignmentFlag.AlignRight)
            cl.addWidget(row)

        layout.addWidget(card)

        btn_pdf = QPushButton("🖨️  Generar PDF")
        btn_pdf.clicked.connect(lambda: self._imprimir(pago))
        layout.addWidget(btn_pdf)

        btn_close = QPushButton("Cerrar")
        btn_close.setObjectName("btn_secondary")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

    def _imprimir(self, pago: dict):
        try:
            from services.pdf_generator import generar_recibo
            import subprocess
            path = generar_recibo(pago["id"])
            subprocess.Popen(["open", path])
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Error PDF", str(e))
