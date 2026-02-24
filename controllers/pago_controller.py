from typing import Optional, List
"""
Payment processing controller — the most critical module.
Orchestrates: mora calc → payment → cuota update → loan balance → caja.
"""

from datetime import date
from database.seed import get_config
from services.mora_calculator import (
    calcular_mora_cuota, calcular_cancelacion_total,
)
from models.prestamo import obtener_prestamo, obtener_cuotas, obtener_proxima_cuota
from models.pago import registrar_pago, listar_pagos_prestamo, listar_pagos_caja
from controllers.caja_controller import caja_activa


def _tasa_mora() -> float:
    return float(get_config("tasa_mora_diaria")) / 100.0


def _dias_gracia() -> int:
    return int(get_config("dias_gracia"))


def calcular_cuota_con_mora(cuota: dict, hoy: Optional[date] = None) -> dict:
    """
    Enrich a cuota dict with live mora calculation for today.
    Returns cuota + pendiente, dias_mora, monto_mora, total_a_cobrar.
    """
    if hoy is None:
        hoy = date.today()

    pendiente = round(
        cuota["cuota_total"] - cuota["capital_pagado"] - cuota["intereses_pagados"], 2
    )
    pendiente = max(0.0, pendiente)

    mora_info = calcular_mora_cuota(
        saldo_pendiente=pendiente,
        fecha_vencimiento=date.fromisoformat(cuota["fecha_vencimiento"]),
        fecha_calculo=hoy,
        tasa_mora_diaria=_tasa_mora(),
        dias_gracia=_dias_gracia(),
    )

    return {
        **cuota,
        "pendiente":    pendiente,
        "dias_mora":    mora_info["dias_mora"],
        "monto_mora":   mora_info["monto_mora"],
        "total_a_cobrar": round(pendiente + mora_info["monto_mora"], 2),
    }


def calcular_pago_cuota_normal(prestamo_id: int) -> dict:
    """
    Returns the breakdown for paying the next installment.
    Raises if no active caja or no pending cuota.
    """
    caja = caja_activa()
    if not caja:
        raise ValueError("No hay una sesión de caja abierta. Abra la caja primero.")

    cuota = obtener_proxima_cuota(prestamo_id)
    if not cuota:
        raise ValueError("Este préstamo no tiene cuotas pendientes.")

    return {
        "caja":  caja,
        "cuota": calcular_cuota_con_mora(cuota),
    }


def calcular_cancelacion(prestamo_id: int) -> dict:
    """Returns full payoff breakdown for early cancellation."""
    caja = caja_activa()
    if not caja:
        raise ValueError("No hay una sesión de caja abierta.")

    prestamo = obtener_prestamo(prestamo_id)
    if not prestamo:
        raise ValueError("Préstamo no encontrado.")

    cuotas_pend = obtener_cuotas(prestamo_id, solo_pendientes=True)
    resultado = calcular_cancelacion_total(
        saldo_capital=prestamo["saldo_capital"],
        cuotas_pendientes=cuotas_pend,
        fecha_calculo=date.today(),
        tasa_mora_diaria=_tasa_mora(),
        dias_gracia=_dias_gracia(),
    )
    return {"caja": caja, "prestamo": prestamo, "cancelacion": resultado}


def cobrar_cuota_normal(
    prestamo_id: int,
    cuota_id: int,
    metodo_pago: str = "EFECTIVO",
    referencia_pago: str = "",
    notas: str = "",
) -> dict:
    """
    Process a standard installment payment.
    Returns the registered payment dict (with numero_recibo).
    """
    caja = caja_activa()
    if not caja:
        raise ValueError("No hay sesión de caja abierta.")

    # Re-fetch cuota to get fresh state
    from database.connection import get_connection
    conn = get_connection()
    cuota_row = conn.execute(
        "SELECT * FROM cuotas WHERE id = ? AND prestamo_id = ?",
        (cuota_id, prestamo_id),
    ).fetchone()
    if not cuota_row:
        raise ValueError("Cuota no encontrada.")

    cuota = calcular_cuota_con_mora(dict(cuota_row))
    prestamo = obtener_prestamo(prestamo_id)

    # Allocation: mora first, then intereses, then capital
    pendiente = cuota["pendiente"]
    interes_pendiente = round(cuota["intereses"] - cuota["intereses_pagados"], 2)
    capital_pendiente = round(cuota["capital"]   - cuota["capital_pagado"],   2)

    datos_pago = {
        "caja_id":        caja["id"],
        "cuota_id":       cuota_id,
        "prestamo_id":    prestamo_id,
        "cliente_id":     prestamo["cliente_id"],
        "tipo_pago":      "CUOTA_NORMAL",
        "monto_capital":  round(capital_pendiente, 2),
        "monto_intereses": round(interes_pendiente, 2),
        "monto_mora":     round(cuota["monto_mora"], 2),
        "monto_total":    round(capital_pendiente + interes_pendiente + cuota["monto_mora"], 2),
        "metodo_pago":    metodo_pago,
        "referencia_pago": referencia_pago,
        "notas":          notas,
    }
    return registrar_pago(datos_pago)


def cobrar_cancelacion_total(
    prestamo_id: int,
    metodo_pago: str = "EFECTIVO",
    referencia_pago: str = "",
    notas: str = "",
) -> List[dict]:
    """
    Pay off all remaining installments atomically — all or nothing.
    Returns list of payment dicts (one per pending cuota).
    """
    caja = caja_activa()
    if not caja:
        raise ValueError("No hay sesión de caja abierta.")

    prestamo = obtener_prestamo(prestamo_id)
    cuotas_pend = obtener_cuotas(prestamo_id, solo_pendientes=True)

    # Build all payment data before touching the DB
    lista_pagos = []
    for cuota in cuotas_pend:
        c = calcular_cuota_con_mora(cuota)
        if c["total_a_cobrar"] <= 0:
            continue
        interes_p = round(cuota["intereses"] - cuota["intereses_pagados"], 2)
        capital_p = round(cuota["capital"]   - cuota["capital_pagado"],   2)
        lista_pagos.append({
            "caja_id":         caja["id"],
            "cuota_id":        cuota["id"],
            "prestamo_id":     prestamo_id,
            "cliente_id":      prestamo["cliente_id"],
            "tipo_pago":       "CANCELACION_TOTAL",
            "monto_capital":   capital_p,
            "monto_intereses": interes_p,
            "monto_mora":      c["monto_mora"],
            "monto_total":     round(capital_p + interes_p + c["monto_mora"], 2),
            "metodo_pago":     metodo_pago,
            "referencia_pago": referencia_pago,
            "notas":           notas,
        })

    # Execute all payments in a single atomic transaction
    from models.pago import registrar_pagos_cancelacion
    return registrar_pagos_cancelacion(lista_pagos)


def historial_pagos_prestamo(prestamo_id: int) -> List[dict]:
    return listar_pagos_prestamo(prestamo_id)


def pagos_de_caja(caja_id: int) -> List[dict]:
    return listar_pagos_caja(caja_id)
