from typing import Optional, List
"""Business logic for loan creation and management."""

from datetime import date
from services.amortizacion import calcular_prestamo
from models.prestamo import (
    numero_prestamo_nuevo, crear_prestamo,
    obtener_prestamo, listar_prestamos, buscar_prestamos,
    obtener_cuotas, obtener_proxima_cuota,
)


def previsualizar(datos: dict) -> dict:
    """
    Calculate amortization without saving.
    datos: monto, tasa, tipo_tasa, plazo, frecuencia_pago,
           tipo_amortizacion, fecha_inicio (str YYYY-MM-DD)
    Returns full result from services/amortizacion.calcular_prestamo
    """
    return calcular_prestamo(
        monto=float(datos["monto"]),
        tasa=float(datos["tasa"]),
        tipo_tasa=datos["tipo_tasa"],
        plazo=int(datos["plazo"]),
        frecuencia_pago=datos["frecuencia_pago"],
        tipo_amortizacion=datos["tipo_amortizacion"],
        fecha_inicio=date.fromisoformat(datos["fecha_inicio"]) if datos.get("fecha_inicio") else date.today(),
    )


def crear(cliente_id: int, datos: dict) -> int:
    """
    Full loan creation: validate → calculate → persist atomically.
    datos: same as previsualizar plus optional notas.
    Returns new loan id.
    """
    if float(datos.get("monto", 0)) <= 0:
        raise ValueError("El monto debe ser mayor a cero.")
    if float(datos.get("tasa", 0)) <= 0:
        raise ValueError("La tasa de interés debe ser mayor a cero.")
    if int(datos.get("plazo", 0)) <= 0:
        raise ValueError("El plazo debe ser mayor a cero.")

    resultado = previsualizar(datos)

    numero = numero_prestamo_nuevo()
    hoy = date.today().isoformat()

    prestamo_datos = {
        "cliente_id":       cliente_id,
        "numero_prestamo":  numero,
        "monto_principal":  float(datos["monto"]),
        "tasa_interes":     float(datos["tasa"]),
        "tipo_tasa":        datos["tipo_tasa"],
        "plazo":            int(datos["plazo"]),
        "frecuencia_pago":  datos["frecuencia_pago"],
        "tipo_amortizacion": datos["tipo_amortizacion"],
        "fecha_inicio":     datos["fecha_inicio"] if datos.get("fecha_inicio") else date.today().isoformat(),
        "fecha_vencimiento": resultado["fecha_vencimiento"].isoformat(),
        "cuota_base":       resultado["cuota_base"],
        "total_intereses":  resultado["total_intereses"],
        "total_a_pagar":    resultado["total_a_pagar"],
        "saldo_capital":    float(datos["monto"]),
        "fecha_desembolso": hoy,
        "notas":            datos.get("notas", ""),
    }

    return crear_prestamo(prestamo_datos, resultado["tabla"])


def obtener(prestamo_id: int) -> Optional[dict]:
    return obtener_prestamo(prestamo_id)


def listar(estado: Optional[str] = None, cliente_id: Optional[int] = None) -> List[dict]:
    return listar_prestamos(estado=estado, cliente_id=cliente_id)


def buscar(termino: str) -> List[dict]:
    return buscar_prestamos(termino.strip())


def cuotas(prestamo_id: int, solo_pendientes: bool = False) -> List[dict]:
    return obtener_cuotas(prestamo_id, solo_pendientes)


def proxima_cuota(prestamo_id: int) -> Optional[dict]:
    return obtener_proxima_cuota(prestamo_id)
