"""Lanzador web — Flask en hilo + QWebEngineView (ventana de escritorio nativa, sin pythonnet)."""

import os, sys, threading, socket

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import RECEIPTS_DIR, REPORTS_DIR, APP_WIDTH, APP_HEIGHT, APP_MIN_W, APP_MIN_H, APP_TITLE, ASSETS_DIR
from database.schema import crear_tablas
from database.seed import insertar_defaults

PORT = 8080


def bootstrap():
    os.makedirs(RECEIPTS_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)
    crear_tablas()
    insertar_defaults()


def _iniciar_flask():
    from app_web import app
    import traceback as tb

    @app.errorhandler(Exception)
    def handle_exception(e):
        return (
            f"<pre style='color:red;padding:20px'>ERROR:\n{tb.format_exc()}</pre>",
            500,
        )

    app.run(debug=False, port=PORT, host="127.0.0.1", use_reloader=False)


if __name__ == "__main__":
    bootstrap()

    # Arrancar Flask en hilo daemon ANTES de iniciar Qt
    threading.Thread(target=_iniciar_flask, daemon=True).start()

    from PyQt6.QtWidgets import QApplication, QMainWindow
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebEngineCore import QWebEngineProfile
    from PyQt6.QtCore import QUrl, QTimer
    from PyQt6.QtGui import QIcon

    qt_app = QApplication(sys.argv)

    # Ventana principal
    window = QMainWindow()
    window.setWindowTitle(APP_TITLE)
    window.resize(APP_WIDTH, APP_HEIGHT)
    window.setMinimumSize(APP_MIN_W, APP_MIN_H)

    # Ícono si existe
    icon_path = os.path.join(ASSETS_DIR, "logo.png")
    if os.path.exists(icon_path):
        window.setWindowIcon(QIcon(icon_path))

    # Vista web embebida
    web = QWebEngineView()
    window.setCentralWidget(web)
    window.show()

    # Pantalla de carga mientras Flask inicia
    web.setHtml("""<!DOCTYPE html>
<html>
<body style="margin:0;display:flex;align-items:center;justify-content:center;
             height:100vh;font-family:'Segoe UI',sans-serif;
             background:#1E3A8A;color:white;">
  <div style="text-align:center">
    <div style="font-size:3rem;font-weight:bold;margin-bottom:.5rem">AGP</div>
    <div style="font-size:1rem;opacity:.7;margin-bottom:1rem">Sistema de Gestión de Préstamos</div>
    <div style="font-size:.8rem;opacity:.4">Iniciando sistema...</div>
  </div>
</body>
</html>""")

    # Sondear el puerto cada 200ms y cargar cuando Flask esté listo
    _timer = QTimer()

    def _check_flask():
        try:
            with socket.create_connection(("127.0.0.1", PORT), timeout=0.3):
                _timer.stop()
                web.setUrl(QUrl(f"http://127.0.0.1:{PORT}"))
        except OSError:
            pass

    _timer.timeout.connect(_check_flask)
    _timer.start(200)

    sys.exit(qt_app.exec())
