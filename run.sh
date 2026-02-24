#!/bin/bash
# AGP — Sistema de Gestión de Préstamos
# Script de lanzamiento para macOS

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON="/Library/Frameworks/Python.framework/Versions/3.11/bin/python3"
LOG="$APP_DIR/data/agp_launch.log"

mkdir -p "$APP_DIR/data"

# Verificar Python
if [ ! -f "$PYTHON" ]; then
    PYTHON="$(which python3)"
fi

if [ -z "$PYTHON" ] || [ ! -f "$PYTHON" ]; then
    echo "ERROR: Python 3 no encontrado." | tee -a "$LOG"
    exit 1
fi

echo "[$(date)] Iniciando AGP con $PYTHON" >> "$LOG"

cd "$APP_DIR"
exec "$PYTHON" main.py
