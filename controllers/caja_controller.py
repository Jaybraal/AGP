from typing import Optional, List
"""Business logic for daily cash session management."""

from models.caja import (
    obtener_caja_hoy, abrir_caja, cerrar_caja,
    listar_cajas, obtener_caja,
)


def caja_activa() -> Optional[dict]:
    """Return today's open cash session or None."""
    caja = obtener_caja_hoy()
    if caja and caja["estado"] == "ABIERTA":
        return caja
    return None


def abrir(monto_apertura: float, notas: str = "") -> int:
    existente = obtener_caja_hoy()
    if existente:
        raise ValueError("Ya existe una sesión de caja para hoy.")
    if monto_apertura < 0:
        raise ValueError("El monto de apertura no puede ser negativo.")
    return abrir_caja(monto_apertura, notas)


def cerrar(caja_id: int, monto_cierre: float, notas: str = ""):
    caja = obtener_caja(caja_id)
    if not caja:
        raise ValueError("Sesión de caja no encontrada.")
    if caja["estado"] == "CERRADA":
        raise ValueError("La caja ya está cerrada.")
    cerrar_caja(caja_id, monto_cierre, notas)


def historial(limite: int = 30) -> List[dict]:
    return listar_cajas(limite)
