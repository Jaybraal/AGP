"""Client profile dialog — PyQt6."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QFrame, QLineEdit,
)
from PyQt6.QtCore import Qt

from config import ESTADO_COLORS
from controllers.cliente_controller import obtener
from controllers.prestamo_controller import listar as listar_prestamos
from models.cliente import nombre_completo, obtener_garantes, agregar_garante, eliminar_garante
from views.components.tabla import Tabla
from views.components.modal_confirm import confirmar
from views.components.worker import Worker

_CAL_COLORS = {
    "BUENO":   "#16A34A",
    "REGULAR": "#D97706",
    "MALO":    "#DC2626",
    "NUEVO":   "#64748B",
}


class PerfilCliente(QDialog):

    def __init__(self, cliente_id: int, navegar=None, parent=None):
        super().__init__(parent)
        self._cliente_id = cliente_id
        self._navegar    = navegar
        self._worker: Worker | None = None
        self._garantes_data: list = []

        self._cliente = obtener(cliente_id)
        if not self._cliente:
            self.done(0)
            return

        self.setWindowTitle(f"Perfil: {nombre_completo(self._cliente)}")
        self.resize(840, 720)
        self.setModal(True)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)
        scroll.setWidget(inner)
        root.addWidget(scroll, 1)

        c = self._cliente

        # ── Header card ────────────────────────────────────────
        hdr = QFrame()
        hdr.setStyleSheet("background: #2563EB; border-radius: 12px;")
        hdr_layout = QVBoxLayout(hdr)
        hdr_layout.setContentsMargins(20, 16, 20, 14)
        hdr_layout.setSpacing(4)

        top_row = QWidget()
        top_row.setStyleSheet("background: transparent;")
        tr_layout = QHBoxLayout(top_row)
        tr_layout.setContentsMargins(0, 0, 0, 0)

        lbl_nombre = QLabel(nombre_completo(c))
        lbl_nombre.setStyleSheet("color: white; font-size: 18px; font-weight: bold; background: transparent;")
        tr_layout.addWidget(lbl_nombre, 1)

        cal_color = _CAL_COLORS.get(c["calificacion"], "#FFFFFF")
        lbl_cal = QLabel(c["calificacion"])
        lbl_cal.setStyleSheet(f"color: {cal_color}; font-weight: bold; background: transparent;")
        tr_layout.addWidget(lbl_cal)

        hdr_layout.addWidget(top_row)

        lbl_info = QLabel(
            f"Cédula: {c['cedula']}   |   Tel: {c['telefono_principal']}"
            f"   |   {c.get('email', '') or 'Sin correo'}"
        )
        lbl_info.setStyleSheet("color: #BFDBFE; font-size: 11px; background: transparent;")
        hdr_layout.addWidget(lbl_info)

        layout.addWidget(hdr)

        # ── Info grid ──────────────────────────────────────────
        info_card = QFrame()
        info_card.setObjectName("card")
        info_grid = QWidget()
        info_grid.setStyleSheet("background: transparent;")
        grid_layout = QHBoxLayout(info_card)
        grid_layout.setContentsMargins(16, 12, 16, 12)

        campos = [
            ("Ciudad",    c.get("ciudad", "—") or "—"),
            ("Dirección", c.get("direccion", "—") or "—"),
            ("Ocupación", c.get("ocupacion", "—") or "—"),
            ("Ingresos",  f"RD$ {c.get('ingresos_mensuales', 0):,.2f}"),
            ("Registro",  (c.get("fecha_registro", "—") or "—")[:10]),
        ]
        for label, valor in campos:
            f = QWidget()
            f.setStyleSheet("background: transparent;")
            fl = QHBoxLayout(f)
            fl.setContentsMargins(0, 0, 0, 0)
            fl.setSpacing(6)
            lbl_k = QLabel(label + ":")
            lbl_k.setObjectName("dim")
            fl.addWidget(lbl_k)
            lbl_v = QLabel(valor)
            lbl_v.setStyleSheet("font-weight: bold;")
            fl.addWidget(lbl_v)
            grid_layout.addWidget(f)

        layout.addWidget(info_card)

        # ── Loans ──────────────────────────────────────────────
        loans_hdr = QLabel("📋  Préstamos")
        loans_hdr.setObjectName("section")
        layout.addWidget(loans_hdr)

        prestamos = listar_prestamos(cliente_id=self._cliente_id)
        if not prestamos:
            lbl_np = QLabel("Sin préstamos registrados.")
            lbl_np.setObjectName("dim")
            layout.addWidget(lbl_np)
        else:
            for p in prestamos:
                color = ESTADO_COLORS.get(p["estado"], "#2563EB")
                card = QFrame()
                card.setObjectName("card")
                cl = QHBoxLayout(card)
                cl.setContentsMargins(14, 10, 14, 10)

                left_col = QWidget()
                left_col.setStyleSheet("background: transparent;")
                lcl = QVBoxLayout(left_col)
                lcl.setContentsMargins(0, 0, 0, 0)
                lcl.setSpacing(2)

                lbl_num = QLabel(
                    f"#{p['numero_prestamo']}   Capital: RD$ {p['monto_principal']:,.2f}"
                    f"   Cuota: RD$ {p['cuota_base']:,.2f}"
                )
                lbl_num.setStyleSheet("font-weight: bold;")
                lcl.addWidget(lbl_num)

                lbl_detail = QLabel(
                    f"Saldo: RD$ {p['saldo_capital']:,.2f}   |   "
                    f"Vence: {p['fecha_vencimiento']}   |   {p['frecuencia_pago']}"
                )
                lbl_detail.setObjectName("dim")
                lcl.addWidget(lbl_detail)

                cl.addWidget(left_col, 1)

                lbl_estado = QLabel(p["estado"])
                lbl_estado.setStyleSheet(f"color: {color}; font-weight: bold;")
                cl.addWidget(lbl_estado)

                layout.addWidget(card)

        # ── Guarantors ─────────────────────────────────────────
        gar_hdr = QWidget()
        gar_hdr.setStyleSheet("background: transparent;")
        gh_layout = QHBoxLayout(gar_hdr)
        gh_layout.setContentsMargins(0, 8, 0, 4)

        lbl_gar = QLabel("🤝  Garantes / Fiadores")
        lbl_gar.setObjectName("section")
        gh_layout.addWidget(lbl_gar, 1)

        btn_add_gar = QPushButton("➕  Agregar Garante")
        btn_add_gar.setFixedHeight(34)
        btn_add_gar.clicked.connect(self._agregar_garante)
        gh_layout.addWidget(btn_add_gar)

        layout.addWidget(gar_hdr)

        COLS_GAR = [
            ("cedula",             "Cédula",    120),
            ("nombres",            "Nombre",    180),
            ("apellidos",          "Apellido",  150),
            ("telefono_principal", "Teléfono",  110),
            ("relacion",           "Relación",  100),
        ]
        self._tabla_garantes = Tabla(columnas=COLS_GAR, height=150)
        layout.addWidget(self._tabla_garantes)

        btn_gar_row = QWidget()
        btn_gar_row.setStyleSheet("background: transparent;")
        bg_layout = QHBoxLayout(btn_gar_row)
        bg_layout.setContentsMargins(0, 4, 0, 4)
        bg_layout.setSpacing(8)

        btn_quit_gar = QPushButton("🗑️  Quitar Garante Seleccionado")
        btn_quit_gar.setObjectName("btn_secondary")
        btn_quit_gar.setFixedHeight(34)
        btn_quit_gar.clicked.connect(self._quitar_garante)
        bg_layout.addWidget(btn_quit_gar)

        self._lbl_gar_msg = QLabel("")
        self._lbl_gar_msg.setStyleSheet("color: #DC2626;")
        bg_layout.addWidget(self._lbl_gar_msg)
        bg_layout.addStretch()

        layout.addWidget(btn_gar_row)

        # Close button
        btn_close = QPushButton("Cerrar")
        btn_close.setObjectName("btn_secondary")
        btn_close.clicked.connect(self.accept)
        root.addWidget(btn_close)

        self._cargar_garantes()

    # ── Guarantors ───────────────────────────────────────────────────────

    def _cargar_garantes(self):
        prestamos = listar_prestamos(cliente_id=self._cliente_id)
        garantes = []
        visto_ids: set = set()
        for p in prestamos:
            for g in obtener_garantes(p["id"]):
                if g["id"] not in visto_ids:
                    garantes.append(g)
                    visto_ids.add(g["id"])
        self._garantes_data = garantes
        self._tabla_garantes.cargar(garantes)

    def _agregar_garante(self):
        from PyQt6.QtWidgets import QDialog as _D
        dlg = _AgregarGaranteDialog(self._cliente_id, parent=self)
        if dlg.exec() == _D.DialogCode.Accepted:
            self._cargar_garantes()

    def _quitar_garante(self):
        self._lbl_gar_msg.setText("")
        sel = self._tabla_garantes.seleccionado()
        if not sel:
            self._lbl_gar_msg.setText("Seleccione un garante primero.")
            return
        nombre = f"{sel.get('nombres', '')} {sel.get('apellidos', '')}"

        def _hacer():
            try:
                eliminar_garante(sel["id"])
                self._cargar_garantes()
            except Exception as e:
                self._lbl_gar_msg.setText(str(e))

        confirmar(self, "Quitar Garante", f"¿Quitar a {nombre} como garante?",
                  "Quitar", on_confirmado=_hacer)


# ── Add Guarantor Dialog ───────────────────────────────────────────────────────

class _AgregarGaranteDialog(QDialog):

    def __init__(self, cliente_id: int, parent=None):
        super().__init__(parent)
        self._cliente_id = cliente_id
        self._garante_seleccionado = None
        self._worker: Worker | None = None
        self.setWindowTitle("Agregar Garante")
        self.resize(420, 300)
        self.setModal(True)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        lbl_title = QLabel("Agregar Garante / Fiador")
        lbl_title.setObjectName("section")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(lbl_title)

        lbl_sub = QLabel("Busca al garante por cédula o nombre")
        lbl_sub.setObjectName("dim")
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(lbl_sub)

        self._entry = QLineEdit()
        self._entry.setPlaceholderText("Cédula o nombre del garante...")
        self._entry.setFixedHeight(40)
        self._entry.textChanged.connect(self._buscar)
        layout.addWidget(self._entry)

        self._entry_relacion = QLineEdit()
        self._entry_relacion.setPlaceholderText("Relación (ej: Cónyuge, Hermano...)")
        self._entry_relacion.setFixedHeight(36)
        layout.addWidget(self._entry_relacion)

        self._lbl_resultado = QLabel("")
        self._lbl_resultado.setObjectName("dim")
        self._lbl_resultado.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self._lbl_resultado)

        self._lbl_err = QLabel("")
        self._lbl_err.setStyleSheet("color: #DC2626;")
        self._lbl_err.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self._lbl_err)

        btn_row = QWidget()
        bl = QHBoxLayout(btn_row)
        bl.setContentsMargins(0, 0, 0, 0)
        bl.setSpacing(8)

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("btn_secondary")
        btn_cancel.clicked.connect(self.reject)
        bl.addWidget(btn_cancel)

        btn_save = QPushButton("✅  Agregar")
        btn_save.setObjectName("btn_success")
        btn_save.clicked.connect(self._guardar)
        bl.addWidget(btn_save)

        layout.addWidget(btn_row)

        self._timer = __import__("PyQt6.QtCore", fromlist=["QTimer"]).QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._ejecutar_busqueda)

    def _buscar(self, _text: str):
        self._timer.stop()
        self._timer.start(250)

    def _ejecutar_busqueda(self):
        termino = self._entry.text().strip()
        if not termino:
            return
        from controllers.cliente_controller import buscar as buscar_clientes
        self._worker = Worker(buscar_clientes, termino)
        self._worker.result.connect(self._mostrar)
        self._worker.start()

    def _mostrar(self, resultados: list):
        if not resultados:
            self._lbl_resultado.setText("No se encontró ningún cliente.")
            self._lbl_resultado.setStyleSheet("color: #DC2626;")
            self._garante_seleccionado = None
        elif len(resultados) == 1:
            g = resultados[0]
            self._lbl_resultado.setText(
                f"✓ {g['nombres']} {g['apellidos']} — {g['cedula']}"
            )
            self._lbl_resultado.setStyleSheet("color: #16A34A;")
            self._garante_seleccionado = g
        else:
            names = ", ".join(f"{r['nombres']} {r['apellidos']}" for r in resultados[:3])
            self._lbl_resultado.setText(f"Varios: {names}...")
            self._lbl_resultado.setStyleSheet("color: #D97706;")
            self._garante_seleccionado = None

    def _guardar(self):
        self._lbl_err.setText("")
        if not self._garante_seleccionado:
            self._lbl_err.setText("Seleccione un garante válido.")
            return
        if self._garante_seleccionado["id"] == self._cliente_id:
            self._lbl_err.setText("El garante no puede ser el mismo cliente.")
            return
        prestamos = listar_prestamos(cliente_id=self._cliente_id)
        if not prestamos:
            self._lbl_err.setText("Este cliente no tiene préstamos activos.")
            return
        try:
            relacion = self._entry_relacion.text().strip() or "Garante"
            for p in prestamos:
                try:
                    agregar_garante(p["id"], self._garante_seleccionado["id"], relacion)
                except Exception:
                    pass
            self.accept()
        except Exception as e:
            self._lbl_err.setText(str(e))
