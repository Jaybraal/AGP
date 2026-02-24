"""Global QSS stylesheet and color constants for PyQt6 UI."""

PRIMARY   = "#2563EB"
PRIMARY_H = "#1D4ED8"
SUCCESS   = "#16A34A"
SUCCESS_H = "#15803D"
DANGER    = "#DC2626"
DANGER_H  = "#B91C1C"
WARNING   = "#D97706"
SIDEBAR   = "#1E3A8A"
BG_MAIN   = "#F1F5F9"
BG_CARD   = "#FFFFFF"
BG_LIGHT  = "#EFF6FF"
TEXT      = "#0F172A"
TEXT_DIM  = "#64748B"
BORDER    = "#E2E8F0"

ESTADO_COLORS = {
    "ACTIVO":       PRIMARY,
    "AL_DIA":       SUCCESS,
    "VENCIDO":      DANGER,
    "CANCELADO":    "#94A3B8",
    "REFINANCIADO": WARNING,
}

QSS = f"""
/* ── Global ─────────────────────────────────── */
QWidget {{
    font-family: "Segoe UI", "SF Pro Display", Arial, sans-serif;
    font-size: 13px;
    color: {TEXT};
    background: transparent;
}}

QMainWindow {{
    background-color: {BG_MAIN};
}}

/* ── Scrollbar ───────────────────────────────── */
QScrollBar:vertical {{
    width: 8px; background: {BG_MAIN}; border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: #CBD5E1; border-radius: 4px; min-height: 30px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{
    height: 8px; background: {BG_MAIN}; border-radius: 4px;
}}
QScrollBar::handle:horizontal {{
    background: #CBD5E1; border-radius: 4px; min-width: 30px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

/* ── Card ────────────────────────────────────── */
QFrame#card {{
    background: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: 10px;
}}

/* ── Buttons ─────────────────────────────────── */
QPushButton {{
    background-color: {PRIMARY};
    color: white;
    border: none;
    border-radius: 8px;
    padding: 8px 18px;
    font-size: 13px;
    font-weight: 600;
}}
QPushButton:hover {{ background-color: {PRIMARY_H}; }}
QPushButton:pressed {{ background-color: #1E40AF; }}
QPushButton:disabled {{ background-color: #94A3B8; color: white; }}

QPushButton#btn_secondary {{
    background-color: {BG_CARD};
    color: {TEXT};
    border: 1px solid {BORDER};
}}
QPushButton#btn_secondary:hover {{ background-color: {BG_LIGHT}; }}

QPushButton#btn_success {{
    background-color: {SUCCESS};
}}
QPushButton#btn_success:hover {{ background-color: {SUCCESS_H}; }}

QPushButton#btn_danger {{
    background-color: {DANGER};
}}
QPushButton#btn_danger:hover {{ background-color: {DANGER_H}; }}

QPushButton#btn_warning {{
    background-color: {WARNING};
}}

/* ── Line edits ──────────────────────────────── */
QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
    background: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: 7px;
    padding: 6px 10px;
    font-size: 13px;
    color: {TEXT};
    selection-background-color: {PRIMARY};
}}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus,
QSpinBox:focus, QDoubleSpinBox:focus {{
    border: 2px solid {PRIMARY};
}}
QComboBox::drop-down {{
    border: none; width: 24px;
}}
QComboBox::down-arrow {{
    width: 12px; height: 12px;
}}
QComboBox QAbstractItemView {{
    background: {BG_CARD};
    border: 1px solid {BORDER};
    selection-background-color: {BG_LIGHT};
    selection-color: {TEXT};
    outline: none;
}}

/* ── Table ───────────────────────────────────── */
QTableWidget {{
    background: {BG_CARD};
    alternate-background-color: #F8FAFC;
    border: 1px solid {BORDER};
    border-radius: 8px;
    gridline-color: {BORDER};
    selection-background-color: {BG_LIGHT};
    selection-color: {TEXT};
    outline: none;
}}
QTableWidget::item {{ padding: 6px 10px; border: none; }}
QTableWidget::item:selected {{
    background: {BG_LIGHT};
    color: {TEXT};
}}
QHeaderView::section {{
    background: #F8FAFC;
    border: none;
    border-bottom: 2px solid {BORDER};
    border-right: 1px solid {BORDER};
    padding: 8px 10px;
    font-weight: 700;
    font-size: 12px;
    color: {TEXT_DIM};
}}
QHeaderView {{ background: #F8FAFC; }}

/* ── Tab widget ──────────────────────────────── */
QTabWidget::pane {{
    border: 1px solid {BORDER};
    border-radius: 8px;
    background: {BG_CARD};
    top: -1px;
}}
QTabBar::tab {{
    background: {BG_MAIN};
    border: 1px solid {BORDER};
    border-bottom: none;
    border-radius: 6px 6px 0 0;
    padding: 8px 18px;
    margin-right: 2px;
    color: {TEXT_DIM};
    font-size: 13px;
}}
QTabBar::tab:selected {{
    background: {BG_CARD};
    color: {PRIMARY};
    font-weight: 700;
    border-bottom: 2px solid {BG_CARD};
}}
QTabBar::tab:hover:!selected {{ background: {BG_LIGHT}; color: {TEXT}; }}

/* ── Radio buttons ───────────────────────────── */
QRadioButton {{ color: {TEXT}; spacing: 6px; background: transparent; }}
QRadioButton::indicator {{
    width: 16px; height: 16px; border-radius: 8px;
    border: 2px solid {BORDER};
    background: {BG_CARD};
}}
QRadioButton::indicator:checked {{
    background: {PRIMARY};
    border-color: {PRIMARY};
}}

/* ── Labels ──────────────────────────────────── */
QLabel {{ background: transparent; }}
QLabel#title {{ font-size: 22px; font-weight: 700; color: {TEXT}; }}
QLabel#subtitle {{ font-size: 11px; color: {TEXT_DIM}; }}
QLabel#section {{ font-size: 13px; font-weight: 700; color: {TEXT}; }}
QLabel#dim {{ color: {TEXT_DIM}; }}
QLabel#badge_success {{ color: {SUCCESS}; font-weight: 700; }}
QLabel#badge_danger {{ color: {DANGER}; font-weight: 700; }}
QLabel#badge_warning {{ color: {WARNING}; font-weight: 700; }}

/* ── Dialogs ─────────────────────────────────── */
QDialog {{
    background: {BG_MAIN};
}}

/* ── Splitter ────────────────────────────────── */
QSplitter::handle {{
    background: {BORDER};
    width: 1px;
    height: 1px;
}}
"""
