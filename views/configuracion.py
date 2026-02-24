"""System configuration screen — PyQt6."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QScrollArea, QFrame, QCheckBox,
)
from PyQt6.QtCore import Qt

from config import TIPOS_TASA
from database.seed import get_all_config, set_config, get_config

CAMPOS_AGENCIA = [
    ("nombre_agencia",    "Nombre de la Agencia"),
    ("nit_agencia",       "RNC / NIT"),
    ("direccion_agencia", "Dirección"),
    ("telefono_agencia",  "Teléfono"),
    ("email_agencia",     "Correo Electrónico"),
    ("moneda_simbolo",    "Símbolo Moneda"),
]

CAMPOS_CREDITO = [
    ("tasa_mora_diaria", "Tasa Mora Diaria (%)"),
    ("dias_gracia",      "Días de Gracia"),
    ("tasa_default",     "Tasa de Interés Default (%)"),
]


class Configuracion(QWidget):

    def __init__(self, navegar=None, parent=None):
        super().__init__(parent)
        self._navegar  = navegar
        self._widgets: dict[str, QWidget] = {}
        self._build()
        self.refrescar()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        lbl_title = QLabel("Configuración del Sistema")
        lbl_title.setObjectName("title")
        lbl_title.setContentsMargins(24, 20, 24, 12)
        root.addWidget(lbl_title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        inner = QWidget()
        self._layout = QVBoxLayout(inner)
        self._layout.setContentsMargins(24, 0, 24, 24)
        self._layout.setSpacing(4)
        scroll.setWidget(inner)
        root.addWidget(scroll, 1)

        def seccion(titulo: str, campos: list):
            lbl = QLabel(titulo)
            lbl.setObjectName("section")
            self._layout.addSpacing(12)
            self._layout.addWidget(lbl)
            card = QFrame()
            card.setObjectName("card")
            cl = QVBoxLayout(card)
            cl.setContentsMargins(16, 8, 16, 8)
            cl.setSpacing(4)
            for clave, label in campos:
                row = QWidget()
                row.setStyleSheet("background: transparent;")
                rl = QHBoxLayout(row)
                rl.setContentsMargins(0, 4, 0, 4)
                rl.setSpacing(12)
                lbl_k = QLabel(label)
                lbl_k.setFixedWidth(220)
                lbl_k.setObjectName("dim")
                rl.addWidget(lbl_k)
                entry = QLineEdit()
                entry.setFixedHeight(32)
                rl.addWidget(entry, 1)
                cl.addWidget(row)
                self._widgets[clave] = entry
            self._layout.addWidget(card)

        seccion("🏢  Datos de la Agencia", CAMPOS_AGENCIA)
        seccion("💰  Parámetros de Crédito", CAMPOS_CREDITO)

        # Tipo tasa default
        tasa_card = QFrame()
        tasa_card.setObjectName("card")
        tl = QVBoxLayout(tasa_card)
        tl.setContentsMargins(16, 8, 16, 8)
        tasa_row = QWidget()
        tasa_row.setStyleSheet("background: transparent;")
        tr = QHBoxLayout(tasa_row)
        tr.setContentsMargins(0, 4, 0, 4)
        lbl_tr = QLabel("Tipo de Tasa Default")
        lbl_tr.setFixedWidth(220)
        lbl_tr.setObjectName("dim")
        tr.addWidget(lbl_tr)
        cb_tipo = QComboBox()
        cb_tipo.addItems(TIPOS_TASA)
        cb_tipo.setFixedWidth(160)
        tr.addWidget(cb_tipo)
        tr.addStretch()
        tl.addWidget(tasa_row)
        self._layout.addWidget(tasa_card)
        self._widgets["tipo_tasa_default"] = cb_tipo

        # ── Terminal de Pago ──────────────────────────────────
        lbl_term = QLabel("💳  Terminal de Pago (Verifone)")
        lbl_term.setObjectName("section")
        self._layout.addSpacing(12)
        self._layout.addWidget(lbl_term)

        term_card = QFrame()
        term_card.setObjectName("card")
        term_layout = QVBoxLayout(term_card)
        term_layout.setContentsMargins(16, 12, 16, 12)
        term_layout.setSpacing(6)

        # Enable toggle
        toggle_row = QWidget()
        toggle_row.setStyleSheet("background: transparent;")
        tog_l = QHBoxLayout(toggle_row)
        tog_l.setContentsMargins(0, 0, 0, 0)
        lbl_tog = QLabel("Habilitar Terminal")
        lbl_tog.setFixedWidth(220)
        lbl_tog.setObjectName("dim")
        tog_l.addWidget(lbl_tog)
        self._chk_terminal = QCheckBox("Habilitado")
        self._chk_terminal.setStyleSheet("background: transparent;")
        self._chk_terminal.stateChanged.connect(self._toggle_terminal)
        tog_l.addWidget(self._chk_terminal)
        tog_l.addStretch()
        term_layout.addWidget(toggle_row)

        self._lbl_terminal_estado = QLabel("Deshabilitado")
        self._lbl_terminal_estado.setObjectName("dim")
        term_layout.addWidget(self._lbl_terminal_estado)

        # Mode
        modo_row = QWidget()
        modo_row.setStyleSheet("background: transparent;")
        mr = QHBoxLayout(modo_row)
        mr.setContentsMargins(0, 4, 0, 4)
        lbl_modo = QLabel("Modo de Integración")
        lbl_modo.setFixedWidth(220)
        lbl_modo.setObjectName("dim")
        mr.addWidget(lbl_modo)
        cb_modo = QComboBox()
        cb_modo.addItems(["DISPLAY", "SERIAL"])
        cb_modo.setFixedWidth(160)
        cb_modo.currentTextChanged.connect(self._on_modo_change)
        mr.addWidget(cb_modo)
        mr.addStretch()
        term_layout.addWidget(modo_row)
        self._widgets["terminal_modo"] = cb_modo

        self._lbl_modo_desc = QLabel("")
        self._lbl_modo_desc.setObjectName("dim")
        self._lbl_modo_desc.setWordWrap(True)
        term_layout.addWidget(self._lbl_modo_desc)

        # Serial settings
        self._serial_frame = QWidget()
        self._serial_frame.setStyleSheet("background: transparent;")
        sf_layout = QVBoxLayout(self._serial_frame)
        sf_layout.setContentsMargins(0, 0, 0, 0)
        sf_layout.setSpacing(4)

        for clave, label in [("terminal_puerto", "Puerto COM (ej: COM3)"),
                               ("terminal_baudrate", "Baud Rate")]:
            sr = QWidget()
            sr.setStyleSheet("background: transparent;")
            srl = QHBoxLayout(sr)
            srl.setContentsMargins(0, 2, 0, 2)
            lbl_s = QLabel(label)
            lbl_s.setFixedWidth(220)
            lbl_s.setObjectName("dim")
            srl.addWidget(lbl_s)
            entry = QLineEdit()
            entry.setFixedSize(160, 32)
            srl.addWidget(entry)
            srl.addStretch()
            sf_layout.addWidget(sr)
            self._widgets[clave] = entry

        term_layout.addWidget(self._serial_frame)

        btn_test = QPushButton("🔌  Probar Conexión")
        btn_test.setObjectName("btn_secondary")
        btn_test.setFixedHeight(34)
        btn_test.clicked.connect(self._probar_terminal)
        term_layout.addWidget(btn_test, 0, Qt.AlignmentFlag.AlignLeft)

        self._layout.addWidget(term_card)

        # ── Backup ───────────────────────────────────────────────
        lbl_bk = QLabel("🗄️  Respaldo de Datos")
        lbl_bk.setObjectName("section")
        self._layout.addSpacing(12)
        self._layout.addWidget(lbl_bk)

        bk_card = QFrame()
        bk_card.setObjectName("card")
        bk_layout = QVBoxLayout(bk_card)
        bk_layout.setContentsMargins(16, 12, 16, 12)
        bk_layout.setSpacing(8)

        lbl_bk_info = QLabel(
            "El sistema crea un backup automático cada vez que se inicia.\n"
            "Se conservan los últimos 7 respaldos."
        )
        lbl_bk_info.setObjectName("dim")
        lbl_bk_info.setWordWrap(True)
        bk_layout.addWidget(lbl_bk_info)

        self._lbl_backup_status = QLabel("")
        self._lbl_backup_status.setStyleSheet("color: #16A34A;")
        bk_layout.addWidget(self._lbl_backup_status)

        bk_btns = QWidget()
        bk_btns.setStyleSheet("background: transparent;")
        bbl = QHBoxLayout(bk_btns)
        bbl.setContentsMargins(0, 0, 0, 0)
        bbl.setSpacing(8)

        btn_bk_now = QPushButton("💾  Hacer Backup Ahora")
        btn_bk_now.setFixedHeight(36)
        btn_bk_now.clicked.connect(self._hacer_backup)
        bbl.addWidget(btn_bk_now)

        btn_bk_open = QPushButton("📂  Abrir Carpeta de Backups")
        btn_bk_open.setObjectName("btn_secondary")
        btn_bk_open.setFixedHeight(36)
        btn_bk_open.clicked.connect(self._abrir_carpeta_backup)
        bbl.addWidget(btn_bk_open)

        bbl.addStretch()
        bk_layout.addWidget(bk_btns)
        self._layout.addWidget(bk_card)

        # ── Save ─────────────────────────────────────────────────
        self._layout.addSpacing(8)
        self._lbl_msg = QLabel("")
        self._layout.addWidget(self._lbl_msg)

        btn_save = QPushButton("💾  Guardar Configuración")
        btn_save.setFixedHeight(40)
        btn_save.clicked.connect(self._guardar)
        self._layout.addWidget(btn_save)

    # ── Logic ────────────────────────────────────────────────────────────

    def _get_widget_value(self, w: QWidget) -> str:
        if isinstance(w, QLineEdit):
            return w.text()
        if isinstance(w, QComboBox):
            return w.currentText()
        return ""

    def _set_widget_value(self, w: QWidget, val: str):
        if isinstance(w, QLineEdit):
            w.setText(val)
        elif isinstance(w, QComboBox):
            idx = w.findText(val)
            if idx >= 0:
                w.setCurrentIndex(idx)

    def refrescar(self):
        conf = get_all_config()
        for clave, w in self._widgets.items():
            self._set_widget_value(w, conf.get(clave, ""))
        self._chk_terminal.setChecked(conf.get("terminal_habilitado", "0") == "1")
        self._on_modo_change(conf.get("terminal_modo", "DISPLAY"))
        self._toggle_terminal()

    def _toggle_terminal(self):
        on = self._chk_terminal.isChecked()
        self._lbl_terminal_estado.setText(
            "✅ Habilitado" if on else "Deshabilitado"
        )
        self._lbl_terminal_estado.setStyleSheet(
            f"color: {'#16A34A' if on else '#94A3B8'};"
        )

    def _on_modo_change(self, modo: str = None):
        if modo is None:
            modo = self._widgets["terminal_modo"].currentText()
        if isinstance(modo, int):
            modo = self._widgets["terminal_modo"].currentText()
        if modo == "SERIAL":
            desc = (
                "Modo Serial: el sistema enviará el monto directamente al puerto COM del terminal.\n"
                "Requiere que el terminal esté conectado y configurado."
            )
            self._serial_frame.show()
        else:
            desc = (
                "Modo Display: el monto aparece en pantalla grande para que el operador\n"
                "lo digite en el Verifone. Funciona con cualquier terminal sin configuración."
            )
            self._serial_frame.hide()
        self._lbl_modo_desc.setText(desc)

    def _probar_terminal(self):
        from services.terminal_pago import TerminalPago
        set_config("terminal_modo",       self._get_widget_value(self._widgets["terminal_modo"]))
        set_config("terminal_puerto",     self._get_widget_value(self._widgets.get("terminal_puerto", QLineEdit())))
        set_config("terminal_baudrate",   self._get_widget_value(self._widgets.get("terminal_baudrate", QLineEdit())))
        set_config("terminal_habilitado", "1" if self._chk_terminal.isChecked() else "0")
        t = TerminalPago()
        resultado = t.iniciar_pago(1.00, "TEST")
        ok = resultado.get("ok", False)
        msg = resultado.get("msg", "")
        self._lbl_msg.setText(f"{'✅' if ok else '⚠'} {msg}")
        self._lbl_msg.setStyleSheet(f"color: {'#16A34A' if ok else '#D97706'};")

    def _hacer_backup(self):
        try:
            from services.backup import hacer_backup
            import os
            path = hacer_backup()
            self._lbl_backup_status.setText(
                f"✅  Backup guardado: {os.path.basename(path)}"
            )
        except Exception as e:
            self._lbl_backup_status.setText(f"⚠  Error: {e}")
            self._lbl_backup_status.setStyleSheet("color: #DC2626;")

    def _abrir_carpeta_backup(self):
        import subprocess, os
        from config import BASE_DIR
        backup_dir = os.path.join(BASE_DIR, "data", "backups")
        os.makedirs(backup_dir, exist_ok=True)
        subprocess.Popen(["open", backup_dir])

    def _guardar(self):
        for clave, w in self._widgets.items():
            set_config(clave, self._get_widget_value(w))
        set_config("terminal_habilitado", "1" if self._chk_terminal.isChecked() else "0")
        self._lbl_msg.setText("✅  Configuración guardada.")
        self._lbl_msg.setStyleSheet("color: #16A34A;")
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(3000, lambda: self._lbl_msg.setText(""))
