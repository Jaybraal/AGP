"""Lanzador web para Windows — inicia Flask y abre el navegador."""

import os, sys, threading, webbrowser, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import RECEIPTS_DIR, REPORTS_DIR
from database.schema import crear_tablas
from database.seed import insertar_defaults


def bootstrap():
    os.makedirs(RECEIPTS_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)
    crear_tablas()
    insertar_defaults()


def _abrir_navegador():
    time.sleep(2)
    webbrowser.open("http://127.0.0.1:8080")


if __name__ == "__main__":
    bootstrap()
    threading.Thread(target=_abrir_navegador, daemon=True).start()
    from app_web import app
    import traceback

    @app.errorhandler(Exception)
    def handle_exception(e):
        return (
            f"<pre style='color:red;padding:20px'>"
            f"ERROR:\n{traceback.format_exc()}"
            f"</pre>",
            500,
        )

    app.run(debug=False, port=8080, host="127.0.0.1", use_reloader=False)
