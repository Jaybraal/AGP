import sqlite3
import os
import threading
from config import DB_PATH

# Cada hilo tiene su propia conexión para evitar deadlocks
_local = threading.local()


def get_connection() -> sqlite3.Connection:
    if not hasattr(_local, "conn") or _local.conn is None:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        _local.conn = conn
    return _local.conn


def close_connection():
    if hasattr(_local, "conn") and _local.conn:
        _local.conn.close()
        _local.conn = None
