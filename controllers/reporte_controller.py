from typing import Optional, List
"""Controller for report data assembly."""

from datetime import date
from models.reporte import (
    reporte_caja_dia, reporte_mora, reporte_proyeccion, resumen_dashboard,
)


def dashboard() -> dict:
    return resumen_dashboard()


def caja(fecha: Optional[str] = None) -> dict:
    if not fecha:
        fecha = date.today().isoformat()
    return reporte_caja_dia(fecha)


def mora() -> List[dict]:
    return reporte_mora()


def proyeccion(dias: int = 30) -> List[dict]:
    return reporte_proyeccion(dias)
