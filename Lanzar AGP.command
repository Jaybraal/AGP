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

# Verificar Flask
if ! python3 -c "import flask" &>/dev/null; then
    echo "📦  Instalando dependencias (solo la primera vez)..."
    pip3 install -r requirements.txt --quiet
    echo "✅  Dependencias instaladas."
    echo ""
fi

# Cerrar servidor anterior si existía
lsof -ti:8080 | xargs kill -9 2>/dev/null
sleep 0.5

echo "🚀  Iniciando servidor..."
python3 app_web.py &
SERVER_PID=$!

# Esperar a que el servidor arranque
sleep 2

# Abrir navegador
echo "🌐  Abriendo en el navegador: http://127.0.0.1:8080"
open http://127.0.0.1:8080

echo ""
echo "✅  Sistema corriendo. No cierres esta ventana."
echo "    Para detener el sistema, cierra esta ventana."
echo "=================================================="

# Mantener vivo hasta que el usuario cierre la ventana
wait $SERVER_PID
