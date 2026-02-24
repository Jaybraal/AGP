"""
Automatic database backup service.
Creates timestamped SQLite backups, keeps only the last N copies.
"""

import shutil
import os
from datetime import datetime
from config import DB_PATH, BASE_DIR

BACKUP_DIR  = os.path.join(BASE_DIR, "data", "backups")
MAX_BACKUPS = 7   # Keep last 7 daily backups


def hacer_backup() -> str:
    """
    Copies the SQLite database to data/backups/ with a timestamp.
    Removes old backups beyond MAX_BACKUPS.
    Returns the path of the new backup file.
    """
    os.makedirs(BACKUP_DIR, exist_ok=True)

    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Base de datos no encontrada: {DB_PATH}")

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nombre = f"prestamos_{timestamp}.db"
    destino = os.path.join(BACKUP_DIR, nombre)

    shutil.copy2(DB_PATH, destino)

    _limpiar_backups_viejos()

    return destino


def _limpiar_backups_viejos():
    """Removes oldest backups, keeping only MAX_BACKUPS files."""
    archivos = sorted([
        os.path.join(BACKUP_DIR, f)
        for f in os.listdir(BACKUP_DIR)
        if f.startswith("prestamos_") and f.endswith(".db")
    ])
    while len(archivos) > MAX_BACKUPS:
        os.remove(archivos.pop(0))


def listar_backups() -> list:
    """Returns list of backup dicts with name, path, size and date."""
    if not os.path.exists(BACKUP_DIR):
        return []
    backups = []
    for f in sorted(os.listdir(BACKUP_DIR), reverse=True):
        if f.startswith("prestamos_") and f.endswith(".db"):
            path = os.path.join(BACKUP_DIR, f)
            stat = os.stat(path)
            backups.append({
                "nombre": f,
                "path":   path,
                "tamaño": f"{stat.st_size / 1024:.1f} KB",
                "fecha":  datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
            })
    return backups
