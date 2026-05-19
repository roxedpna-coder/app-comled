#!/bin/bash
# Lanzador local COM.LED para macOS

echo "============================================"
echo "🚀 INICIANDO APLICACIÓN COM.LED (LOCAL)"
echo "============================================"

# 1. Comprobar si existe entorno virtual
if [ ! -d "venv" ]; then
    echo "📦 Creando entorno virtual local..."
    python3 -m venv venv
fi

# 2. Activar entorno virtual
source venv/bin/activate

# 3. Instalar dependencias si es necesario
echo "🔌 Verificando dependencias..."
pip install -q -r requirements.txt

# 4. Abrir la interfaz en el navegador
echo "💻 Abriendo interfaz en el navegador..."
sleep 1
open "http://127.0.0.1:8000"

# 5. Ejecutar servidor
echo "🔥 Iniciando servidor backend..."
python3 backend/api.py
