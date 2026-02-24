"""Cash session opening screen — PyQt6."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame,
)
from PyQt6.QtCore import Qt

from controllers.caja_controller import abrir


class AperturaCaja(QWidget):

    def __init__(self, on_abierta=None, parent=None):
        super().__init__(parent)
        self._on_abierta = on_abierta
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        # Center card
        card = QFrame()
        card.setObjectName("card")
        card.setFixedWidth(420)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(40, 30, 40, 30)
        card_layout.setSpacing(12)

        lbl_title = QLabel("💵  Apertura de Caja")
        lbl_title.setObjectName("title")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        card_layout.addWidget(lbl_title)

        lbl_sub = QLabel("Ingrese el efectivo inicial en caja")
        lbl_sub.setObjectName("dim")
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        card_layout.addWidget(lbl_sub)

        lbl_monto = QLabel("Monto de Apertura (RD$)")
        card_layout.addWidget(lbl_monto)

        self._entry_monto = QLineEdit("0")
        self._entry_monto.setFixedHeight(40)
        self._entry_monto.setStyleSheet("font-size: 16px;")
        card_layout.addWidget(self._entry_monto)

        lbl_notas = QLabel("Notas (opcional)")
        card_layout.addWidget(lbl_notas)

        self._entry_notas = QLineEdit()
        self._entry_notas.setFixedHeight(34)
        card_layout.addWidget(self._entry_notas)

        self._lbl_error = QLabel("")
        self._lbl_error.setStyleSheet("color: #DC2626;")
        self._lbl_error.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        card_layout.addWidget(self._lbl_error)

        btn_abrir = QPushButton("✅  Abrir Caja")
        btn_abrir.setObjectName("btn_success")
        btn_abrir.setFixedHeight(44)
        btn_abrir.clicked.connect(self._abrir)
        card_layout.addWidget(btn_abrir)

        # Center the card
        center = QWidget()
        center_layout = QVBoxLayout(center)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(card)
        outer.addWidget(center, 1)

    def _abrir(self):
        self._lbl_error.setText("")
        try:
            monto = float(self._entry_monto.text() or 0)
            notas = self._entry_notas.text().strip()
            abrir(monto, notas)
            if self._on_abierta:
                self._on_abierta()
        except Exception as e:
            self._lbl_error.setText(str(e))
