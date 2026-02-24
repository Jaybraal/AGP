"""
Amortization calculation service.
Pure math — no database access. Fully unit-testable.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from typing import List


@dataclass
class FilaCuota:
    numero_cuota:     int
    fecha_vencimiento: date
    cuota_total:      float
    capital:          float
    intereses:        float
    saldo_restante:   float


# Days per period type (for rate conversion)
_DIAS_PERIODO = {
    "DIARIA":    1,
    "SEMANAL":   7,
    "QUINCENAL": 15,
    "MENSUAL":   30,
    "ANUAL":     360,
}


def calcular_siguiente_fecha(base: date, frecuencia: str, n: int) -> date:
    """
    Return the due date for period n (1-indexed) from base date.
    frecuencia: DIARIO | SEMANAL | QUINCENAL | MENSUAL
    """
    if frecuencia == "DIARIO":
        return base + timedelta(days=n)
    elif frecuencia == "SEMANAL":
        return base + timedelta(weeks=n)
    elif frecuencia == "QUINCENAL":
        return base + timedelta(days=n * 15)
    elif frecuencia == "MENSUAL":
        return base + relativedelta(months=n)
    raise ValueError(f"Frecuencia no reconocida: {frecuencia}")


def convertir_tasa(tasa_decimal: float, tipo_tasa: str, frecuencia_pago: str) -> float:
    """
    Convert a rate expressed in tipo_tasa terms to the payment-frequency rate.
    Uses compound-interest conversion:
        r_dest = (1 + r_orig)^(dias_dest/dias_orig) - 1
    """
    dias_orig = _DIAS_PERIODO[tipo_tasa]
    dias_dest = _DIAS_PERIODO[frecuencia_pago]
    return (1 + tasa_decimal) ** (dias_dest / dias_orig) - 1


def _tabla_frances(monto: float, i: float, n: int,
                   fecha_inicio: date, frecuencia: str) -> List[FilaCuota]:
    """French (constant payment) amortization."""
    if i == 0:
        cuota = round(monto / n, 2)
    else:
        cuota = round(monto * (i * (1 + i) ** n) / ((1 + i) ** n - 1), 2)

    tabla = []
    saldo = monto

    for k in range(1, n + 1):
        interes  = round(saldo * i, 2)
        capital  = round(cuota - interes, 2)
        cuota_k  = cuota

        if k == n:                          # last: fix rounding drift
            capital = round(saldo, 2)
            cuota_k = round(capital + interes, 2)

        saldo = round(saldo - capital, 2)
        fecha = calcular_siguiente_fecha(fecha_inicio, frecuencia, k)

        tabla.append(FilaCuota(
            numero_cuota=k,
            fecha_vencimiento=fecha,
            cuota_total=cuota_k,
            capital=capital,
            intereses=interes,
            saldo_restante=max(saldo, 0.0),
        ))

    return tabla


def _tabla_solo_interes(monto: float, i: float, n: int,
                        fecha_inicio: date, frecuencia: str) -> List[FilaCuota]:
    """Interest-only loan: borrower pays interest each period, principal on last."""
    tabla = []

    for k in range(1, n + 1):
        interes = round(monto * i, 2)
        if k < n:
            capital = 0.0
            cuota_k = interes
            saldo   = monto
        else:
            capital = monto
            cuota_k = round(monto + interes, 2)
            saldo   = 0.0

        fecha = calcular_siguiente_fecha(fecha_inicio, frecuencia, k)

        tabla.append(FilaCuota(
            numero_cuota=k,
            fecha_vencimiento=fecha,
            cuota_total=cuota_k,
            capital=capital,
            intereses=interes,
            saldo_restante=saldo,
        ))

    return tabla


def calcular_prestamo(
    monto: float,
    tasa: float,            # percentage, e.g. 5.0 means 5%
    tipo_tasa: str,         # DIARIA|SEMANAL|QUINCENAL|MENSUAL|ANUAL
    plazo: int,             # number of payment periods
    frecuencia_pago: str,   # DIARIO|SEMANAL|QUINCENAL|MENSUAL
    tipo_amortizacion: str, # FRANCES|SOLO_INTERES
    fecha_inicio: date,
) -> dict:
    """
    Top-level entry point.
    Returns:
        cuota_base      – payment amount for period 1 (fixed for FRANCES)
        total_intereses – sum of all interest charges
        total_a_pagar   – monto + total_intereses
        fecha_vencimiento – last payment date
        tasa_periodo    – effective rate per payment period (decimal)
        tabla           – list[FilaCuota]
    """
    tasa_decimal = tasa / 100.0
    tasa_periodo = convertir_tasa(tasa_decimal, tipo_tasa, frecuencia_pago)

    if tipo_amortizacion == "FRANCES":
        tabla = _tabla_frances(monto, tasa_periodo, plazo, fecha_inicio, frecuencia_pago)
    elif tipo_amortizacion == "SOLO_INTERES":
        tabla = _tabla_solo_interes(monto, tasa_periodo, plazo, fecha_inicio, frecuencia_pago)
    else:
        raise ValueError(f"Tipo de amortización no soportado: {tipo_amortizacion}")

    total_intereses = round(sum(f.intereses for f in tabla), 2)
    total_a_pagar   = round(monto + total_intereses, 2)

    return {
        "cuota_base":       tabla[0].cuota_total,
        "total_intereses":  total_intereses,
        "total_a_pagar":    total_a_pagar,
        "fecha_vencimiento": tabla[-1].fecha_vencimiento,
        "tasa_periodo":     tasa_periodo,
        "tabla":            tabla,
    }
