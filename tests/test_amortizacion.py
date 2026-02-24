"""Tests for amortization service."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import date
from services.amortizacion import calcular_prestamo, convertir_tasa


def test_frances_suma_capital():
    """Total capital in amortization table must equal principal."""
    r = calcular_prestamo(
        monto=100_000, tasa=5.0, tipo_tasa="MENSUAL",
        plazo=12, frecuencia_pago="MENSUAL",
        tipo_amortizacion="FRANCES",
        fecha_inicio=date(2026, 1, 1),
    )
    total_capital = sum(f.capital for f in r["tabla"])
    assert abs(total_capital - 100_000) < 0.10, f"Capital sum mismatch: {total_capital}"


def test_frances_saldo_final_cero():
    """Balance after last payment must be zero."""
    r = calcular_prestamo(
        monto=50_000, tasa=3.0, tipo_tasa="MENSUAL",
        plazo=6, frecuencia_pago="MENSUAL",
        tipo_amortizacion="FRANCES",
        fecha_inicio=date(2026, 2, 1),
    )
    assert r["tabla"][-1].saldo_restante == 0.0


def test_frances_cuota_fija():
    """All installments except the last must have the same payment amount."""
    r = calcular_prestamo(
        monto=100_000, tasa=2.0, tipo_tasa="MENSUAL",
        plazo=10, frecuencia_pago="MENSUAL",
        tipo_amortizacion="FRANCES",
        fecha_inicio=date(2026, 1, 1),
    )
    cuotas = [f.cuota_total for f in r["tabla"][:-1]]
    assert max(cuotas) - min(cuotas) < 0.02, "Cuotas deben ser prácticamente iguales"


def test_solo_interes_capital_al_final():
    """Interest-only: only last period has capital > 0."""
    r = calcular_prestamo(
        monto=200_000, tasa=1.5, tipo_tasa="MENSUAL",
        plazo=6, frecuencia_pago="MENSUAL",
        tipo_amortizacion="SOLO_INTERES",
        fecha_inicio=date(2026, 1, 1),
    )
    for f in r["tabla"][:-1]:
        assert f.capital == 0.0
    assert r["tabla"][-1].capital == 200_000


def test_tasa_anual_a_mensual():
    """Annual rate of 12% should convert to ~0.9489% monthly (compound)."""
    tasa = convertir_tasa(0.12, "ANUAL", "MENSUAL")
    assert abs(tasa - 0.009489) < 0.0001, f"Expected ~0.009489, got {tasa}"


def test_total_intereses_positivo():
    """Total interest must be positive for non-zero rate."""
    r = calcular_prestamo(
        monto=10_000, tasa=4.0, tipo_tasa="MENSUAL",
        plazo=3, frecuencia_pago="MENSUAL",
        tipo_amortizacion="FRANCES",
        fecha_inicio=date(2026, 1, 1),
    )
    assert r["total_intereses"] > 0
    assert r["total_a_pagar"] > 10_000


def test_numero_cuotas():
    """Table length must equal plazo."""
    for plazo in [6, 12, 24]:
        r = calcular_prestamo(
            monto=100_000, tasa=2.0, tipo_tasa="MENSUAL",
            plazo=plazo, frecuencia_pago="MENSUAL",
            tipo_amortizacion="FRANCES",
            fecha_inicio=date(2026, 1, 1),
        )
        assert len(r["tabla"]) == plazo
