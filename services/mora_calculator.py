"""
Late fee (mora) calculation service.
Pure math — no database access.
"""

from datetime import date, timedelta
from typing import List


def calcular_mora_cuota(
    saldo_pendiente: float,
    fecha_vencimiento: date,
    fecha_calculo: date,
    tasa_mora_diaria: float,   # decimal, e.g. 0.005 = 0.5%
    dias_gracia: int = 3,
) -> dict:
    """
    Calculate late fee for a single installment.

    Returns:
        dias_mora           – days past grace period
        monto_mora          – amount owed in late fees
        fecha_limite        – last date without penalty
    """
    fecha_limite = fecha_vencimiento + timedelta(days=dias_gracia)

    if saldo_pendiente <= 0 or fecha_calculo <= fecha_limite:
        return {"dias_mora": 0, "monto_mora": 0.0, "fecha_limite": fecha_limite}

    dias_mora  = (fecha_calculo - fecha_limite).days
    monto_mora = round(saldo_pendiente * tasa_mora_diaria * dias_mora, 2)

    return {"dias_mora": dias_mora, "monto_mora": monto_mora, "fecha_limite": fecha_limite}


def calcular_mora_prestamo(
    cuotas_pendientes: List[dict],
    fecha_calculo: date,
    tasa_mora_diaria: float,
    dias_gracia: int = 3,
) -> List[dict]:
    """
    Apply mora calculation to all pending installments of a loan.

    Each dict in cuotas_pendientes must have keys:
        id, numero_cuota, fecha_vencimiento (str YYYY-MM-DD),
        cuota_total, capital_pagado, intereses_pagados, mora_pagada

    Returns the same list with added keys:
        pendiente           – unpaid portion of this installment
        dias_mora
        monto_mora_calculado
        total_a_cobrar      – pendiente + mora
    """
    resultado = []
    for c in cuotas_pendientes:
        _fv = str(c["fecha_vencimiento"] or "")
        fecha_vcto = date.fromisoformat(_fv[:10]) if len(_fv) >= 10 else date.today()
        pendiente  = round(
            c["cuota_total"] - c["capital_pagado"] - c["intereses_pagados"], 2
        )
        pendiente = max(0.0, pendiente)

        info = calcular_mora_cuota(
            saldo_pendiente=pendiente,
            fecha_vencimiento=fecha_vcto,
            fecha_calculo=fecha_calculo,
            tasa_mora_diaria=tasa_mora_diaria,
            dias_gracia=dias_gracia,
        )
        resultado.append({
            **c,
            "pendiente":             pendiente,
            "dias_mora":             info["dias_mora"],
            "monto_mora_calculado":  info["monto_mora"],
            "total_a_cobrar":        round(pendiente + info["monto_mora"], 2),
        })
    return resultado


def calcular_cancelacion_total(
    saldo_capital: float,
    cuotas_pendientes: List[dict],
    fecha_calculo: date,
    tasa_mora_diaria: float,
    dias_gracia: int = 3,
) -> dict:
    """
    Compute the full payoff amount for early total cancellation.
    """
    cuotas = calcular_mora_prestamo(
        cuotas_pendientes, fecha_calculo, tasa_mora_diaria, dias_gracia
    )
    intereses_pend = round(
        sum(max(0, c["intereses"] - c["intereses_pagados"]) for c in cuotas), 2
    )
    mora_total = round(sum(c["monto_mora_calculado"] for c in cuotas), 2)

    return {
        "capital":             round(saldo_capital, 2),
        "intereses_pendientes": intereses_pend,
        "mora_total":          mora_total,
        "total":               round(saldo_capital + intereses_pend + mora_total, 2),
    }
