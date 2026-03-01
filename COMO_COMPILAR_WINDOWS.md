# Cómo generar AGP-Installer.exe para Windows

## Lo que necesitas (una sola vez)
1. Una PC o VM con Windows
2. Python 3.11 instalado + dependencias (`pip install -r requirements.txt`)
3. PyInstaller: `pip install pyinstaller`
4. Inno Setup: descargar gratis en https://jrsoftware.org/isdl.php

---

## Paso 1 — Compilar la app con PyInstaller

En la carpeta del proyecto, ejecuta:
```
pyinstaller AGP-windows.spec
```
Esto genera la carpeta `dist\AGP\` con el `.exe` y todos sus archivos.

---

## Paso 2 — (Opcional) Convertir ícono

Si quieres ícono personalizado en el instalador:
- Ve a https://convertico.com
- Sube `assets/icon.png` → descarga `icon.ico`
- Guárdalo en `assets/icon.ico`
- En `AGP-installer.iss`, descomenta la línea `SetupIconFile=assets\icon.ico`

---

## Paso 3 — Crear el instalador con Inno Setup

1. Abre **Inno Setup Compiler**
2. Abre el archivo `AGP-installer.iss`
3. Presiona **F9** (o menú Build → Compile)
4. Se genera: `AGP-Installer.exe` en la carpeta del proyecto

---

## Paso 4 — Entregar al cliente

Solo envías **un archivo**: `AGP-Installer.exe`

El cliente:
1. Descarga el archivo
2. Doble clic → instala
3. Icono en el Escritorio → listo

---

## Notas
- El instalador incluye TODO: no requiere Python ni nada adicional
- Los datos de la base de datos se guardan en la carpeta de instalación
- Para actualizar la app, sube la versión en `AppVersion` del `.iss` y recompila
