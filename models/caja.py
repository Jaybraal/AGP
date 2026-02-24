from typing import Optional, List
from datetime import date
from database.connection import get_connection


def obtener_caja_hoy() -> Optional[dict]:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM cajas WHERE fecha = ?",
        (date.today().isoformat(),),
    ).fetchone()
    return dict(row) if row else None


def abrir_caja(monto_apertura: float, notas: str = "") -> int:
    conn = get_connection()
    cur = conn.execute(
        """INSERT INTO cajas (fecha, monto_apertura, notas)
           VALUES (?, ?, ?)""",
        (date.today().isoformat(), monto_apertura, notas),
    )
    conn.commit()
    return cur.lastrowid


def cerrar_caja(caja_id: int, monto_cierre: float, notas: str = ""):
    conn = get_connection()
    from datetime import datetime
    conn.execute(
        """UPDATE cajas
           SET estado = 'CERRADA', monto_cierre = ?,
               hora_cierre = ?, notas = ?
           WHERE id = ?""",
        (
            monto_cierre,
            datetime.now().strftime("%H:%M:%S"),
            notas,
            caja_id,
        ),
    )
    conn.commit()


def sumar_cobro(caja_id: int, monto: float):
    conn = get_connection()
    conn.execute(
        "UPDATE cajas SET total_cobrado = total_cobrado + ? WHERE id = ?",
        (round(monto, 2), caja_id),
    )
    conn.commit()


def listar_cajas(limite: int = 30) -> List[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM cajas ORDER BY fecha DESC LIMIT ?",
        (limite,),
    ).fetchall()
    return [dict(r) for r in rows]


def obtener_caja(caja_id: int) -> Optional[dict]:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM cajas WHERE id = ?", (caja_id,)
    ).fetchone()
    return dict(row) if row else None
