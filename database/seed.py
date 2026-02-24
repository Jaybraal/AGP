from database.connection import get_connection

DEFAULTS = [
    ("nombre_agencia",       "Agencia de Préstamos AGP",  "TEXT"),
    ("nit_agencia",          "000-000-000-0",             "TEXT"),
    ("direccion_agencia",    "Calle Principal #1",        "TEXT"),
    ("telefono_agencia",     "000-000-0000",              "TEXT"),
    ("email_agencia",        "",                          "TEXT"),
    ("tasa_mora_diaria",     "0.5",                       "REAL"),   # 0.5% por día
    ("dias_gracia",          "3",                         "INTEGER"),
    ("moneda_simbolo",       "RD$",                       "TEXT"),
    ("proximo_num_prestamo", "1",                         "INTEGER"),
    ("proximo_num_recibo",   "1",                         "INTEGER"),
    ("logo_path",            "assets/logo.png",           "TEXT"),
    # Terminal de pago
    ("terminal_habilitado",  "0",                         "INTEGER"),
    ("terminal_puerto",      "COM1",                      "TEXT"),   # COM1-COM9 o /dev/ttyUSB0
    ("terminal_baudrate",    "9600",                      "INTEGER"),
    ("terminal_modo",        "DISPLAY",                   "TEXT"),   # DISPLAY o SERIAL
    ("tasa_default",         "5.0",                       "REAL"),   # tasa sugerida global
    ("tipo_tasa_default",    "MENSUAL",                   "TEXT"),
]


def insertar_defaults():
    conn = get_connection()
    conn.executemany(
        "INSERT OR IGNORE INTO configuracion (clave, valor, tipo) VALUES (?, ?, ?)",
        DEFAULTS
    )
    conn.commit()


def get_config(clave: str) -> str:
    conn = get_connection()
    row = conn.execute(
        "SELECT valor FROM configuracion WHERE clave = ?", (clave,)
    ).fetchone()
    return row["valor"] if row else ""


def set_config(clave: str, valor: str):
    conn = get_connection()
    conn.execute(
        "UPDATE configuracion SET valor = ? WHERE clave = ?", (valor, clave)
    )
    conn.commit()


def get_all_config() -> dict:
    conn = get_connection()
    rows = conn.execute("SELECT clave, valor FROM configuracion").fetchall()
    return {r["clave"]: r["valor"] for r in rows}
