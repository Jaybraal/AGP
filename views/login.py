"""Login dialog — PyQt6."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QWidget,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class LoginDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AGP — Iniciar Sesión")
        self.setFixedSize(380, 320)
        self.setModal(True)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.CustomizeWindowHint
        )
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 36, 40, 32)
        layout.setSpacing(0)

        # ── Logo / título ────────────────────────────────────────────
        lbl_logo = QLabel("AGP")
        lbl_logo.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        font_logo = QFont("Segoe UI", 28, QFont.Weight.Bold)
        lbl_logo.setFont(font_logo)
        lbl_logo.setStyleSheet("color: #2563EB; margin-bottom: 2px;")
        layout.addWidget(lbl_logo)

        lbl_sub = QLabel("Sistema de Gestión de Préstamos")
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        lbl_sub.setStyleSheet("color: #64748B; font-size: 12px; margin-bottom: 24px;")
        layout.addWidget(lbl_sub)

        # ── Usuario ──────────────────────────────────────────────────
        lbl_usr = QLabel("Usuario")
        lbl_usr.setStyleSheet("font-size: 12px; font-weight: 600; color: #374151; margin-top: 4px;")
        layout.addWidget(lbl_usr)

        self._inp_usuario = QLineEdit()
        self._inp_usuario.setPlaceholderText("Ingrese su usuario")
        self._inp_usuario.setFixedHeight(40)
        self._inp_usuario.setStyleSheet(
            "QLineEdit { border: 1px solid #D1D5DB; border-radius: 6px; "
            "padding: 0 12px; font-size: 13px; background: #F9FAFB; }"
            "QLineEdit:focus { border-color: #2563EB; background: #fff; }"
        )
        layout.addWidget(self._inp_usuario)
        layout.addSpacing(10)

        # ── Contraseña ───────────────────────────────────────────────
        lbl_pwd = QLabel("Contraseña")
        lbl_pwd.setStyleSheet("font-size: 12px; font-weight: 600; color: #374151;")
        layout.addWidget(lbl_pwd)

        self._inp_password = QLineEdit()
        self._inp_password.setPlaceholderText("Ingrese su contraseña")
        self._inp_password.setEchoMode(QLineEdit.EchoMode.Password)
        self._inp_password.setFixedHeight(40)
        self._inp_password.setStyleSheet(
            "QLineEdit { border: 1px solid #D1D5DB; border-radius: 6px; "
            "padding: 0 12px; font-size: 13px; background: #F9FAFB; }"
            "QLineEdit:focus { border-color: #2563EB; background: #fff; }"
        )
        self._inp_password.returnPressed.connect(self._intentar_login)
        layout.addWidget(self._inp_password)
        layout.addSpacing(6)

        # ── Error ────────────────────────────────────────────────────
        self._lbl_error = QLabel("")
        self._lbl_error.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self._lbl_error.setStyleSheet("color: #DC2626; font-size: 12px;")
        self._lbl_error.setWordWrap(True)
        layout.addWidget(self._lbl_error)
        layout.addSpacing(10)

        # ── Botón ────────────────────────────────────────────────────
        self._btn_login = QPushButton("Iniciar Sesión")
        self._btn_login.setFixedHeight(42)
        self._btn_login.setStyleSheet(
            "QPushButton { background: #2563EB; color: white; border-radius: 6px; "
            "font-size: 14px; font-weight: 600; border: none; }"
            "QPushButton:hover { background: #1D4ED8; }"
            "QPushButton:pressed { background: #1E40AF; }"
        )
        self._btn_login.clicked.connect(self._intentar_login)
        layout.addWidget(self._btn_login)

    def _intentar_login(self):
        from werkzeug.security import check_password_hash
        from database.seed import get_config

        usuario  = self._inp_usuario.text().strip()
        password = self._inp_password.text()

        if not usuario or not password:
            self._lbl_error.setText("Complete usuario y contraseña.")
            return

        usr_ok = usuario == get_config("login_usuario")
        pwd_ok = check_password_hash(get_config("login_password_hash"), password)

        if usr_ok and pwd_ok:
            self.accept()
        else:
            self._lbl_error.setText("Usuario o contraseña incorrectos.")
            self._inp_password.clear()
            self._inp_password.setFocus()
