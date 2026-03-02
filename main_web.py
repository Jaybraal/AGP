"""Lanzador web — Flask en hilo + Edge/Chrome en modo --app (ventana nativa)."""

import os
import sys
import subprocess
import threading
import socket
import time
import webbrowser
import secrets

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import RECEIPTS_DIR, REPORTS_DIR, APP_TITLE, APP_WIDTH, APP_HEIGHT
from database.schema import crear_tablas
from database.seed import insertar_defaults

PORT = 8080

# Directorio de perfil exclusivo de la app (evita mezclar con el navegador del usuario)
if getattr(sys, "frozen", False):
    if sys.platform == "win32":
        _APP_DATA = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "AGP")
    else:
        _APP_DATA = os.path.join(os.path.expanduser("~"), "Library", "Application Support", "AGP")
else:
    _APP_DATA = os.path.dirname(os.path.abspath(__file__))

# Clave secreta aleatoria → sesión siempre expira al cerrar la app
_SESSION_KEY = secrets.token_hex(32)


def _liberar_puerto():
    if sys.platform != "win32":
        return
    try:
        result = subprocess.run(["netstat", "-ano"], capture_output=True, text=True)
        for line in result.stdout.splitlines():
            if f":{PORT}" in line and "LISTENING" in line:
                parts = line.split()
                pid = parts[-1]
                if pid.isdigit() and int(pid) != os.getpid():
                    subprocess.run(["taskkill", "/PID", pid, "/F"], capture_output=True)
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

    app.secret_key = _SESSION_KEY   # aleatorio → login requerido en cada arranque

    @app.errorhandler(Exception)
    def handle_exception(e):
        return (
            f"<pre style='color:red;padding:20px'>ERROR:\n{tb.format_exc()}</pre>",
            500,
        )

    app.run(debug=False, port=PORT, host="127.0.0.1", use_reloader=False)


def _esperar_flask(timeout=15):
    inicio = time.time()
    while time.time() - inicio < timeout:
        try:
            with socket.create_connection(("127.0.0.1", PORT), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.2)
    return False


def _abrir_ventana_app():
    """
    Abre Edge o Chrome en modo --app con perfil exclusivo.
    Devuelve el proceso para poder esperar a que el usuario lo cierre.
    """
    url = f"http://127.0.0.1:{PORT}"
    profile_dir = os.path.join(_APP_DATA, "browser-profile")
    os.makedirs(profile_dir, exist_ok=True)

    flags = [
        f"--app={url}",
        f"--window-size={APP_WIDTH},{APP_HEIGHT}",
        f"--user-data-dir={profile_dir}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-extensions",
    ]

    # Buscar Edge (siempre presente en Windows 10 y 11)
    for path in [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]:
        if os.path.exists(path):
            return subprocess.Popen([path] + flags)

    # Chrome como alternativa
    for path in [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe"),
    ]:
        if os.path.exists(path):
            return subprocess.Popen([path] + flags)

    # macOS (desarrollo)
    if sys.platform == "darwin":
        chrome_mac = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        if os.path.exists(chrome_mac):
            return subprocess.Popen([chrome_mac] + flags)

    # Último recurso: abrir en el navegador del sistema (no queda proceso para esperar)
    webbrowser.open(url)
    return None


if __name__ == "__main__":
    _liberar_puerto()
    bootstrap()

    # Arrancar Flask en hilo daemon
    threading.Thread(target=_iniciar_flask, daemon=True).start()

    # Esperar a que Flask esté listo
    _esperar_flask()

    # Abrir la ventana en modo app y esperar a que el usuario la cierre
    proc = _abrir_ventana_app()
    if proc:
        proc.wait()   # bloquea hasta que el usuario cierra la ventana → Flask (daemon) se detiene
    else:
        # Fallback sin proceso: mantener Flask vivo hasta Ctrl+C
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
