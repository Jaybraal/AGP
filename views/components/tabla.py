"""Reusable table widget — PyQt6 (QTableWidget)."""

from typing import Optional, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView,
)
from PyQt6.QtCore import Qt


class Tabla(QWidget):
    """
    columnas : list of (key, label, width) tuples
    on_select: callback(row_dict) when user clicks a row
    height   : optional fixed pixel height
    """

    def __init__(self, parent=None, columnas: List[tuple] = None,
                 on_select=None, height: int = None):
        super().__init__(parent)
        self._columnas  = columnas or []
        self._on_select = on_select
        self._datos: List[dict] = []
        self._build(height)

    # ── Build ──────────────────────────────────────────────────────────

    def _build(self, height: Optional[int]):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        ncols = len(self._columnas)
        self._table = QTableWidget(0, ncols)
        self._table.setHorizontalHeaderLabels([c[1] for c in self._columnas])
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(False)
        self._table.horizontalHeader().setHighlightSections(False)

        # Column widths — last column stretches
        for i, (key, label, width) in enumerate(self._columnas):
            self._table.setColumnWidth(i, width)
        if self._columnas:
            self._table.horizontalHeader().setStretchLastSection(True)

        if height:
            self._table.setFixedHeight(height)

        self._table.selectionModel().selectionChanged.connect(self._on_selection)

        layout.addWidget(self._table)

    # ── Internal ───────────────────────────────────────────────────────

    def _on_selection(self, selected, _deselected):
        if self._on_select and selected.indexes():
            row = selected.indexes()[0].row()
            if 0 <= row < len(self._datos):
                self._on_select(self._datos[row])

    # ── Public API — matches the CTk Tabla interface ───────────────────

    def cargar(self, datos: List[dict]):
        """Populate the table from a list of dicts."""
        self._datos = list(datos)
        self._table.setRowCount(0)
        for row_data in self._datos:
            row = self._table.rowCount()
            self._table.insertRow(row)
            for col, (key, _label, _width) in enumerate(self._columnas):
                val = str(row_data.get(key, "") or "")
                item = QTableWidgetItem(val)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
                )
                self._table.setItem(row, col, item)
        self._table.resizeRowsToContents()

    def limpiar(self):
        self._datos = []
        self._table.setRowCount(0)

    def seleccionado(self) -> Optional[dict]:
        rows = self._table.selectionModel().selectedRows()
        if rows:
            row = rows[0].row()
            if 0 <= row < len(self._datos):
                return self._datos[row]
        return None
