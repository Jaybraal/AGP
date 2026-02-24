"""Confirmation dialog — PyQt6.
exec() runs Qt's nested event loop (UI stays responsive, unlike tkinter wait_window).
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget,
)
from PyQt6.QtCore import Qt


class ModalConfirm(QDialog):

    def __init__(self, parent=None, titulo: str = "", mensaje: str = "",
                 btn_ok: str = "Confirmar"):
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.setModal(True)
        self.setFixedWidth(380)
        self._build(titulo, mensaje, btn_ok)

    def _build(self, titulo: str, mensaje: str, btn_ok: str):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 20)

        lbl_titulo = QLabel(titulo)
        lbl_titulo.setObjectName("section")
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(lbl_titulo)

        lbl_msg = QLabel(mensaje)
        lbl_msg.setWordWrap(True)
        lbl_msg.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(lbl_msg)

        btn_bar = QWidget()
        btn_layout = QHBoxLayout(btn_bar)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(8)

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("btn_secondary")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        btn_ok_w = QPushButton(btn_ok)
        btn_ok_w.setObjectName("btn_danger")
        btn_ok_w.clicked.connect(self.accept)
        btn_layout.addWidget(btn_ok_w)

        layout.addWidget(btn_bar)


def confirmar(parent, titulo: str, mensaje: str,
              btn_ok: str = "Confirmar", on_confirmado=None):
    """
    Show a blocking confirmation dialog.
    Qt's exec() runs a nested event loop — the UI stays responsive.
    on_confirmado() is called only when the user clicks OK.
    """
    dlg = ModalConfirm(parent, titulo, mensaje, btn_ok=btn_ok)
    if dlg.exec() == QDialog.DialogCode.Accepted:
        if on_confirmado:
            on_confirmado()
