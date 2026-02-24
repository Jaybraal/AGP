from typing import Optional, List
from datetime import date, timedelta
from database.connection import get_connection


def reporte_caja_dia(fecha: str) -> dict:
    """Full daily cash report for a given date (YYYY-MM-DD)."""
    conn = get_connection()
    caja = conn.execute(
        "SELECT * FROM cajas WHERE fecha = ?", (fecha,)
    ).fetchone()

    if not caja:
        return {"fecha": fecha, "caja": None, "pagos": [], "totales": {}}

    pagos = conn.execute(
        """SELECT p.*,
                  c.nombres || ' ' || c.apellidos AS cliente_nombre,
                  pr.numero_prestamo
           FROM pagos p
           JOIN clientes c   ON c.id  = p.cliente_id
           JOIN prestamos pr ON pr.id = p.prestamo_id
           WHERE p.caja_id = ? AND p.anulado = 0
           ORDER BY p.hora_pago""",
        (caja["id"],),
    ).fetchall()

    totales = {
        "total_capital":   sum(r["monto_capital"]   for r in pagos),
        "total_intereses": sum(r["monto_intereses"] for r in pagos),
        "total_mora":      sum(r["monto_mora"]      for r in pagos),
        "total_cobrado":   sum(r["monto_total"]     for r in pagos),
        "num_pagos":       len(pagos),
    }

    return {
        "fecha": fecha,
        "caja":  dict(caja),
        "pagos": [dict(r) for r in pagos],
        "totales": totales,
    }


def reporte_mora(fecha_base: Optional[str] = None) -> List[dict]:
    """Returns all overdue loans with days in arrears."""
    if not fecha_base:
        fecha_base = date.today().isoformat()

    conn = get_connection()
    rows = conn.execute(
        """SELECT
               p.id AS prestamo_id,
               p.numero_prestamo,
               p.saldo_capital,
               c.nombres || ' ' || c.apellidos AS cliente_nombre,
               c.cedula,
               c.telefono_principal,
               MIN(cu.fecha_vencimiento) AS primera_cuota_vencida,
               COUNT(cu.id)             AS cuotas_vencidas,
               SUM(cu.cuota_total - cu.capital_pagado - cu.intereses_pagados) AS monto_pendiente
           FROM prestamos p
           JOIN clientes c ON c.id = p.cliente_id
           JOIN cuotas cu ON cu.prestamo_id = p.id
           WHERE p.estado IN ('ACTIVO', 'VENCIDO')
             AND cu.estado IN ('PENDIENTE', 'PARCIAL', 'VENCIDA')
             AND cu.fecha_vencimiento < ?
           GROUP BY p.id
           ORDER BY primera_cuota_vencida""",
        (fecha_base,),
    ).fetchall()
    return [dict(r) for r in rows]


def reporte_proyeccion(dias: int = 30) -> List[dict]:
    """Returns expected collections for the next `dias` days."""
    hoy = date.today()
    fin  = hoy + timedelta(days=dias)
    conn = get_connection()
    rows = conn.execute(
        """SELECT
               cu.fecha_vencimiento,
               COUNT(cu.id)            AS num_cuotas,
               SUM(cu.cuota_total - cu.capital_pagado - cu.intereses_pagados) AS monto_esperado,
               SUM(cu.capital - cu.capital_pagado)             AS capital_esperado,
               SUM(cu.intereses - cu.intereses_pagados)        AS intereses_esperados
           FROM cuotas cu
           JOIN prestamos p ON p.id = cu.prestamo_id
           WHERE cu.fecha_vencimiento BETWEEN ? AND ?
             AND cu.estado IN ('PENDIENTE', 'PARCIAL')
             AND p.estado IN ('ACTIVO', 'AL_DIA')
           GROUP BY cu.fecha_vencimiento
           ORDER BY cu.fecha_vencimiento""",
        (hoy.isoformat(), fin.isoformat()),
    ).fetchall()
    return [dict(r) for r in rows]


def resumen_dashboard() -> dict:
    """Quick numbers for the main dashboard."""
    conn = get_connection()
    hoy = date.today().isoformat()

    activos = conn.execute(
        "SELECT COUNT(*) FROM prestamos WHERE estado IN ('ACTIVO', 'AL_DIA')"
    ).fetchone()[0]

    vencidos = conn.execute(
        """SELECT COUNT(DISTINCT prestamo_id) FROM cuotas
           WHERE fecha_vencimiento < ? AND estado IN ('PENDIENTE', 'VENCIDA', 'PARCIAL')""",
        (hoy,),
    ).fetchone()[0]

    cobrado_hoy = conn.execute(
        """SELECT COALESCE(SUM(p.monto_total), 0)
           FROM pagos p JOIN cajas ca ON ca.id = p.caja_id
           WHERE ca.fecha = ? AND p.anulado = 0""",
        (hoy,),
    ).fetchone()[0]

    clientes_total = conn.execute(
        "SELECT COUNT(*) FROM clientes WHERE activo = 1"
    ).fetchone()[0]

    cartera_total = conn.execute(
        "SELECT COALESCE(SUM(saldo_capital), 0) FROM prestamos WHERE estado IN ('ACTIVO', 'AL_DIA')"
    ).fetchone()[0]

    return {
        "prestamos_activos": activos,
        "prestamos_vencidos": vencidos,
        "cobrado_hoy": round(cobrado_hoy, 2),
        "clientes_total": clientes_total,
        "cartera_total": round(cartera_total, 2),
    }
