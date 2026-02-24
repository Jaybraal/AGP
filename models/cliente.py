from typing import Optional, List
from database.connection import get_connection


def crear_cliente(datos: dict) -> int:
    conn = get_connection()
    cur = conn.execute(
        """INSERT INTO clientes
           (cedula, tipo_documento, nombres, apellidos, fecha_nacimiento,
            telefono_principal, telefono_secundario, email,
            direccion, barrio, ciudad, calificacion,
            ocupacion, empresa, ingresos_mensuales,
            tasa_sugerida, tipo_tasa_sugerida, notas)
           VALUES (:cedula, :tipo_documento, :nombres, :apellidos, :fecha_nacimiento,
                   :telefono_principal, :telefono_secundario, :email,
                   :direccion, :barrio, :ciudad, :calificacion,
                   :ocupacion, :empresa, :ingresos_mensuales,
                   :tasa_sugerida, :tipo_tasa_sugerida, :notas)""",
        datos,
    )
    conn.commit()
    return cur.lastrowid


def actualizar_cliente(cliente_id: int, datos: dict):
    datos["id"] = cliente_id
    conn = get_connection()
    conn.execute(
        """UPDATE clientes SET
           cedula=:cedula, tipo_documento=:tipo_documento,
           nombres=:nombres, apellidos=:apellidos,
           fecha_nacimiento=:fecha_nacimiento,
           telefono_principal=:telefono_principal,
           telefono_secundario=:telefono_secundario, email=:email,
           direccion=:direccion, barrio=:barrio, ciudad=:ciudad,
           calificacion=:calificacion, ocupacion=:ocupacion,
           empresa=:empresa, ingresos_mensuales=:ingresos_mensuales,
           tasa_sugerida=:tasa_sugerida,
           tipo_tasa_sugerida=:tipo_tasa_sugerida,
           notas=:notas
           WHERE id=:id""",
        datos,
    )
    conn.commit()


def obtener_cliente(cliente_id: int) -> Optional[dict]:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM clientes WHERE id = ?", (cliente_id,)
    ).fetchone()
    return dict(row) if row else None


def buscar_clientes(termino: str) -> List[dict]:
    conn = get_connection()
    t = f"%{termino}%"
    rows = conn.execute(
        """SELECT * FROM clientes
           WHERE activo = 1
             AND (nombres LIKE ? OR apellidos LIKE ?
                  OR cedula LIKE ? OR telefono_principal LIKE ?)
           ORDER BY apellidos, nombres
           LIMIT 100""",
        (t, t, t, t),
    ).fetchall()
    return [dict(r) for r in rows]


def listar_clientes(solo_activos: bool = True) -> List[dict]:
    conn = get_connection()
    where = "WHERE activo = 1" if solo_activos else ""
    rows = conn.execute(
        f"SELECT * FROM clientes {where} ORDER BY apellidos, nombres"
    ).fetchall()
    return [dict(r) for r in rows]


def nombre_completo(cliente: dict) -> str:
    return f"{cliente['nombres']} {cliente['apellidos']}"


def agregar_garante(prestamo_id: int, cliente_id: int, relacion: str = ""):
    conn = get_connection()
    conn.execute(
        """INSERT OR IGNORE INTO garantes_prestamo (prestamo_id, cliente_id, relacion)
           VALUES (?, ?, ?)""",
        (prestamo_id, cliente_id, relacion),
    )
    conn.commit()


def obtener_garantes(prestamo_id: int) -> List[dict]:
    conn = get_connection()
    rows = conn.execute(
        """SELECT g.*, c.nombres, c.apellidos, c.cedula, c.telefono_principal
           FROM garantes_prestamo g
           JOIN clientes c ON c.id = g.cliente_id
           WHERE g.prestamo_id = ?""",
        (prestamo_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def eliminar_garante(garante_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM garantes_prestamo WHERE id = ?", (garante_id,))
    conn.commit()


def actualizar_calificacion(cliente_id: int, calificacion: str):
    conn = get_connection()
    conn.execute(
        "UPDATE clientes SET calificacion = ? WHERE id = ?",
        (calificacion, cliente_id),
    )
    conn.commit()
