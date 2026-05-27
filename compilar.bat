@echo off
title Compilador COM.LED a Ejecutable Standalone (.exe)
chcp 65001 > nul

echo ============================================================
echo  COMPILANDO COM.LED A APLICACION DE ESCRITORIO (.EXE)
echo ============================================================
echo.

:: 1. Verificar si Python esta instalado
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python no esta instalado o no se encuentra en el PATH.
    echo Por favor, instala Python 3.8 o superior antes de compilar.
    pause
    exit /b
)

:: 2. Crear y activar entorno virtual si no existe
if not exist venv (
    echo [INFO] Creando entorno virtual local...
    python -m venv venv
)
call venv\Scripts\activate.bat

:: 3. Instalar dependencias necesarias
echo [INFO] Instalando dependencias del proyecto...
pip install -r requirements.txt
echo [INFO] Instalando PyInstaller para la compilacion...
pip install pyinstaller

:: 4. Ejecutar la compilacion con PyInstaller
echo.
echo [INFO] Compilando archivo ejecutable unico (.exe)...
echo Esto puede tomar un par de minutos, por favor espera...
echo.

pyinstaller --name="COM-LED" ^
            --onefile ^
            --noconsole ^
            --copy-metadata pymatting ^
            --copy-metadata rembg ^
            --add-data ".env;." ^
            --add-data "frontend;frontend" ^
            --add-data "plantillas;plantillas" ^
            --add-data "backend;backend" ^
            --icon="frontend/icon-512.png" ^
            backend/api.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Hubo un problema al compilar la aplicacion.
    pause
    exit /b
)

echo.
echo ============================================================
echo  COMPILACION COMPLETADA EXITOSAMENTE!
echo ============================================================
echo.
echo Encontraras tu aplicacion lista para usar en la carpeta:
echo   =^> dist\COM-LED.exe
echo.
echo Puedes mover ese archivo "COM-LED.exe" a donde quieras,
echo por ejemplo a tu Escritorio o Barra de Tareas.
echo Al abrirlo, se levantara el servidor y se abrira tu 
echo navegador automaticamente.
echo ============================================================
echo.
pause
