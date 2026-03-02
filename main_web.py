"""Lanzador web — Flask en hilo + tkinter como ventana de control."""

import os
import sys
import threading
import socket
import time
import webbrowser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import RECEIPTS_DIR, REPORTS_DIR, APP_TITLE
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
    inicio = time.time()
    while time.time() - inicio < timeout:
        try:
            with socket.create_connection(("127.0.0.1", PORT), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.2)
    return False


def _abrir_navegador():
    webbrowser.open(f"http://127.0.0.1:{PORT}")


if __name__ == "__main__":
    _liberar_puerto()
    bootstrap()

    # Arrancar Flask en hilo daemon
    threading.Thread(target=_iniciar_flask, daemon=True).start()

    # Esperar a que Flask esté listo
    _esperar_flask()

    # Abrir el navegador del sistema automáticamente
    _abrir_navegador()

    # Ventana de control con tkinter (viene incluido en Python, sin dependencias extra)
    import tkinter as tk

    root = tk.Tk()
    root.title(APP_TITLE)
    root.geometry("320x140")
    root.resizable(False, False)
    # Centrar en pantalla
    root.eval("tk::PlaceWindow . center")

    frame = tk.Frame(root, padx=20, pady=16)
    frame.pack(fill="both", expand=True)

    tk.Label(
        frame,
        text="AGP — Sistema de Gestión de Préstamos",
        font=("Segoe UI", 10, "bold"),
        wraplength=280,
        justify="center",
    ).pack(pady=(0, 4))

    tk.Label(
        frame,
        text="El sistema está corriendo en tu navegador.",
        font=("Segoe UI", 9),
        fg="#555",
    ).pack()

    tk.Button(
        frame,
        text="Abrir en el navegador",
        command=_abrir_navegador,
        font=("Segoe UI", 9),
        bg="#2563EB",
        fg="white",
        relief="flat",
        padx=14,
        pady=6,
        cursor="hand2",
    ).pack(pady=(12, 0))

    # Al cerrar la ventana se cierra todo (Flask es daemon)
    root.mainloop()
