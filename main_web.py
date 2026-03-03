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

_PORT_BASE = 8080

if getattr(sys, "frozen", False):
    if sys.platform == "win32":
        _APP_DATA = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "AGP")
    else:
        _APP_DATA = os.path.join(os.path.expanduser("~"), "Library", "Application Support", "AGP")
else:
    _APP_DATA = os.path.dirname(os.path.abspath(__file__))

_SESSION_KEY = secrets.token_hex(32)


def _encontrar_puerto() -> int:
    """Busca un puerto libre desde _PORT_BASE usando solo Python puro."""
    for port in range(_PORT_BASE, _PORT_BASE + 20):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(("127.0.0.1", port))
                return port
        except OSError:
            continue
    return _PORT_BASE


PORT = _encontrar_puerto()


def bootstrap():
    os.makedirs(RECEIPTS_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)
    crear_tablas()
    insertar_defaults()


def _iniciar_flask():
    import traceback as tb

    _LOG = os.path.join(_APP_DATA, "agp_error.log")

    def _log(msg: str):
        try:
            os.makedirs(_APP_DATA, exist_ok=True)
            with open(_LOG, "a", encoding="utf-8") as f:
                from datetime import datetime
                f.write(f"[{datetime.now().isoformat()}] {msg}\n")
        except Exception:
            pass

    try:
        from app_web import app
    except Exception:
        err = tb.format_exc()
        _log(f"ERROR al importar app_web:\n{err}")
        raise

    app.secret_key = _SESSION_KEY

    @app.errorhandler(Exception)
    def handle_exception(e):
        err = tb.format_exc()
        _log(f"ERROR en ruta:\n{err}")
        return (
            f"<pre style='color:red;padding:20px;font-size:13px'>"
            f"ERROR — revisa {_LOG}\n\n{err}</pre>",
            500,
        )

    _log("Flask iniciando OK")
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


def _buscar_edge():
    """Busca msedge.exe en Windows usando múltiples métodos."""
    import shutil

    # 1. shutil.which (respeta PATH del sistema)
    found = shutil.which("msedge")
    if found:
        return found

    # 2. Registro de Windows
    try:
        import winreg
        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe"
        ) as key:
            path = winreg.QueryValue(key, None)
            if path and os.path.exists(path):
                return path
    except Exception:
        pass

    # 3. Rutas comunes
    rutas = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        os.path.join(os.environ.get("LOCALAPPDATA", ""),
                     "Microsoft", "Edge", "Application", "msedge.exe"),
        os.path.join(os.environ.get("PROGRAMFILES", ""),
                     "Microsoft", "Edge", "Application", "msedge.exe"),
        os.path.join(os.environ.get("PROGRAMFILES(X86)", ""),
                     "Microsoft", "Edge", "Application", "msedge.exe"),
    ]
    for r in rutas:
        if r and os.path.exists(r):
            return r

    return None


def _buscar_chrome():
    """Busca chrome.exe en Windows."""
    import shutil
    found = shutil.which("chrome")
    if found:
        return found
    rutas = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.join(os.environ.get("LOCALAPPDATA", ""),
                     "Google", "Chrome", "Application", "chrome.exe"),
    ]
    for r in rutas:
        if r and os.path.exists(r):
            return r
    return None


def _abrir_ventana_app():
    """
    Abre Edge o Chrome en modo --app. Devuelve el proceso Popen,
    o None si solo se pudo abrir en el navegador normal.
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
        "--disable-features=TranslateUI",
    ]

    # Windows: probar Edge primero, luego Chrome
    if sys.platform == "win32":
        exe = _buscar_edge() or _buscar_chrome()
        if exe:
            proc = subprocess.Popen([exe] + flags)
            # Dar 2 segundos para ver si el proceso sigue corriendo
            time.sleep(2)
            if proc.poll() is None:
                return proc   # proceso activo → es nuestra ventana
            # Si ya terminó, Edge/Chrome lo pasó a una instancia existente;
            # en ese caso igual se abrió la ventana, solo no podemos rastrear el proceso
            return None

    # macOS (desarrollo)
    if sys.platform == "darwin":
        chrome_mac = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        if os.path.exists(chrome_mac):
            proc = subprocess.Popen([chrome_mac] + flags)
            time.sleep(2)
            if proc.poll() is None:
                return proc

    # Fallback: navegador del sistema
    webbrowser.open(url)
    return None


if __name__ == "__main__":
    bootstrap()

    threading.Thread(target=_iniciar_flask, daemon=True).start()
    _esperar_flask()

    proc = _abrir_ventana_app()

    if proc:
        # Esperar a que el usuario cierre la ventana de la app
        proc.wait()
    else:
        # Edge/Chrome pasó la ventana a una instancia ya abierta —
        # mantener Flask vivo con una ventanita mínima de tkinter
        import tkinter as tk

        root = tk.Tk()
        root.title("AGP")
        root.geometry("260x80")
        root.resizable(False, False)
        root.eval("tk::PlaceWindow . center")
        root.attributes("-topmost", True)

        f = tk.Frame(root, padx=16, pady=12)
        f.pack(fill="both", expand=True)
        tk.Label(f, text="AGP está corriendo", font=("Segoe UI", 10, "bold")).pack()
        tk.Button(
            f, text="Cerrar AGP",
            command=root.destroy,
            font=("Segoe UI", 9), bg="#DC2626", fg="white",
            relief="flat", padx=10, pady=4, cursor="hand2",
        ).pack(pady=(8, 0))

        root.mainloop()
