#!/bin/bash
# ─────────────────────────────────────────────────────────────
#  AGP — Script de Instalación (ejecutar UNA sola vez)
# ─────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=================================================="
echo "   AGP — Instalación del Sistema"
echo "=================================================="
echo ""

# 1. Verificar Python 3
echo "🔍  Verificando Python 3..."
if ! command -v python3 &>/dev/null; then
    echo ""
    echo "❌  Python 3 no está instalado."
    echo ""
    echo "    1. Ve a: https://www.python.org/downloads/"
    echo "    2. Descarga e instala Python 3"
    echo "    3. Vuelve a ejecutar este script"
    echo ""
    read -p "Presiona Enter para cerrar..."
    exit 1
fi
PYVER=$(python3 --version)
echo "✅  $PYVER encontrado"

# 2. Instalar dependencias
echo ""
echo "📦  Instalando dependencias..."
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo ""
    echo "❌  Error instalando dependencias."
    echo "    Intenta ejecutar manualmente:"
    echo "    pip3 install flask fpdf2 openpyxl python-dateutil"
    read -p "Presiona Enter para cerrar..."
    exit 1
fi
echo "✅  Dependencias instaladas"

# 3. Crear lanzador en escritorio
echo ""
echo "🖥️   Creando acceso directo en el Escritorio..."
chmod +x "Lanzar AGP.command"
cp "Lanzar AGP.command" ~/Desktop/
chmod +x ~/Desktop/"Lanzar AGP.command"
echo "✅  Lanzador creado en el Escritorio"

# 4. Inicializar base de datos
echo ""
echo "🗄️   Inicializando base de datos..."
python3 -c "from database.schema import inicializar; inicializar(); print('✅  Base de datos lista')"

echo ""
echo "=================================================="
echo "   ✅  INSTALACIÓN COMPLETADA"
echo ""
echo "   Para usar el sistema:"
echo "   → Doble clic en 'Lanzar AGP' en el Escritorio"
echo "=================================================="
echo ""
read -p "Presiona Enter para cerrar..."
