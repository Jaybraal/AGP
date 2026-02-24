"""Dashboard principal — PyQt6 con QThread para carga asíncrona."""

from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame,
)
from PyQt6.QtCore import Qt

from controllers.reporte_controller import dashboard as get_dashboard
from database.seed import get_config
from views.components.worker import Worker

_MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]
_DIAS = [
    "lunes", "martes", "miércoles", "jueves",
    "viernes", "sábado", "domingo",
]

# Light tint backgrounds for metric card accent
_TINTS = {
    "#2563EB": "#DBEAFE",
    "#DC2626": "#FEE2E2",
    "#16A34A": "#DCFCE7",
    "#D97706": "#FEF3C7",
    "#0F172A": "#F1F5F9",
}


def _fecha_es() -> str:
    now = datetime.now()
    return f"{_DIAS[now.weekday()].capitalize()}, {now.day} de {_MESES[now.month - 1]} de {now.year}"


# ── Metric card ────────────────────────────────────────────────────────────────

class _Metrica(QFrame):

    def __init__(self, icon: str, titulo: str, color: str, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self._build(icon, titulo, color)

    def _build(self, icon: str, titulo: str, color: str):
        tint = _TINTS.get(color, "#F1F5F9")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 16, 0)
        layout.setSpacing(0)

        # Left accent bar
        bar = QFrame()
        bar.setFixedWidth(4)
        bar.setStyleSheet(f"background: {color}; border-radius: 2px;")
        layout.addWidget(bar)

        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(16, 14, 0, 14)
        inner_layout.setSpacing(6)

        # Icon + title row
        top_row = QWidget()
        top_row.setStyleSheet("background: transparent;")
        top_layout = QHBoxLayout(top_row)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(8)

        icon_box = QLabel(icon)
        icon_box.setFixedSize(36, 36)
        icon_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_box.setStyleSheet(
            f"background: {tint}; border-radius: 8px; font-size: 16px;"
        )
        top_layout.addWidget(icon_box)

        lbl_title = QLabel(f" {titulo}")
        lbl_title.setObjectName("dim")
        top_layout.addWidget(lbl_title)
        top_layout.addStretch()

        inner_layout.addWidget(top_row)

        self._lbl_valor = QLabel("—")
        self._lbl_valor.setStyleSheet(
            "font-size: 28px; font-weight: 700; color: #0F172A; background: transparent;"
        )
        inner_layout.addWidget(self._lbl_valor)

        layout.addWidget(inner, 1)

    def set_valor(self, text: str):
        self._lbl_valor.setText(text)


# ── Dashboard ──────────────────────────────────────────────────────────────────

class Dashboard(QWidget):

    def __init__(self, navegar=None, parent=None):
        super().__init__(parent)
        self._navegar = navegar
        self._moneda  = get_config("moneda_simbolo") or "RD$"
        self._cards: dict[str, _Metrica] = {}
        self._worker: Worker | None = None
        self._build()
        self.refrescar()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(0)

        # ── Header ─────────────────────────────────────────────
        hdr = QWidget()
        hdr.setStyleSheet("background: transparent;")
        hdr_layout = QHBoxLayout(hdr)
        hdr_layout.setContentsMargins(0, 0, 0, 0)

        left = QWidget()
        left.setStyleSheet("background: transparent;")
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(2)

        lbl_title = QLabel("Panel Principal")
        lbl_title.setObjectName("title")
        left_layout.addWidget(lbl_title)

        self._lbl_fecha = QLabel("")
        self._lbl_fecha.setObjectName("subtitle")
        left_layout.addWidget(self._lbl_fecha)

        hdr_layout.addWidget(left, 1)

        btn_cobrar = QPushButton("💵  Cobrar Cuota")
        btn_cobrar.setObjectName("btn_success")
        btn_cobrar.setFixedHeight(44)
        btn_cobrar.clicked.connect(lambda: self._navegar("caja") if self._navegar else None)
        hdr_layout.addWidget(btn_cobrar)

        layout.addWidget(hdr)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #E2E8F0;")
        layout.addWidget(sep)
        layout.addSpacing(20)

        # ── Row 1 — 3 metrics ──────────────────────────────────
        row1 = QWidget()
        row1.setStyleSheet("background: transparent;")
        row1_layout = QHBoxLayout(row1)
        row1_layout.setContentsMargins(0, 0, 0, 0)
        row1_layout.setSpacing(12)

        for key, icon, titulo, color in [
            ("activos",  "📋", "Préstamos Activos", "#2563EB"),
            ("mora",     "⚠️",  "En Mora",           "#DC2626"),
            ("cobrado",  "💰", "Cobrado Hoy",       "#16A34A"),
        ]:
            c = _Metrica(icon=icon, titulo=titulo, color=color)
            row1_layout.addWidget(c)
            self._cards[key] = c

        layout.addWidget(row1)
        layout.addSpacing(12)

        # ── Row 2 — 2 metrics ──────────────────────────────────
        row2 = QWidget()
        row2.setStyleSheet("background: transparent;")
        row2_layout = QHBoxLayout(row2)
        row2_layout.setContentsMargins(0, 0, 0, 0)
        row2_layout.setSpacing(12)

        for key, icon, titulo, color in [
            ("clientes", "👤", "Clientes Total",  "#0F172A"),
            ("cartera",  "💼", "Cartera Total",   "#D97706"),
        ]:
            c = _Metrica(icon=icon, titulo=titulo, color=color)
            row2_layout.addWidget(c)
            self._cards[key] = c

        layout.addWidget(row2)
        layout.addSpacing(20)

        # ── Quick actions ──────────────────────────────────────
        qa = QFrame()
        qa.setObjectName("card")
        qa_layout = QVBoxLayout(qa)
        qa_layout.setContentsMargins(20, 16, 20, 16)
        qa_layout.setSpacing(12)

        qa_hdr = QLabel("⚡  Acciones Rápidas")
        qa_hdr.setObjectName("section")
        qa_layout.addWidget(qa_hdr)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet("background: #E2E8F0;")
        qa_layout.addWidget(sep2)

        btn_row = QWidget()
        btn_row.setStyleSheet("background: transparent;")
        btn_layout = QHBoxLayout(btn_row)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(10)

        for label, key, obj in [
            ("➕  Nuevo Cliente",  "clientes",  ""),
            ("📋  Nuevo Préstamo", "prestamos", ""),
            ("💵  Cobrar",         "caja",      "btn_success"),
            ("📊  Reportes",       "reportes",  "btn_secondary"),
        ]:
            btn = QPushButton(label)
            btn.setFixedHeight(42)
            if obj:
                btn.setObjectName(obj)
            btn.clicked.connect(lambda ch=False, k=key: self._navegar(k) if self._navegar else None)
            btn_layout.addWidget(btn)

        btn_layout.addStretch()
        qa_layout.addWidget(btn_row)

        layout.addWidget(qa)
        layout.addStretch()

    # ── Refresh ─────────────────────────────────────────────────────────

    def refrescar(self):
        self._lbl_fecha.setText(_fecha_es())
        for card in self._cards.values():
            card.set_valor("...")
        self._worker = Worker(get_dashboard)
        self._worker.result.connect(self._actualizar_ui)
        self._worker.start()

    def _actualizar_ui(self, datos: dict):
        m = self._moneda
        self._cards["activos"].set_valor(str(datos["prestamos_activos"]))
        self._cards["mora"].set_valor(str(datos["prestamos_vencidos"]))
        self._cards["cobrado"].set_valor(f"{m} {datos['cobrado_hoy']:,.2f}")
        self._cards["clientes"].set_valor(str(datos["clientes_total"]))
        self._cards["cartera"].set_valor(f"{m} {datos['cartera_total']:,.2f}")
