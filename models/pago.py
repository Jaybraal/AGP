from typing import Optional, List
from database.connection import get_connection
from database.seed import get_config, set_config
from datetime import date


def _numero_recibo() -> str:
    num = int(get_config("proximo_num_recibo"))
    set_config("proximo_num_recibo", str(num + 1))
    return f"REC-{date.today().year}-{num:05d}"


def registrar_pago(datos: dict) -> dict:
    """
    Atomically records a payment and updates cuota + prestamo + caja.
    datos must include:
        caja_id, cuota_id, prestamo_id, cliente_id, tipo_pago,
        monto_capital, monto_intereses, monto_mora, monto_total,
        metodo_pago, referencia_pago (optional), notas (optional)
    Returns the inserted payment dict with numero_recibo.
    """
    conn = get_connection()
    with conn:
        numero_recibo = _numero_recibo()
        datos["numero_recibo"] = numero_recibo

        # 1. Insert payment
        cur = conn.execute(
            """INSERT INTO pagos
               (caja_id, cuota_id, prestamo_id, cliente_id, tipo_pago,
                monto_capital, monto_intereses, monto_mora, monto_total,
                numero_recibo, metodo_pago, referencia_pago, notas)
               VALUES (:caja_id, :cuota_id, :prestamo_id, :cliente_id, :tipo_pago,
                       :monto_capital, :monto_intereses, :monto_mora, :monto_total,
                       :numero_recibo, :metodo_pago, :referencia_pago, :notas)""",
            datos,
        )
        pago_id = cur.lastrowid

        # 2. Update cuota
        conn.execute(
            """UPDATE cuotas SET
               capital_pagado    = capital_pagado    + :cap,
               intereses_pagados = intereses_pagados + :int,
               mora_pagada       = mora_pagada       + :mora,
               estado = CASE
                   WHEN (capital_pagado + :cap) >= capital
                     AND (intereses_pagados + :int) >= intereses
                   THEN 'PAGADA'
                   WHEN (capital_pagado + :cap) > 0
                   THEN 'PARCIAL'
                   ELSE estado
               END,
               fecha_pago = CASE
                   WHEN estado != 'PAGADA' AND (capital_pagado + :cap) >= capital
                     AND (intereses_pagados + :int) >= intereses
                   THEN date('now', 'localtime')
                   ELSE fecha_pago
               END
               WHERE id = :cuota_id""",
            {
                "cap": datos["monto_capital"],
                "int": datos["monto_intereses"],
                "mora": datos["monto_mora"],
                "cuota_id": datos["cuota_id"],
            },
        )

        # 3. Update loan balance (CASE protects against negative saldo)
        conn.execute(
            """UPDATE prestamos
               SET saldo_capital = CASE
                   WHEN saldo_capital - ? < 0 THEN 0
                   ELSE saldo_capital - ?
               END
               WHERE id = ?""",
            (datos["monto_capital"], datos["monto_capital"], datos["prestamo_id"]),
        )

        # 4. Check if loan is fully paid
        saldo = conn.execute(
            "SELECT saldo_capital FROM prestamos WHERE id = ?",
            (datos["prestamo_id"],),
        ).fetchone()[0]
        if saldo <= 0.01:
            conn.execute(
                "UPDATE prestamos SET estado = 'CANCELADO' WHERE id = ?",
                (datos["prestamo_id"],),
            )

        # 5. Update caja
        conn.execute(
            "UPDATE cajas SET total_cobrado = total_cobrado + ? WHERE id = ?",
            (datos["monto_total"], datos["caja_id"]),
        )

    return {**datos, "id": pago_id}


def anular_pago(pago_id: int, motivo: str):
    """
    Voids a payment and reverses all related updates:
    - cuota: restores capital_pagado, intereses_pagados, mora_pagada, estado
    - prestamos: restores saldo_capital, reverts CANCELADO if needed
    - cajas: restores total_cobrado
    """
    conn = get_connection()
    with conn:
        # Fetch the payment to get the amounts
        pago = conn.execute(
            "SELECT * FROM pagos WHERE id = ? AND anulado = 0",
            (pago_id,),
        ).fetchone()
        if not pago:
            raise ValueError("Pago no encontrado o ya fue anulado.")
        pago = dict(pago)

        # 1. Mark payment as void
        conn.execute(
            """UPDATE pagos SET anulado = 1, motivo_anulacion = ?,
               fecha_anulacion = date('now', 'localtime')
               WHERE id = ?""",
            (motivo, pago_id),
        )

        # 2. Reverse cuota updates
        conn.execute(
            """UPDATE cuotas SET
               capital_pagado    = MAX(0, capital_pagado    - :cap),
               intereses_pagados = MAX(0, intereses_pagados - :int),
               mora_pagada       = MAX(0, mora_pagada       - :mora),
               estado = CASE
                   WHEN (capital_pagado - :cap) <= 0
                     AND (intereses_pagados - :int) <= 0
                   THEN 'PENDIENTE'
                   WHEN (capital_pagado - :cap) > 0
                   THEN 'PARCIAL'
                   ELSE estado
               END,
               fecha_pago = CASE
                   WHEN (capital_pagado - :cap) <= 0 THEN NULL
                   ELSE fecha_pago
               END
               WHERE id = :cuota_id""",
            {
                "cap": pago["monto_capital"],
                "int": pago["monto_intereses"],
                "mora": pago["monto_mora"],
                "cuota_id": pago["cuota_id"],
            },
        )

        # 3. Restore loan balance
        conn.execute(
            "UPDATE prestamos SET saldo_capital = saldo_capital + ? WHERE id = ?",
            (pago["monto_capital"], pago["prestamo_id"]),
        )

        # 4. If loan was CANCELADO and now has balance, restore to ACTIVO
        saldo = conn.execute(
            "SELECT saldo_capital, estado FROM prestamos WHERE id = ?",
            (pago["prestamo_id"],),
        ).fetchone()
        if saldo and saldo["estado"] == "CANCELADO" and saldo["saldo_capital"] > 0.01:
            conn.execute(
                "UPDATE prestamos SET estado = 'ACTIVO' WHERE id = ?",
                (pago["prestamo_id"],),
            )

        # 5. Restore caja total_cobrado
        conn.execute(
            "UPDATE cajas SET total_cobrado = MAX(0, total_cobrado - ?) WHERE id = ?",
            (pago["monto_total"], pago["caja_id"]),
        )


def registrar_pagos_cancelacion(lista_pagos: List[dict]) -> List[dict]:
    """
    Registers multiple payments in a SINGLE atomic transaction.
    Used for full loan cancellation: all cuotas paid or none.
    """
    from database.seed import get_config, set_config
    from datetime import date as _date

    conn = get_connection()
    resultados = []

    with conn:
        for datos in lista_pagos:
            # Generate receipt number inside the transaction
            num = int(get_config("proximo_num_recibo"))
            set_config("proximo_num_recibo", str(num + 1))
            datos["numero_recibo"] = f"REC-{_date.today().year}-{num:05d}"

            cur = conn.execute(
                """INSERT INTO pagos
                   (caja_id, cuota_id, prestamo_id, cliente_id, tipo_pago,
                    monto_capital, monto_intereses, monto_mora, monto_total,
                    numero_recibo, metodo_pago, referencia_pago, notas)
                   VALUES (:caja_id, :cuota_id, :prestamo_id, :cliente_id, :tipo_pago,
                           :monto_capital, :monto_intereses, :monto_mora, :monto_total,
                           :numero_recibo, :metodo_pago, :referencia_pago, :notas)""",
                datos,
            )
            pago_id = cur.lastrowid

            # Update cuota
            conn.execute(
                """UPDATE cuotas SET
                   capital_pagado    = capital_pagado    + :cap,
                   intereses_pagados = intereses_pagados + :int,
                   mora_pagada       = mora_pagada       + :mora,
                   estado = 'PAGADA',
                   fecha_pago = date('now', 'localtime')
                   WHERE id = :cuota_id""",
                {
                    "cap":      datos["monto_capital"],
                    "int":      datos["monto_intereses"],
                    "mora":     datos["monto_mora"],
                    "cuota_id": datos["cuota_id"],
                },
            )

            # Update caja
            conn.execute(
                "UPDATE cajas SET total_cobrado = total_cobrado + ? WHERE id = ?",
                (datos["monto_total"], datos["caja_id"]),
            )

            resultados.append({**datos, "id": pago_id})

        # After all cuotas: set loan saldo = 0 and estado = CANCELADO
        if lista_pagos:
            prestamo_id = lista_pagos[0]["prestamo_id"]
            conn.execute(
                "UPDATE prestamos SET saldo_capital = 0, estado = 'CANCELADO' WHERE id = ?",
                (prestamo_id,),
            )

    return resultados


def listar_pagos_prestamo(prestamo_id: int) -> List[dict]:
    conn = get_connection()
    rows = conn.execute(
        """SELECT p.*, c.numero_cuota
           FROM pagos p
           JOIN cuotas c ON c.id = p.cuota_id
           WHERE p.prestamo_id = ? AND p.anulado = 0
           ORDER BY p.fecha_pago DESC, p.hora_pago DESC""",
        (prestamo_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def listar_pagos_caja(caja_id: int) -> List[dict]:
    conn = get_connection()
    rows = conn.execute(
        """SELECT p.*,
                  c.nombres || ' ' || c.apellidos AS cliente_nombre,
                  pr.numero_prestamo
           FROM pagos p
           JOIN clientes c  ON c.id  = p.cliente_id
           JOIN prestamos pr ON pr.id = p.prestamo_id
           WHERE p.caja_id = ? AND p.anulado = 0
           ORDER BY p.hora_pago DESC""",
        (caja_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def obtener_pago(pago_id: int) -> Optional[dict]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM pagos WHERE id = ?", (pago_id,)).fetchone()
    return dict(row) if row else None
