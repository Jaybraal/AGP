"""Lanzador web para Windows — Flask en hilo + Edge/Chrome app mode (sin barra de URL)."""

import os, sys, threading, time, socket, traceback, subprocess, webbrowser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import RECEIPTS_DIR, REPORTS_DIR, APP_WIDTH, APP_HEIGHT
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
            f"<pre style='color:red;padding:20px'>"
            f"ERROR:\n{tb.format_exc()}"
            f"</pre>",
            500,
        )

    app.run(debug=False, port=PORT, host="127.0.0.1", use_reloader=False)


def _esperar_flask(timeout=15):
    """Sondea el puerto hasta que Flask esté listo."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", PORT), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.1)
    return False


def _buscar_navegador():
    """Devuelve la ruta a Edge o Chrome si están instalados."""
    pf86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    pf   = os.environ.get("ProgramFiles",       r"C:\Program Files")
    candidatos = [
        os.path.join(pf86, r"Microsoft\Edge\Application\msedge.exe"),
        os.path.join(pf,   r"Microsoft\Edge\Application\msedge.exe"),
        os.path.join(pf86, r"Google\Chrome\Application\chrome.exe"),
        os.path.join(pf,   r"Google\Chrome\Application\chrome.exe"),
    ]
    for path in candidatos:
        if os.path.exists(path):
            return path
    return None


if __name__ == "__main__":
    bootstrap()

    threading.Thread(target=_iniciar_flask, daemon=True).start()
    _esperar_flask()

    url = f"http://127.0.0.1:{PORT}"
    exe = _buscar_navegador()

    if exe:
        # --user-data-dir propio → proceso separado → proc.wait() funciona al cerrar la ventana
        profile_dir = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "AGP", "browser-profile")
        proc = subprocess.Popen([
            exe,
            f"--app={url}",
            f"--window-size={APP_WIDTH},{APP_HEIGHT}",
            f"--user-data-dir={profile_dir}",
            "--no-first-run",
            "--no-default-browser-check",
        ])
        proc.wait()          # bloquea hasta que el usuario cierre la ventana
    else:
        # Fallback: navegador por defecto
        webbrowser.open(url)
        while True:          # mantiene Flask vivo
            time.sleep(60)
