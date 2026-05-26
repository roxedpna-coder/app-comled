#!/bin/bash
# Compilador local COM.LED para macOS (.app / ejecutable)

echo "============================================================"
echo "🛠️ COMPILANDO COM.LED A APLICACIÓN DE ESCRITORIO MACOS"
echo "============================================================"
echo

# 1. Comprobar si existe entorno virtual
if [ ! -d "venv" ]; then
    echo "📦 Creando entorno virtual local..."
    python3 -m venv venv
fi

# 2. Activar entorno virtual
source venv/bin/activate

# 3. Instalar dependencias
echo "🔌 Instalando dependencias del proyecto..."
pip install -r requirements.txt
echo "🔌 Instalando PyInstaller para la compilación..."
pip install pyinstaller

# 4. Ejecutar la compilación
echo
echo "🚀 Compilando aplicación..."
pyinstaller --name="COM-LED" \
            --onefile \
            --noconsole \
            --add-data "frontend:frontend" \
            --add-data "plantillas:plantillas" \
            --add-data "backend:backend" \
            --icon="frontend/icon-512.png" \
            backend/api.py

if [ $? -ne 0 ]; then
    echo
    echo "❌ [ERROR] Hubo un problema al compilar la aplicación."
    exit 1
fi

echo
echo "============================================================"
echo "🎉 ¡COMPILACIÓN COMPLETADA EXITOSAMENTE!"
echo "============================================================"
echo
echo "Encontrarás tu aplicación lista para usar en la carpeta:"
echo "  => dist/COM-LED"
echo
echo "Puedes abrirla con doble clic. Al iniciar, levantará el"
echo "servidor y abrirá la interfaz en tu navegador automáticamente."
echo "============================================================"
echo
