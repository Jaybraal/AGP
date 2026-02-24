@echo off
chcp 65001 > nul
title Instalador AGP - Sistema de Prestamos

echo ================================================
echo   Instalador del Sistema de Gestion de Prestamos
echo ================================================
echo.

:: Verify Python is available
python --version > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no encontrado.
    echo.
    echo Por favor instala Python 3.11 o superior desde:
    echo   https://www.python.org/downloads/
    echo.
    echo IMPORTANTE: Marca la opcion "Add Python to PATH" durante la instalacion.
    echo.
    pause
    exit /b 1
)

echo [OK] Python encontrado:
python --version
echo.

:: Install dependencies
echo Instalando dependencias...
echo.
python -m pip install --upgrade pip --quiet
python -m pip install PyQt6 flask python-dateutil fpdf2 openpyxl --quiet

if errorlevel 1 (
    echo [ERROR] Fallo la instalacion de dependencias.
    echo Verifica tu conexion a Internet e intenta de nuevo.
    pause
    exit /b 1
)

echo [OK] Dependencias instaladas correctamente.
echo.

:: Create desktop shortcut using VBScript
echo Creando acceso directo en el Escritorio...
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

(
echo Set oWS = WScript.CreateObject^("WScript.Shell"^)
echo sLinkFile = oWS.SpecialFolders^("Desktop"^) ^& "\AGP Sistema de Prestamos.lnk"
echo Set oLink = oWS.CreateShortcut^(sLinkFile^)
echo oLink.TargetPath = "pythonw.exe"
echo oLink.Arguments = """%SCRIPT_DIR%\main.py"""
echo oLink.WorkingDirectory = "%SCRIPT_DIR%"
echo oLink.Description = "Sistema de Gestion de Prestamos AGP"
echo oLink.Save
) > "%TEMP%\crear_acceso.vbs"

cscript //nologo "%TEMP%\crear_acceso.vbs"
del "%TEMP%\crear_acceso.vbs"

echo [OK] Acceso directo creado en el Escritorio.
echo.
echo ================================================
echo   Instalacion completada con exito!
echo ================================================
echo.
echo Puedes iniciar el sistema desde:
echo   - El acceso directo "AGP Sistema de Prestamos" en el Escritorio
echo   - O ejecutando "ejecutar_agp.bat" en esta carpeta
echo.
pause
