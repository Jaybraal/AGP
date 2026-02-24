"""Reports main screen with tabs — PyQt6."""

from datetime import date
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTabWidget, QLineEdit,
)
from PyQt6.QtCore import Qt

from controllers.reporte_controller import caja, mora, proyeccion
from models.caja import listar_cajas
from models.pago import listar_pagos_caja
from views.components.tabla import Tabla
from views.components.worker import Worker


class ReportesMain(QWidget):

    def __init__(self, navegar=None, parent=None):
        super().__init__(parent)
        self._navegar = navegar
        self._workers: list = []
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 16)
        layout.setSpacing(0)

        # Header
        hdr = QLabel("Reportes")
        hdr.setObjectName("title")
        layout.addWidget(hdr)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background: #E2E8F0;")
        sep.setFixedHeight(1)
        layout.addWidget(sep)
        layout.addSpacing(12)

        self._tabs = QTabWidget()
        layout.addWidget(self._tabs, 1)

        tab1 = QWidget()
        tab2 = QWidget()
        tab3 = QWidget()
        tab4 = QWidget()

        self._tabs.addTab(tab1, "📊  Caja Diaria")
        self._tabs.addTab(tab2, "⚠️  Mora")
        self._tabs.addTab(tab3, "📈  Proyección")
        self._tabs.addTab(tab4, "🗂️  Historial Cajas")

        self._build_caja_tab(tab1)
        self._build_mora_tab(tab2)
        self._build_proyeccion_tab(tab3)
        self._build_historial_tab(tab4)

    # ── Caja Tab ────────────────────────────────────────────────────────

    def _build_caja_tab(self, parent: QWidget):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        top = QWidget()
        top.setStyleSheet("background: transparent;")
        tl = QHBoxLayout(top)
        tl.setContentsMargins(0, 0, 0, 0)
        tl.setSpacing(6)

        lbl = QLabel("Fecha:")
        lbl.setObjectName("dim")
        tl.addWidget(lbl)

        self._fecha_entry = QLineEdit(date.today().isoformat())
        self._fecha_entry.setFixedSize(140, 36)
        tl.addWidget(self._fecha_entry)

        btn_con = QPushButton("Consultar")
        btn_con.setFixedHeight(36)
        btn_con.clicked.connect(self._cargar_caja)
        tl.addWidget(btn_con)

        btn_pdf = QPushButton("🖨️  PDF")
        btn_pdf.setObjectName("btn_secondary")
        btn_pdf.setFixedHeight(36)
        btn_pdf.clicked.connect(self._pdf_caja)
        tl.addWidget(btn_pdf)

        btn_xl = QPushButton("📥  Excel")
        btn_xl.setObjectName("btn_secondary")
        btn_xl.setFixedHeight(36)
        btn_xl.clicked.connect(self._excel_caja)
        tl.addWidget(btn_xl)

        tl.addStretch()
        layout.addWidget(top)

        # Summary row
        self._resumen_caja = QFrame()
        self._resumen_caja.setStyleSheet(
            "background: #EFF6FF; border-radius: 8px; border: 1px solid #E2E8F0;"
        )
        self._resumen_layout = QHBoxLayout(self._resumen_caja)
        self._resumen_layout.setContentsMargins(12, 8, 12, 8)
        layout.addWidget(self._resumen_caja)

        cols = [
            ("fecha_pago",      "Fecha",       100),
            ("numero_recibo",   "Recibo",      120),
            ("cliente_nombre",  "Cliente",     180),
            ("numero_prestamo", "Préstamo",    120),
            ("monto_capital",   "Capital",      90),
            ("monto_intereses", "Intereses",    90),
            ("monto_mora",      "Mora",          80),
            ("monto_total",     "Total",         90),
        ]
        self._tabla_caja = Tabla(columnas=cols)
        layout.addWidget(self._tabla_caja, 1)

        self._cargar_caja()

    def _cargar_caja(self):
        w = Worker(caja, self._fecha_entry.text())
        w.result.connect(self._mostrar_caja)
        self._workers.append(w)
        w.start()

    def _mostrar_caja(self, reporte: dict):
        for i in reversed(range(self._resumen_layout.count())):
            item = self._resumen_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()

        t = reporte.get("totales", {})
        for lbl, val in [
            ("Cobros",    str(t.get("num_pagos", 0))),
            ("Capital",   f"RD$ {t.get('total_capital', 0):,.2f}"),
            ("Intereses", f"RD$ {t.get('total_intereses', 0):,.2f}"),
            ("Mora",      f"RD$ {t.get('total_mora', 0):,.2f}"),
            ("TOTAL",     f"RD$ {t.get('total_cobrado', 0):,.2f}"),
        ]:
            col = QWidget()
            col.setStyleSheet("background: transparent;")
            cl = QVBoxLayout(col)
            cl.setContentsMargins(8, 0, 8, 0)
            cl.setSpacing(2)

            lbl_k = QLabel(lbl)
            lbl_k.setObjectName("dim")
            cl.addWidget(lbl_k)

            lbl_v = QLabel(val)
            lbl_v.setStyleSheet("font-size: 13px; font-weight: bold;")
            cl.addWidget(lbl_v)

            self._resumen_layout.addWidget(col)

        self._resumen_layout.addStretch()
        self._tabla_caja.cargar(reporte.get("pagos", []))

    def _pdf_caja(self):
        try:
            from services.pdf_generator import generar_reporte_caja
            import subprocess
            path = generar_reporte_caja(self._fecha_entry.text())
            subprocess.Popen(["open", path])
        except Exception as e:
            self._show_error(str(e))

    def _excel_caja(self):
        try:
            from services.excel_exporter import exportar_caja
            reporte = caja(self._fecha_entry.text())
            path = exportar_caja(reporte)
            import subprocess
            subprocess.Popen(["open", path])
        except Exception as e:
            self._show_error(str(e))

    # ── Mora Tab ────────────────────────────────────────────────────────

    def _build_mora_tab(self, parent: QWidget):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        top = QWidget()
        top.setStyleSheet("background: transparent;")
        tl = QHBoxLayout(top)
        tl.setContentsMargins(0, 0, 0, 0)
        tl.setSpacing(6)

        btn_update = QPushButton("Actualizar")
        btn_update.setFixedHeight(36)
        btn_update.clicked.connect(self._cargar_mora)
        tl.addWidget(btn_update)

        btn_xl = QPushButton("📥  Excel")
        btn_xl.setObjectName("btn_secondary")
        btn_xl.setFixedHeight(36)
        btn_xl.clicked.connect(self._excel_mora)
        tl.addWidget(btn_xl)

        tl.addStretch()
        layout.addWidget(top)

        cols = [
            ("numero_prestamo",       "Préstamo",        130),
            ("cliente_nombre",        "Cliente",          180),
            ("cedula",                "Cédula",           110),
            ("telefono_principal",    "Teléfono",         110),
            ("primera_cuota_vencida", "Primera Vencida",  120),
            ("cuotas_vencidas",       "Cuotas Venc.",      90),
            ("monto_pendiente",       "Monto Pend.",       100),
            ("saldo_capital",         "Saldo Capital",     100),
        ]
        self._tabla_mora = Tabla(columnas=cols)
        layout.addWidget(self._tabla_mora, 1)
        self._cargar_mora()

    def _cargar_mora(self):
        w = Worker(mora)
        w.result.connect(self._tabla_mora.cargar)
        self._workers.append(w)
        w.start()

    def _excel_mora(self):
        try:
            from services.excel_exporter import exportar_mora
            path = exportar_mora(mora())
            import subprocess
            subprocess.Popen(["open", path])
        except Exception as e:
            self._show_error(str(e))

    # ── Proyección Tab ──────────────────────────────────────────────────

    def _build_proyeccion_tab(self, parent: QWidget):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        top = QWidget()
        top.setStyleSheet("background: transparent;")
        tl = QHBoxLayout(top)
        tl.setContentsMargins(0, 0, 0, 0)
        tl.setSpacing(6)

        lbl = QLabel("Días a proyectar:")
        lbl.setObjectName("dim")
        tl.addWidget(lbl)

        self._dias_entry = QLineEdit("30")
        self._dias_entry.setFixedSize(80, 36)
        tl.addWidget(self._dias_entry)

        btn_calc = QPushButton("Calcular")
        btn_calc.setFixedHeight(36)
        btn_calc.clicked.connect(self._cargar_proyeccion)
        tl.addWidget(btn_calc)

        btn_xl = QPushButton("📥  Excel")
        btn_xl.setObjectName("btn_secondary")
        btn_xl.setFixedHeight(36)
        btn_xl.clicked.connect(self._excel_proyeccion)
        tl.addWidget(btn_xl)

        tl.addStretch()
        layout.addWidget(top)

        cols = [
            ("fecha_vencimiento",   "Fecha",         110),
            ("num_cuotas",          "# Cuotas",       80),
            ("monto_esperado",      "Esperado",       110),
            ("capital_esperado",    "Capital",        110),
            ("intereses_esperados", "Intereses",      110),
        ]
        self._tabla_proy = Tabla(columnas=cols)
        layout.addWidget(self._tabla_proy, 1)
        self._cargar_proyeccion()

    def _cargar_proyeccion(self):
        try:
            dias = int(self._dias_entry.text() or 30)
        except ValueError:
            dias = 30
        w = Worker(proyeccion, dias)
        w.result.connect(self._tabla_proy.cargar)
        self._workers.append(w)
        w.start()

    def _excel_proyeccion(self):
        try:
            from services.excel_exporter import exportar_proyeccion
            try:
                dias = int(self._dias_entry.text() or 30)
            except ValueError:
                dias = 30
            path = exportar_proyeccion(proyeccion(dias))
            import subprocess
            subprocess.Popen(["open", path])
        except Exception as e:
            self._show_error(str(e))

    # ── Historial Tab ───────────────────────────────────────────────────

    def _build_historial_tab(self, parent: QWidget):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        top = QWidget()
        top.setStyleSheet("background: transparent;")
        tl = QHBoxLayout(top)
        tl.setContentsMargins(0, 0, 0, 0)
        tl.setSpacing(6)

        btn_update = QPushButton("Actualizar")
        btn_update.setFixedHeight(36)
        btn_update.clicked.connect(self._cargar_historial)
        tl.addWidget(btn_update)

        lbl_sub = QLabel("  Mostrando últimas 60 sesiones")
        lbl_sub.setObjectName("dim")
        tl.addWidget(lbl_sub)

        tl.addStretch()
        layout.addWidget(top)

        cols_cajas = [
            ("fecha",          "Fecha",          100),
            ("hora_apertura",  "Apertura",         80),
            ("hora_cierre",    "Cierre",           80),
            ("estado",         "Estado",           80),
            ("monto_apertura", "Monto Inicial",   110),
            ("total_cobrado",  "Total Cobrado",   120),
            ("monto_cierre",   "Monto Cierre",    110),
        ]
        self._tabla_hist = Tabla(columnas=cols_cajas, on_select=self._on_caja_select)
        layout.addWidget(self._tabla_hist)

        # Detail area
        self._detalle_caja = QFrame()
        self._detalle_caja.setStyleSheet(
            "background: #EFF6FF; border-radius: 10px; border: 1px solid #E2E8F0;"
        )
        self._detalle_layout = QVBoxLayout(self._detalle_caja)
        self._detalle_layout.setContentsMargins(12, 10, 12, 10)

        self._lbl_detalle = QLabel("Seleccione una sesión de caja para ver sus pagos")
        self._lbl_detalle.setObjectName("dim")
        self._detalle_layout.addWidget(self._lbl_detalle)

        layout.addWidget(self._detalle_caja)

        self._cargar_historial()

    def _cargar_historial(self):
        w = Worker(listar_cajas, 60)
        w.result.connect(self._tabla_hist.cargar)
        self._workers.append(w)
        w.start()

    def _on_caja_select(self, caja_row: dict):
        # Clear detail area
        for i in reversed(range(self._detalle_layout.count())):
            item = self._detalle_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()

        hdr = QWidget()
        hdr.setStyleSheet("background: transparent;")
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(0, 0, 0, 4)

        estado_color = "#2563EB" if caja_row["estado"] == "ABIERTA" else "#64748B"
        lbl_h = QLabel(f"Pagos de la caja del {caja_row['fecha']}")
        lbl_h.setStyleSheet("font-weight: bold;")
        hl.addWidget(lbl_h)

        lbl_est = QLabel(f"  [{caja_row['estado']}]")
        lbl_est.setStyleSheet(f"color: {estado_color};")
        hl.addWidget(lbl_est)

        hl.addStretch()

        lbl_total = QLabel(f"Total cobrado: RD$ {caja_row.get('total_cobrado', 0):,.2f}")
        lbl_total.setStyleSheet("color: #2563EB; font-weight: bold;")
        hl.addWidget(lbl_total)

        self._detalle_layout.addWidget(hdr)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background: #E2E8F0;")
        self._detalle_layout.addWidget(sep)

        cols_pagos = [
            ("hora_pago",       "Hora",      70),
            ("numero_recibo",   "Recibo",   120),
            ("cliente_nombre",  "Cliente",  160),
            ("numero_prestamo", "Préstamo", 110),
            ("monto_capital",   "Capital",   85),
            ("monto_intereses", "Intereses", 85),
            ("monto_mora",      "Mora",       75),
            ("monto_total",     "Total",      90),
            ("metodo_pago",     "Método",     90),
        ]
        tabla_pagos = Tabla(columnas=cols_pagos)
        self._detalle_layout.addWidget(tabla_pagos)

        w = Worker(listar_pagos_caja, caja_row["id"])
        w.result.connect(tabla_pagos.cargar)
        self._workers.append(w)
        w.start()

    # ── Helpers ─────────────────────────────────────────────────────────

    def _show_error(self, msg: str):
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.warning(self, "Error", msg)
