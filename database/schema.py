from database.connection import get_connection

DDL = """
CREATE TABLE IF NOT EXISTS clientes (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    cedula              TEXT NOT NULL UNIQUE,
    tipo_documento      TEXT NOT NULL DEFAULT 'Cédula',
    nombres             TEXT NOT NULL,
    apellidos           TEXT NOT NULL,
    fecha_nacimiento    TEXT,
    telefono_principal  TEXT NOT NULL,
    telefono_secundario TEXT,
    email               TEXT,
    direccion           TEXT,
    barrio              TEXT,
    ciudad              TEXT NOT NULL DEFAULT '',
    calificacion        TEXT NOT NULL DEFAULT 'NUEVO',
    ocupacion           TEXT,
    empresa             TEXT,
    ingresos_mensuales  REAL DEFAULT 0,
    activo              INTEGER NOT NULL DEFAULT 1,
    fecha_registro      TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    notas               TEXT
);
CREATE INDEX IF NOT EXISTS idx_clientes_cedula  ON clientes(cedula);
CREATE INDEX IF NOT EXISTS idx_clientes_nombre  ON clientes(nombres, apellidos);

CREATE TABLE IF NOT EXISTS prestamos (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id          INTEGER NOT NULL REFERENCES clientes(id),
    numero_prestamo     TEXT NOT NULL UNIQUE,
    monto_principal     REAL NOT NULL,
    tasa_interes        REAL NOT NULL,
    tipo_tasa           TEXT NOT NULL DEFAULT 'MENSUAL',
    plazo               INTEGER NOT NULL,
    frecuencia_pago     TEXT NOT NULL,
    tipo_amortizacion   TEXT NOT NULL DEFAULT 'FRANCES',
    fecha_inicio        TEXT NOT NULL,
    fecha_vencimiento   TEXT NOT NULL,
    cuota_base          REAL NOT NULL,
    total_intereses     REAL NOT NULL,
    total_a_pagar       REAL NOT NULL,
    estado              TEXT NOT NULL DEFAULT 'ACTIVO',
    saldo_capital       REAL NOT NULL,
    desembolsado        INTEGER NOT NULL DEFAULT 1,
    fecha_desembolso    TEXT,
    fecha_creacion      TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    notas               TEXT
);
CREATE INDEX IF NOT EXISTS idx_prestamos_cliente ON prestamos(cliente_id);
CREATE INDEX IF NOT EXISTS idx_prestamos_estado  ON prestamos(estado);
CREATE INDEX IF NOT EXISTS idx_prestamos_numero  ON prestamos(numero_prestamo);

CREATE TABLE IF NOT EXISTS garantes_prestamo (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    prestamo_id     INTEGER NOT NULL REFERENCES prestamos(id) ON DELETE CASCADE,
    cliente_id      INTEGER NOT NULL REFERENCES clientes(id),
    relacion        TEXT,
    fecha_registro  TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    UNIQUE(prestamo_id, cliente_id)
);

CREATE TABLE IF NOT EXISTS cuotas (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    prestamo_id         INTEGER NOT NULL REFERENCES prestamos(id) ON DELETE CASCADE,
    numero_cuota        INTEGER NOT NULL,
    fecha_vencimiento   TEXT NOT NULL,
    cuota_total         REAL NOT NULL,
    capital             REAL NOT NULL,
    intereses           REAL NOT NULL,
    saldo_restante      REAL NOT NULL,
    estado              TEXT NOT NULL DEFAULT 'PENDIENTE',
    capital_pagado      REAL NOT NULL DEFAULT 0,
    intereses_pagados   REAL NOT NULL DEFAULT 0,
    mora_acumulada      REAL NOT NULL DEFAULT 0,
    mora_pagada         REAL NOT NULL DEFAULT 0,
    fecha_pago          TEXT,
    UNIQUE(prestamo_id, numero_cuota)
);
CREATE INDEX IF NOT EXISTS idx_cuotas_prestamo    ON cuotas(prestamo_id);
CREATE INDEX IF NOT EXISTS idx_cuotas_vencimiento ON cuotas(fecha_vencimiento);
CREATE INDEX IF NOT EXISTS idx_cuotas_estado      ON cuotas(estado);

CREATE TABLE IF NOT EXISTS cajas (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha               TEXT NOT NULL UNIQUE,
    monto_apertura      REAL NOT NULL DEFAULT 0,
    monto_cierre        REAL,
    total_cobrado       REAL NOT NULL DEFAULT 0,
    total_desembolsado  REAL NOT NULL DEFAULT 0,
    estado              TEXT NOT NULL DEFAULT 'ABIERTA',
    hora_apertura       TEXT NOT NULL DEFAULT (time('now', 'localtime')),
    hora_cierre         TEXT,
    notas               TEXT
);

CREATE TABLE IF NOT EXISTS pagos (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    caja_id             INTEGER NOT NULL REFERENCES cajas(id),
    cuota_id            INTEGER NOT NULL REFERENCES cuotas(id),
    prestamo_id         INTEGER NOT NULL REFERENCES prestamos(id),
    cliente_id          INTEGER NOT NULL REFERENCES clientes(id),
    tipo_pago           TEXT NOT NULL,
    monto_capital       REAL NOT NULL DEFAULT 0,
    monto_intereses     REAL NOT NULL DEFAULT 0,
    monto_mora          REAL NOT NULL DEFAULT 0,
    monto_total         REAL NOT NULL,
    numero_recibo       TEXT NOT NULL UNIQUE,
    metodo_pago         TEXT NOT NULL DEFAULT 'EFECTIVO',
    referencia_pago     TEXT,
    fecha_pago          TEXT NOT NULL DEFAULT (date('now', 'localtime')),
    hora_pago           TEXT NOT NULL DEFAULT (time('now', 'localtime')),
    anulado             INTEGER NOT NULL DEFAULT 0,
    fecha_anulacion     TEXT,
    motivo_anulacion    TEXT,
    notas               TEXT
);
CREATE INDEX IF NOT EXISTS idx_pagos_prestamo ON pagos(prestamo_id);
CREATE INDEX IF NOT EXISTS idx_pagos_caja     ON pagos(caja_id);
CREATE INDEX IF NOT EXISTS idx_pagos_fecha    ON pagos(fecha_pago);

CREATE TABLE IF NOT EXISTS configuracion (
    clave   TEXT PRIMARY KEY,
    valor   TEXT NOT NULL,
    tipo    TEXT NOT NULL DEFAULT 'TEXT'
);
"""


MIGRACIONES = [
    # v1 → v2: tasa sugerida por cliente y campo autorización en pagos
    "ALTER TABLE clientes ADD COLUMN tasa_sugerida REAL DEFAULT 0",
    "ALTER TABLE clientes ADD COLUMN tipo_tasa_sugerida TEXT DEFAULT 'MENSUAL'",
    "ALTER TABLE pagos ADD COLUMN autorizacion_terminal TEXT",
    "ALTER TABLE pagos ADD COLUMN terminal_estado TEXT",
]


def crear_tablas():
    conn = get_connection()
    conn.executescript(DDL)
    conn.commit()
    _aplicar_migraciones(conn)


def _aplicar_migraciones(conn):
    """Safe migrations: execute each ALTER TABLE, ignore if column already exists."""
    for sql in MIGRACIONES:
        try:
            conn.execute(sql)
            conn.commit()
        except Exception:
            pass  # Column already exists — harmless
