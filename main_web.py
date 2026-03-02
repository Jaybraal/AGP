"""Lanzador web — Flask en hilo + QWebEngineView (ventana de escritorio nativa, sin pythonnet)."""

import os, sys, threading, socket

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import RECEIPTS_DIR, REPORTS_DIR, APP_WIDTH, APP_HEIGHT, APP_MIN_W, APP_MIN_H, APP_TITLE, ASSETS_DIR
from database.schema import crear_tablas
from database.seed import insertar_defaults

PORT = 8080


def _liberar_puerto():
    """En Windows, mata cualquier proceso que esté usando el puerto antes de arrancar."""
    if sys.platform != "win32":
        return
    try:
        import subprocess
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True, text=True
        )
        for line in result.stdout.splitlines():
            if f":{PORT}" in line and "LISTENING" in line:
                parts = line.split()
                pid = parts[-1]
                if pid.isdigit() and int(pid) != os.getpid():
                    subprocess.run(["taskkill", "/PID", pid, "/F"],
                                   capture_output=True)
                    break
    except Exception:
        pass


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
    _liberar_puerto()
    bootstrap()

    # Arrancar Flask en hilo daemon ANTES de iniciar Qt
    threading.Thread(target=_iniciar_flask, daemon=True).start()

    from PyQt6.QtWidgets import QApplication, QMainWindow
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebEngineCore import QWebEngineProfile
    from PyQt6.QtCore import QUrl, QTimer
    from PyQt6.QtGui import QIcon

    qt_app = QApplication(sys.argv)

    # Perfil sin persistencia de cookies ni caché — cada apertura empieza limpia
    profile = QWebEngineProfile(qt_app)
    profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.NoCache)

    # Ventana principal
    window = QMainWindow()
    window.setWindowTitle(APP_TITLE)
    window.resize(APP_WIDTH, APP_HEIGHT)
    window.setMinimumSize(APP_MIN_W, APP_MIN_H)

    # Ícono si existe
    icon_path = os.path.join(ASSETS_DIR, "icon.png")
    if os.path.exists(icon_path):
        window.setWindowIcon(QIcon(icon_path))

    # Vista web embebida — usa perfil sin persistencia
    from PyQt6.QtWebEngineCore import QWebEnginePage
    page = QWebEnginePage(profile)
    web = QWebEngineView()
    web.setPage(page)
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
