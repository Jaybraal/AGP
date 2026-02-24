"""
PDF generation service.
Generates:
  - Thermal receipt (80mm width) for individual payments
  - Full daily cash report (A4)
"""

import os
from datetime import datetime
from fpdf import FPDF
from config import RECEIPTS_DIR, REPORTS_DIR, LOGO_PATH
from database.seed import get_config
from models.pago import obtener_pago
from database.connection import get_connection


# ─────────────────────────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────────────────────────

def _agencia_info() -> dict:
    return {
        "nombre":    get_config("nombre_agencia"),
        "nit":       get_config("nit_agencia"),
        "direccion": get_config("direccion_agencia"),
        "telefono":  get_config("telefono_agencia"),
        "moneda":    get_config("moneda_simbolo") or "RD$",
    }


def _fmt(valor: float, moneda: str = "RD$") -> str:
    return f"{moneda} {valor:,.2f}"


# ─────────────────────────────────────────────────────────────────
# Thermal Receipt (80mm)
# ─────────────────────────────────────────────────────────────────

class _Recibo(FPDF):
    W = 80          # receipt width mm
    MARGIN = 4

    def __init__(self):
        super().__init__(orientation="P", unit="mm", format=(self.W, 200))
        self.set_margins(self.MARGIN, self.MARGIN, self.MARGIN)
        self.set_auto_page_break(auto=True, margin=self.MARGIN)
        self.add_page()

    def linea(self):
        self.set_draw_color(180, 180, 180)
        self.line(self.MARGIN, self.get_y(), self.W - self.MARGIN, self.get_y())
        self.ln(2)

    def fila(self, label: str, valor: str, bold_val: bool = False):
        self.set_font("Courier", "", 8)
        self.cell(38, 5, label, ln=0)
        if bold_val:
            self.set_font("Courier", "B", 8)
        self.cell(0, 5, valor, ln=1, align="R")

    def titulo_seccion(self, texto: str):
        self.set_font("Courier", "B", 8)
        self.cell(0, 5, texto, ln=1, align="C")
        self.ln(1)


def generar_recibo(pago_id: int) -> str:
    """Generate thermal receipt for a payment. Returns file path."""
    os.makedirs(RECEIPTS_DIR, exist_ok=True)

    pago = obtener_pago(pago_id)
    if not pago:
        raise ValueError(f"Pago {pago_id} no encontrado.")

    # Fetch related data
    conn = get_connection()
    cliente = conn.execute(
        "SELECT nombres, apellidos, cedula FROM clientes WHERE id = ?",
        (pago["cliente_id"],)
    ).fetchone()
    prestamo = conn.execute(
        "SELECT numero_prestamo, saldo_capital FROM prestamos WHERE id = ?",
        (pago["prestamo_id"],)
    ).fetchone()
    cuota_num = conn.execute(
        "SELECT numero_cuota FROM cuotas WHERE id = ?",
        (pago["cuota_id"],)
    ).fetchone()

    ag = _agencia_info()
    moneda = ag["moneda"]

    pdf = _Recibo()

    # ── Header ──
    pdf.set_font("Courier", "B", 10)
    pdf.cell(0, 6, ag["nombre"], ln=1, align="C")
    pdf.set_font("Courier", "", 8)
    pdf.cell(0, 4, ag["nit"], ln=1, align="C")
    pdf.cell(0, 4, ag["direccion"], ln=1, align="C")
    pdf.cell(0, 4, f"Tel: {ag['telefono']}", ln=1, align="C")
    pdf.ln(2)

    pdf.linea()
    pdf.titulo_seccion("COMPROBANTE DE PAGO")
    pdf.linea()

    # ── Loan / Client info ──
    pdf.fila("Recibo #:", pago["numero_recibo"])
    pdf.fila("Fecha:",    f"{pago['fecha_pago']}  {pago['hora_pago']}")
    pdf.fila("Cliente:",  f"{cliente['nombres']} {cliente['apellidos']}")
    pdf.fila("Cédula:",   cliente["cedula"])
    pdf.fila("Préstamo:", prestamo["numero_prestamo"])
    pdf.fila("Cuota #:",  str(cuota_num["numero_cuota"]))
    pdf.fila("Tipo:",     pago["tipo_pago"].replace("_", " "))

    pdf.linea()
    pdf.titulo_seccion("DETALLE DEL PAGO")
    pdf.linea()

    pdf.fila("Capital:",   _fmt(pago["monto_capital"],   moneda))
    pdf.fila("Intereses:", _fmt(pago["monto_intereses"], moneda))
    pdf.fila("Mora:",      _fmt(pago["monto_mora"],      moneda))
    pdf.linea()
    pdf.fila("TOTAL:",     _fmt(pago["monto_total"],     moneda), bold_val=True)
    pdf.fila("Método:",    pago["metodo_pago"])
    if pago.get("referencia_pago"):
        pdf.fila("Ref:",   pago["referencia_pago"])

    pdf.linea()
    pdf.fila("Saldo Capital:", _fmt(prestamo["saldo_capital"], moneda))
    pdf.linea()

    pdf.set_font("Courier", "I", 7)
    pdf.cell(0, 4, "Gracias por su pago puntual.", ln=1, align="C")
    pdf.cell(0, 4, datetime.now().strftime("%d/%m/%Y %H:%M"), ln=1, align="C")

    path = os.path.join(RECEIPTS_DIR, f"recibo_{pago['numero_recibo']}.pdf")
    pdf.output(path)
    return path


# ─────────────────────────────────────────────────────────────────
# Daily Cash Report (A4)
# ─────────────────────────────────────────────────────────────────

class _ReporteA4(FPDF):
    def header(self):
        ag = _agencia_info()
        self.set_font("Helvetica", "B", 13)
        self.cell(0, 8, ag["nombre"], ln=1, align="C")
        self.set_font("Helvetica", "", 9)
        self.cell(0, 5, f"{ag['nit']}  |  {ag['direccion']}  |  Tel: {ag['telefono']}", ln=1, align="C")
        self.set_draw_color(50, 80, 120)
        self.line(10, self.get_y() + 1, 200, self.get_y() + 1)
        self.ln(4)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 5, f"Página {self.page_no()}  —  Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                  align="C")


def generar_reporte_caja(fecha: str) -> str:
    """Generate A4 daily cash report. Returns file path."""
    os.makedirs(REPORTS_DIR, exist_ok=True)

    from controllers.reporte_controller import caja as get_caja
    reporte = get_caja(fecha)
    ag = _agencia_info()
    moneda = ag["moneda"]

    pdf = _ReporteA4(orientation="L", unit="mm", format="A4")
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, f"REPORTE DE CAJA DIARIA  —  {fecha}", ln=1, align="C")
    pdf.ln(4)

    # Summary
    t = reporte.get("totales", {})
    pdf.set_fill_color(30, 80, 150)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 10)
    resumen_cols = [("# Pagos", 30), ("Capital", 45), ("Intereses", 45),
                    ("Mora", 40), ("Total Cobrado", 50)]
    for label, w in resumen_cols:
        pdf.cell(w, 8, label, border=1, align="C")
    pdf.ln()

    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(220, 235, 255)
    pdf.set_font("Helvetica", "", 10)
    resumen_vals = [
        str(t.get("num_pagos", 0)),
        _fmt(t.get("total_capital", 0), moneda),
        _fmt(t.get("total_intereses", 0), moneda),
        _fmt(t.get("total_mora", 0), moneda),
        _fmt(t.get("total_cobrado", 0), moneda),
    ]
    for val, (_, w) in zip(resumen_vals, resumen_cols):
        pdf.cell(w, 8, val, border=1, align="C", fill=True)
    pdf.ln(10)

    # Payment detail table
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(50, 80, 120)
    pdf.set_text_color(255, 255, 255)
    cols = [
        ("Recibo",      35), ("Cliente",    60), ("Préstamo", 35),
        ("Capital",     35), ("Intereses",  35), ("Mora",     30),
        ("Total",       35), ("Método",     30),
    ]
    for label, w in cols:
        pdf.cell(w, 7, label, border=1, align="C", fill=True)
    pdf.ln()

    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(0, 0, 0)
    fill = False
    for i, pago in enumerate(reporte.get("pagos", [])):
        if i % 2 == 0:
            pdf.set_fill_color(240, 248, 255)
        else:
            pdf.set_fill_color(255, 255, 255)
        vals = [
            pago.get("numero_recibo", ""),
            pago.get("cliente_nombre", "")[:24],
            pago.get("numero_prestamo", ""),
            _fmt(pago.get("monto_capital", 0), ""),
            _fmt(pago.get("monto_intereses", 0), ""),
            _fmt(pago.get("monto_mora", 0), ""),
            _fmt(pago.get("monto_total", 0), ""),
            pago.get("metodo_pago", ""),
        ]
        for val, (_, w) in zip(vals, cols):
            pdf.cell(w, 6, str(val), border=1, fill=True)
        pdf.ln()

    path = os.path.join(REPORTS_DIR, f"reporte_caja_{fecha}.pdf")
    pdf.output(path)
    return path
