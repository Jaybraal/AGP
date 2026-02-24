"""Cash module main entry — PyQt6."""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt

from controllers.caja_controller import caja_activa
from views.components.worker import Worker


class CajaMain(QWidget):

    def __init__(self, navegar=None, parent=None):
        super().__init__(parent)
        self._navegar = navegar
        self._sub: QWidget | None = None
        self._worker: Worker | None = None
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self.refrescar()

    def refrescar(self):
        self._mostrar_loading()
        self._worker = Worker(caja_activa)
        self._worker.result.connect(self._mostrar_caja)
        self._worker.start()

    def _mostrar_loading(self):
        self._clear_sub()
        loading = QLabel("Cargando...")
        loading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading.setObjectName("dim")
        self._sub = loading
        self._layout.addWidget(self._sub)

    def _mostrar_caja(self, caja):
        self._clear_sub()
        if caja:
            from views.caja.cobro_rapido import CobroRapido
            self._sub = CobroRapido(caja=caja, navegar=self._navegar)
        else:
            from views.caja.apertura_caja import AperturaCaja
            self._sub = AperturaCaja(on_abierta=self.refrescar)
        self._layout.addWidget(self._sub)

    def _clear_sub(self):
        if self._sub is not None:
            widget = self._sub
            self._sub = None
            self._layout.removeWidget(widget)
            widget.setParent(None)
            widget.deleteLater()
