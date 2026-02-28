#!/bin/bash
# ─────────────────────────────────────────────────────────────
#  AGP — Lanzador del Sistema de Gestión de Préstamos
#  Doble clic para iniciar · Cierra la ventana para detener
# ─────────────────────────────────────────────────────────────

# Ir a la carpeta del proyecto (donde está este script)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=================================================="
echo "   AGP — Sistema de Gestión de Préstamos"
echo "=================================================="
echo ""

# Verificar Python
if ! command -v python3 &>/dev/null; then
    echo "❌  Python 3 no está instalado."
    echo "    Descárgalo en: https://www.python.org/downloads/"
    read -p "Presiona Enter para cerrar..."
    exit 1
fi

# Verificar dependencias
if ! python3 -c "import flask" &>/dev/null; then
    echo "📦  Instalando dependencias (solo la primera vez)..."
    pip3 install -r requirements.txt --quiet
    echo "✅  Dependencias instaladas."
    echo ""
fi

# Cerrar servidor anterior si existía
lsof -ti:8080 | xargs kill -9 2>/dev/null
sleep 0.5

echo "🚀  Iniciando aplicación de escritorio..."
python3 main_web.py

echo ""
echo "✅  Aplicación cerrada."
