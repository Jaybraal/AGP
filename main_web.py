"""Lanzador web para Windows — Flask en hilo + pywebview (ventana nativa)."""

import os, sys, threading, time, socket, traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import (
    RECEIPTS_DIR, REPORTS_DIR,
    APP_TITLE, APP_WIDTH, APP_HEIGHT, APP_MIN_W, APP_MIN_H,
)
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

    @app.errorhandler(Exception)
    def handle_exception(e):
        return (
            f"<pre style='color:red;padding:20px'>"
            f"ERROR:\n{traceback.format_exc()}"
            f"</pre>",
            500,
        )

    app.run(debug=False, port=PORT, host="127.0.0.1", use_reloader=False)


def _esperar_flask(timeout=15):
    """Espera hasta que Flask acepte conexiones."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", PORT), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.1)
    return False


if __name__ == "__main__":
    bootstrap()

    threading.Thread(target=_iniciar_flask, daemon=True).start()
    _esperar_flask()

    import webview
    webview.create_window(
        APP_TITLE,
        f"http://127.0.0.1:{PORT}",
        width=APP_WIDTH,
        height=APP_HEIGHT,
        min_size=(APP_MIN_W, APP_MIN_H),
    )
    webview.start()
