"""
Verifone payment terminal service.

Modes:
  DISPLAY – shows amount on screen for operator to type manually (always works)
  SERIAL  – tries to send amount via COM port (requires pyserial + correct port)

The module is designed so that when you identify the exact Verifone model/SDK,
only this file needs to change — the UI stays the same.
"""

import threading
import time
from datetime import datetime
from database.seed import get_config

# pyserial is optional — graceful degradation if not installed
try:
    import serial
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False


class ResultadoTerminal:
    def __init__(self, aprobado: bool, codigo: str = "", mensaje: str = ""):
        self.aprobado  = aprobado
        self.codigo    = codigo   # authorization code returned by terminal
        self.mensaje   = mensaje
        self.timestamp = datetime.now().isoformat()


class TerminalPago:
    """
    Stateless helper: one instance per payment attempt.
    """

    def __init__(self):
        self.modo      = get_config("terminal_modo")    or "DISPLAY"
        self.puerto    = get_config("terminal_puerto")  or "COM1"
        self.baudrate  = int(get_config("terminal_baudrate") or 9600)
        self.habilitado = get_config("terminal_habilitado") == "1"

    # ──────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────

    def iniciar_pago(self, monto: float, referencia: str = "") -> dict:
        """
        Attempt to initiate a payment.
        Returns a status dict consumed by the UI panel.
        """
        if not self.habilitado:
            return {"ok": False, "modo": "DISPLAY", "msg": "Terminal deshabilitado — modo manual."}

        if self.modo == "SERIAL" and SERIAL_AVAILABLE:
            return self._iniciar_serial(monto, referencia)

        return {"ok": True, "modo": "DISPLAY", "msg": "Ingrese el monto en el terminal."}

    def _iniciar_serial(self, monto: float, referencia: str) -> dict:
        """
        Attempt to communicate with Verifone via serial port.
        Sends a minimal payment request and waits up to 3 seconds for ACK.

        NOTE: The exact byte sequence depends on your terminal model / bank SDK.
        This implementation sends a plain-text amount that works with some
        Verifone middleware integrations. Replace the payload if your terminal
        uses VIPA, OPI, or a bank-specific protocol.
        """
        try:
            payload = f"PAY:{monto:.2f}:REF:{referencia}\r\n".encode("ascii")
            with serial.Serial(self.puerto, self.baudrate, timeout=3) as ser:
                ser.write(payload)
                time.sleep(0.2)
                response = ser.read(64).decode("ascii", errors="ignore").strip()
            if response:
                return {"ok": True, "modo": "SERIAL", "msg": f"Terminal respondió: {response}"}
            return {"ok": True, "modo": "SERIAL", "msg": "Comando enviado. Esperando operación en terminal."}
        except Exception as e:
            return {"ok": False, "modo": "DISPLAY",
                    "msg": f"No se pudo conectar al puerto {self.puerto}. Modo manual activado. ({e})"}

    @staticmethod
    def confirmar(codigo_autorizacion: str) -> ResultadoTerminal:
        """Called by the operator after the physical terminal approves."""
        codigo = codigo_autorizacion.strip().upper()
        if codigo:
            return ResultadoTerminal(aprobado=True, codigo=codigo, mensaje="Pago aprobado.")
        return ResultadoTerminal(aprobado=False, codigo="", mensaje="Sin código — pago no confirmado.")

    @staticmethod
    def rechazar(motivo: str = "") -> ResultadoTerminal:
        return ResultadoTerminal(aprobado=False, codigo="", mensaje=motivo or "Pago rechazado.")
