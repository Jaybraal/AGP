import os
import sys

# En modo bundle (PyInstaller) los datos del usuario van a
# ~/Library/Application Support/AGP para que sean escribibles.
# En modo desarrollo se usa la carpeta del proyecto normalmente.
if getattr(sys, 'frozen', False):
    _APP_SUPPORT = os.path.join(
        os.path.expanduser('~'), 'Library', 'Application Support', 'AGP'
    )
    BASE_DIR   = _APP_SUPPORT
    ASSETS_DIR = os.path.join(sys._MEIPASS, 'assets')
else:
    BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
    ASSETS_DIR = os.path.join(BASE_DIR, 'assets')

DB_PATH      = os.path.join(BASE_DIR, "data", "prestamos.db")
LOGO_PATH    = os.path.join(ASSETS_DIR, "logo.png")
RECEIPTS_DIR = os.path.join(BASE_DIR, "data", "recibos")
REPORTS_DIR  = os.path.join(BASE_DIR, "data", "reportes")

# Ventana principal
APP_TITLE   = "AGP — Sistema de Gestión de Préstamos"
APP_VERSION = "1.0"
APP_WIDTH   = 1280
APP_HEIGHT  = 800
APP_MIN_W   = 1100
APP_MIN_H   = 650

# CustomTkinter
CTK_APPEARANCE  = "light"
CTK_COLOR_THEME = "blue"

# ── Paleta de colores — Blanco + Azul Moderno ─────────────────────────────────
COLOR_PRIMARY     = "#2563EB"   # azul principal
COLOR_PRIMARY_H   = "#3B82F6"   # hover del azul
COLOR_PRIMARY_DIM = "#1D4ED8"   # azul oscuro (fondo activo sidebar)

COLOR_SUCCESS = "#16A34A"
COLOR_DANGER  = "#DC2626"
COLOR_WARNING = "#D97706"

COLOR_SIDEBAR     = "#1E3A8A"   # azul marino sidebar
COLOR_BG_MAIN     = "#F1F5F9"   # fondo principal (gris muy claro)
COLOR_BG_CARD     = "#FFFFFF"   # tarjetas blancas
COLOR_BG_ELEVATED = "#EFF6FF"   # azul muy suave (hover)

COLOR_TEXT     = "#0F172A"      # texto oscuro principal
COLOR_TEXT_DIM = "#64748B"      # texto secundario
COLOR_BORDER   = "#E2E8F0"      # bordes sutiles claros

# Semáforo de estado de préstamo
ESTADO_COLORS = {
    "ACTIVO":       COLOR_PRIMARY,
    "AL_DIA":       COLOR_SUCCESS,
    "VENCIDO":      COLOR_DANGER,
    "CANCELADO":    "#94A3B8",
    "REFINANCIADO": COLOR_WARNING,
}

# Opciones de dominio
FRECUENCIAS    = ["DIARIO", "SEMANAL", "QUINCENAL", "MENSUAL"]
TIPOS_TASA     = ["DIARIA", "SEMANAL", "QUINCENAL", "MENSUAL", "ANUAL"]
TIPOS_AMORT    = ["FRANCES", "SOLO_INTERES"]
TIPOS_DOC      = ["Cédula", "Pasaporte", "RNC", "Otro"]
CALIFICACIONES = ["NUEVO", "BUENO", "REGULAR", "MALO"]
METODOS_PAGO   = ["EFECTIVO", "TRANSFERENCIA", "CHEQUE"]
