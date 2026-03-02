"""Lanzador web — Flask en hilo + pywebview (usa WebView2/Edge en Windows, nativo en macOS)."""

import os
import sys
import threading
import socket
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import RECEIPTS_DIR, REPORTS_DIR, APP_WIDTH, APP_HEIGHT, APP_TITLE
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


def _esperar_flask(timeout=15):
    """Espera hasta que Flask esté respondiendo o se agote el tiempo."""
    inicio = time.time()
    while time.time() - inicio < timeout:
        try:
            with socket.create_connection(("127.0.0.1", PORT), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.2)
    return False


if __name__ == "__main__":
    _liberar_puerto()
    bootstrap()

    # Arrancar Flask en hilo daemon ANTES de abrir la ventana
    threading.Thread(target=_iniciar_flask, daemon=True).start()

    # Esperar a que Flask esté listo antes de abrir la ventana
    _esperar_flask()

    import webview

    # pywebview usa WebView2/Edge en Windows, WebKit en macOS/Linux
    # No requiere empaquetar Chromium — usa el motor del sistema operativo
    webview.create_window(
        title=APP_TITLE,
        url=f"http://127.0.0.1:{PORT}",
        width=APP_WIDTH,
        height=APP_HEIGHT,
        min_size=(1100, 650),
        text_select=False,
    )

    webview.start()
