@echo off
title Lanzador local COM.LED - Windows
chcp 65001 > nul

echo ============================================
echo  INICIANDO APLICACION COM.LED (LOCAL)
echo ============================================

:: 1. Comprobar si Python esta instalado
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python no esta instalado o no se encuentra en el PATH.
    echo Por favor, instala Python 3.8 o superior y marca la opcion "Add Python to PATH" durante la instalacion.
    echo Puedes descargarlo desde: https://www.python.org/downloads/
    pause
    exit /b
)

:: 2. Crear entorno virtual si no existe
if not exist venv (
    echo [INFO] Creando entorno virtual local...
    python -m venv venv
)

:: 3. Activar entorno virtual
call venv\Scripts\activate.bat

:: 4. Instalar dependencias si es necesario
echo [INFO] Verificando dependencias en venv...
pip install -q -r requirements.txt

:: 5. Abrir la interfaz en el navegador predeterminado
echo [INFO] Abriendo la aplicacion visual...
timeout /t 1 /nobreak > nul
start http://127.0.0.1:8000

:: 6. Ejecutar servidor
echo [INFO] Iniciando servidor backend...
python backend/api.py
pause
