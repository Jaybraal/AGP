"""Tests for late fee (mora) calculator."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import date
from services.mora_calculator import (
    calcular_mora_cuota,
    calcular_mora_prestamo,
    calcular_cancelacion_total,
)


TASA = 0.005   # 0.5% per day
GRACIA = 3


def test_sin_mora_dentro_gracia():
    """No late fee within grace period."""
    info = calcular_mora_cuota(
        saldo_pendiente=10_000,
        fecha_vencimiento=date(2026, 2, 1),
        fecha_calculo=date(2026, 2, 4),   # day 3 of grace
        tasa_mora_diaria=TASA,
        dias_gracia=GRACIA,
    )
    assert info["dias_mora"] == 0
    assert info["monto_mora"] == 0.0


def test_mora_un_dia():
    """1 day past grace → 1 day of mora."""
    info = calcular_mora_cuota(
        saldo_pendiente=10_000,
        fecha_vencimiento=date(2026, 2, 1),
        fecha_calculo=date(2026, 2, 5),   # day 4 = 1 day past grace
        tasa_mora_diaria=TASA,
        dias_gracia=GRACIA,
    )
    assert info["dias_mora"] == 1
    assert info["monto_mora"] == round(10_000 * TASA * 1, 2)


def test_mora_diez_dias():
    """10 days of mora calculated correctly."""
    info = calcular_mora_cuota(
        saldo_pendiente=20_000,
        fecha_vencimiento=date(2026, 1, 1),
        fecha_calculo=date(2026, 1, 14),  # 13 days after due, 10 after grace
        tasa_mora_diaria=TASA,
        dias_gracia=GRACIA,
    )
    assert info["dias_mora"] == 10
    assert info["monto_mora"] == round(20_000 * TASA * 10, 2)


def test_mora_saldo_cero():
    """No mora when installment is already fully paid."""
    info = calcular_mora_cuota(
        saldo_pendiente=0.0,
        fecha_vencimiento=date(2026, 1, 1),
        fecha_calculo=date(2026, 3, 1),
        tasa_mora_diaria=TASA,
        dias_gracia=GRACIA,
    )
    assert info["monto_mora"] == 0.0


def _make_cuota(num, fecha_str, total, capital, intereses):
    return {
        "id": num,
        "numero_cuota": num,
        "fecha_vencimiento": fecha_str,
        "cuota_total": total,
        "capital": capital,
        "intereses": intereses,
        "capital_pagado": 0.0,
        "intereses_pagados": 0.0,
        "mora_pagada": 0.0,
    }


def test_mora_multiple_cuotas():
    """Mora is calculated per-installment for overdue loans."""
    cuotas = [
        _make_cuota(1, "2026-01-01", 5000, 4500, 500),
        _make_cuota(2, "2026-02-01", 5000, 4550, 450),
    ]
    resultado = calcular_mora_prestamo(cuotas, date(2026, 2, 20), TASA, GRACIA)
    # Cuota 1 is overdue from Jan 1 (beyond grace)
    assert resultado[0]["dias_mora"] > 0
    # Cuota 2: Feb 1 + 3 grace = Feb 4; Feb 20 = 16 days
    assert resultado[1]["dias_mora"] == 16


def test_cancelacion_total():
    """Total payoff includes capital + pending interest + mora."""
    cuotas = [
        _make_cuota(1, "2026-01-01", 5000, 4500, 500),
        _make_cuota(2, "2026-02-01", 5000, 4550, 450),
    ]
    resultado = calcular_cancelacion_total(
        saldo_capital=9050,
        cuotas_pendientes=cuotas,
        fecha_calculo=date(2026, 2, 20),
        tasa_mora_diaria=TASA,
        dias_gracia=GRACIA,
    )
    assert resultado["capital"] == 9050
    assert resultado["total"] > 9050
    assert resultado["mora_total"] > 0
