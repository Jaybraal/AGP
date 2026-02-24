from typing import Optional, List
from datetime import date
from database.connection import get_connection
from database.seed import get_config, set_config


def _siguiente_numero(clave: str, prefijo: str) -> str:
    conn = get_connection()
    with conn:
        num = int(get_config(clave))
        set_config(clave, str(num + 1))
    return f"{prefijo}-{date.today().year}-{num:05d}"


def numero_prestamo_nuevo() -> str:
    return _siguiente_numero("proximo_num_prestamo", "PREST")


def crear_prestamo(datos: dict, tabla_cuotas: list) -> int:
    """
    Inserts loan and its full amortization schedule atomically.
    datos: dict with all prestamo fields (except id, fecha_creacion).
    tabla_cuotas: list of FilaCuota from services/amortizacion.py
    """
    conn = get_connection()
    with conn:
        cur = conn.execute(
            """INSERT INTO prestamos
               (cliente_id, numero_prestamo, monto_principal, tasa_interes, tipo_tasa,
                plazo, frecuencia_pago, tipo_amortizacion, fecha_inicio, fecha_vencimiento,
                cuota_base, total_intereses, total_a_pagar, saldo_capital,
                fecha_desembolso, notas)
               VALUES (:cliente_id, :numero_prestamo, :monto_principal, :tasa_interes,
                       :tipo_tasa, :plazo, :frecuencia_pago, :tipo_amortizacion,
                       :fecha_inicio, :fecha_vencimiento, :cuota_base, :total_intereses,
                       :total_a_pagar, :saldo_capital, :fecha_desembolso, :notas)""",
            datos,
        )
        prestamo_id = cur.lastrowid

        conn.executemany(
            """INSERT INTO cuotas
               (prestamo_id, numero_cuota, fecha_vencimiento, cuota_total,
                capital, intereses, saldo_restante)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            [
                (
                    prestamo_id,
                    c.numero_cuota,
                    c.fecha_vencimiento.isoformat(),
                    c.cuota_total,
                    c.capital,
                    c.intereses,
                    c.saldo_restante,
                )
                for c in tabla_cuotas
            ],
        )
    return prestamo_id


def obtener_prestamo(prestamo_id: int) -> Optional[dict]:
    conn = get_connection()
    row = conn.execute(
        """SELECT p.*, c.nombres, c.apellidos, c.cedula
           FROM prestamos p
           JOIN clientes c ON c.id = p.cliente_id
           WHERE p.id = ?""",
        (prestamo_id,),
    ).fetchone()
    return dict(row) if row else None


def listar_prestamos(
    estado: Optional[str] = None,
    cliente_id: Optional[int] = None,
    limite: int = 200,
) -> List[dict]:
    conn = get_connection()
    filtros = []
    params = []
    if estado:
        filtros.append("p.estado = ?")
        params.append(estado)
    if cliente_id:
        filtros.append("p.cliente_id = ?")
        params.append(cliente_id)
    where = ("WHERE " + " AND ".join(filtros)) if filtros else ""
    rows = conn.execute(
        f"""SELECT p.*, c.nombres, c.apellidos, c.cedula
            FROM prestamos p
            JOIN clientes c ON c.id = p.cliente_id
            {where}
            ORDER BY p.fecha_creacion DESC
            LIMIT ?""",
        params + [limite],
    ).fetchall()
    return [dict(r) for r in rows]


def buscar_prestamos(termino: str) -> List[dict]:
    """Search by loan number, client name or cedula."""
    conn = get_connection()
    t = f"%{termino}%"
    rows = conn.execute(
        """SELECT p.*, c.nombres, c.apellidos, c.cedula
           FROM prestamos p
           JOIN clientes c ON c.id = p.cliente_id
           WHERE p.numero_prestamo LIKE ?
              OR c.nombres LIKE ? OR c.apellidos LIKE ? OR c.cedula LIKE ?
           ORDER BY p.fecha_creacion DESC
           LIMIT 50""",
        (t, t, t, t),
    ).fetchall()
    return [dict(r) for r in rows]


def obtener_cuotas(prestamo_id: int, solo_pendientes: bool = False) -> List[dict]:
    conn = get_connection()
    where = "AND estado IN ('PENDIENTE', 'PARCIAL', 'VENCIDA')" if solo_pendientes else ""
    rows = conn.execute(
        f"""SELECT * FROM cuotas
            WHERE prestamo_id = ? {where}
            ORDER BY numero_cuota""",
        (prestamo_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def obtener_proxima_cuota(prestamo_id: int) -> Optional[dict]:
    conn = get_connection()
    row = conn.execute(
        """SELECT * FROM cuotas
           WHERE prestamo_id = ? AND estado IN ('PENDIENTE', 'PARCIAL', 'VENCIDA')
           ORDER BY numero_cuota LIMIT 1""",
        (prestamo_id,),
    ).fetchone()
    return dict(row) if row else None


def actualizar_estado_prestamo(prestamo_id: int, estado: str):
    conn = get_connection()
    conn.execute(
        "UPDATE prestamos SET estado = ? WHERE id = ?",
        (estado, prestamo_id),
    )
    conn.commit()


def actualizar_saldo_capital(prestamo_id: int, nuevo_saldo: float):
    conn = get_connection()
    conn.execute(
        "UPDATE prestamos SET saldo_capital = ? WHERE id = ?",
        (round(nuevo_saldo, 2), prestamo_id),
    )
    conn.commit()
