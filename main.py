import os
import sys

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import RECEIPTS_DIR, REPORTS_DIR
from database.schema import crear_tablas
from database.seed import insertar_defaults


def bootstrap():
    """Initialize database and required directories."""
    os.makedirs(RECEIPTS_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)
    crear_tablas()
    insertar_defaults()
    _backup_al_iniciar()


def _backup_al_iniciar():
    import threading
    def _run():
        try:
            from services.backup import hacer_backup
            hacer_backup()
        except Exception:
            pass
    threading.Thread(target=_run, daemon=True).start()


def main():
    bootstrap()

    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtGui import QFont
    from views.styles import QSS

    app = QApplication(sys.argv)
    app.setStyleSheet(QSS)

    # Default application font
    font = QFont("Segoe UI", 12)
    app.setFont(font)

    from views.app import App
    window = App()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
