from typing import Optional, List
"""Business logic for client management."""

from models.cliente import (
    crear_cliente, actualizar_cliente, obtener_cliente,
    buscar_clientes, listar_clientes,
)


_REQUERIDOS = ["cedula", "nombres", "apellidos", "telefono_principal"]

_DEFAULTS = {
    "tipo_documento": "Cédula",
    "fecha_nacimiento": "",
    "telefono_secundario": "",
    "email": "",
    "direccion": "",
    "barrio": "",
    "ciudad": "",
    "calificacion": "NUEVO",
    "ocupacion": "",
    "empresa": "",
    "ingresos_mensuales": 0.0,
    "tasa_sugerida": 5.0,
    "tipo_tasa_sugerida": "MENSUAL",
    "notas": "",
}


def _validar(datos: dict):
    for campo in _REQUERIDOS:
        if not str(datos.get(campo, "")).strip():
            raise ValueError(f"El campo '{campo}' es obligatorio.")


def _normalizar(datos: dict) -> dict:
    resultado = {**_DEFAULTS, **datos}
    resultado["nombres"]   = resultado["nombres"].strip().upper()
    resultado["apellidos"] = resultado["apellidos"].strip().upper()
    resultado["cedula"]    = resultado["cedula"].strip()
    return resultado


def guardar_cliente(datos: dict, cliente_id: Optional[int] = None) -> int:
    """Create or update a client. Returns client id."""
    datos = _normalizar(datos)
    _validar(datos)
    if cliente_id:
        actualizar_cliente(cliente_id, datos)
        return cliente_id
    return crear_cliente(datos)


def buscar(termino: str) -> List[dict]:
    return buscar_clientes(termino.strip())


def todos() -> List[dict]:
    return listar_clientes()


def obtener(cliente_id: int) -> Optional[dict]:
    return obtener_cliente(cliente_id)
