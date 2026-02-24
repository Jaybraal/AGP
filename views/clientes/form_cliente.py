"""New / Edit client form — PyQt6 QDialog."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QTextEdit, QComboBox, QPushButton,
    QScrollArea, QWidget, QFrame,
)
from PyQt6.QtCore import Qt

from config import TIPOS_DOC, CALIFICACIONES, TIPOS_TASA
from controllers.cliente_controller import guardar_cliente, obtener
from database.seed import get_config
from views.components.worker import Worker


class FormCliente(QDialog):

    def __init__(self, cliente_id=None, on_guardado=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nuevo Cliente" if not cliente_id else "Editar Cliente")
        self.resize(620, 740)
        self.setModal(True)

        self._cliente_id  = cliente_id
        self._on_guardado = on_guardado
        self._worker: Worker | None = None

        self._build()

        if cliente_id:
            self._cargar_datos()

    # ── Build ────────────────────────────────────────────────────────────

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Scrollable area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        inner = QWidget()
        self._form_layout = QVBoxLayout(inner)
        self._form_layout.setContentsMargins(24, 20, 24, 8)
        self._form_layout.setSpacing(4)
        scroll.setWidget(inner)
        root.addWidget(scroll, 1)

        self._widgets: dict[str, QWidget] = {}

        def seccion(titulo: str):
            lbl = QLabel(titulo)
            lbl.setObjectName("section")
            self._form_layout.addSpacing(12)
            self._form_layout.addWidget(lbl)
            sep = QFrame()
            sep.setFrameShape(QFrame.Shape.HLine)
            sep.setStyleSheet("background: #E2E8F0;")
            sep.setFixedHeight(1)
            self._form_layout.addWidget(sep)
            self._form_layout.addSpacing(4)

        def fila(label: str, key: str, widget: QWidget):
            row = QWidget()
            row.setStyleSheet("background: transparent;")
            rl = QHBoxLayout(row)
            rl.setContentsMargins(0, 2, 0, 2)
            rl.setSpacing(12)
            lbl = QLabel(label)
            lbl.setFixedWidth(180)
            lbl.setObjectName("dim")
            rl.addWidget(lbl)
            rl.addWidget(widget, 1)
            self._form_layout.addWidget(row)
            self._widgets[key] = widget

        # ── Identificación ────────────────────────────────────
        seccion("Identificación")

        cb_tipo = QComboBox()
        cb_tipo.addItems(TIPOS_DOC)
        fila("Tipo Documento", "tipo_documento", cb_tipo)

        for key, label in [("cedula", "Número Doc.*"), ("nombres", "Nombres*"),
                            ("apellidos", "Apellidos*"), ("fecha_nacimiento", "Fecha Nac. (YYYY-MM-DD)")]:
            entry = QLineEdit()
            fila(label, key, entry)

        # ── Contacto ─────────────────────────────────────────
        seccion("Contacto")
        for key, label in [("telefono_principal", "Teléfono Principal*"),
                            ("telefono_secundario", "Teléfono Secundario"),
                            ("email", "Correo Electrónico")]:
            entry = QLineEdit()
            fila(label, key, entry)

        # ── Dirección ────────────────────────────────────────
        seccion("Dirección")
        for key, label in [("direccion", "Dirección"), ("barrio", "Sector/Barrio"), ("ciudad", "Ciudad")]:
            entry = QLineEdit()
            fila(label, key, entry)

        # ── Perfil Crediticio ────────────────────────────────
        seccion("Perfil Crediticio")

        cb_cal = QComboBox()
        cb_cal.addItems(CALIFICACIONES)
        cb_cal.setCurrentText("NUEVO")
        fila("Calificación", "calificacion", cb_cal)

        for key, label in [("ocupacion", "Ocupación"), ("empresa", "Empresa")]:
            entry = QLineEdit()
            fila(label, key, entry)

        entry_ing = QLineEdit("0")
        fila("Ingresos Mensuales", "ingresos_mensuales", entry_ing)

        # ── Condiciones de Crédito ───────────────────────────
        seccion("Condiciones de Crédito Personalizadas")

        tasa_container = QWidget()
        tasa_container.setStyleSheet("background: transparent;")
        tasa_layout = QHBoxLayout(tasa_container)
        tasa_layout.setContentsMargins(0, 0, 0, 0)
        tasa_layout.setSpacing(8)

        self._entry_tasa = QLineEdit(get_config("tasa_default") or "5.0")
        self._entry_tasa.setFixedWidth(100)
        tasa_layout.addWidget(self._entry_tasa)

        cb_tipo_tasa = QComboBox()
        cb_tipo_tasa.addItems(TIPOS_TASA)
        cb_tipo_tasa.setCurrentText(get_config("tipo_tasa_default") or "MENSUAL")
        cb_tipo_tasa.setFixedWidth(130)
        tasa_layout.addWidget(cb_tipo_tasa)

        self._lbl_badge_tasa = QLabel("")
        self._lbl_badge_tasa.setObjectName("dim")
        tasa_layout.addWidget(self._lbl_badge_tasa)
        tasa_layout.addStretch()

        fila("Tasa Sugerida (%)", "tasa_sugerida", tasa_container)
        self._widgets["tasa_sugerida"] = self._entry_tasa
        self._widgets["tipo_tasa_sugerida"] = cb_tipo_tasa

        self._entry_tasa.textChanged.connect(self._actualizar_badge)
        cb_tipo_tasa.currentTextChanged.connect(self._actualizar_badge)
        self._actualizar_badge()

        # ── Notas ─────────────────────────────────────────────
        seccion("Notas")
        self._notas = QTextEdit()
        self._notas.setFixedHeight(70)
        self._form_layout.addWidget(self._notas)

        # Error label
        self._lbl_error = QLabel("")
        self._lbl_error.setStyleSheet("color: #DC2626;")
        self._form_layout.addWidget(self._lbl_error)

        # ── Buttons ────────────────────────────────────────────
        btn_frame = QWidget()
        btn_layout = QHBoxLayout(btn_frame)
        btn_layout.setContentsMargins(24, 8, 24, 16)
        btn_layout.setSpacing(8)
        btn_layout.addStretch()

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("btn_secondary")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        btn_save = QPushButton("💾  Guardar")
        btn_save.clicked.connect(self._guardar)
        btn_layout.addWidget(btn_save)

        root.addWidget(btn_frame)

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

    def _actualizar_badge(self):
        try:
            tasa = float(self._entry_tasa.text() or 0)
            tipo = self._widgets["tipo_tasa_sugerida"].currentText()
            dias = {"DIARIA": 1, "SEMANAL": 7, "QUINCENAL": 15, "MENSUAL": 30, "ANUAL": 360}
            d = dias.get(tipo, 30)
            mensual = ((1 + tasa / 100) ** (30 / d) - 1) * 100
            self._lbl_badge_tasa.setText(f"≈ {mensual:.2f}% mensual")
        except Exception:
            self._lbl_badge_tasa.setText("")

    def _cargar_datos(self):
        cliente = obtener(self._cliente_id)
        if not cliente:
            return
        for key, w in self._widgets.items():
            val = cliente.get(key, "")
            self._set_widget_value(w, str(val) if val is not None else "")
        self._notas.setPlainText(cliente.get("notas", "") or "")

    def _guardar(self):
        self._lbl_error.setText("Guardando...")
        datos = {k: self._get_widget_value(w) for k, w in self._widgets.items()}
        for campo in ("ingresos_mensuales", "tasa_sugerida"):
            try:
                datos[campo] = float(datos.get(campo, 0) or 0)
            except ValueError:
                datos[campo] = 0.0
        datos["notas"] = self._notas.toPlainText().strip()
        cliente_id = self._cliente_id

        self._worker = Worker(guardar_cliente, datos, cliente_id)
        self._worker.result.connect(lambda _: self._post_guardar())
        self._worker.error.connect(lambda msg: self._lbl_error.setText(msg))
        self._worker.start()

    def _post_guardar(self):
        if self._on_guardado:
            self._on_guardado()
        self.accept()
