; ===========================================================
;  Inno Setup Script - AGP Sistema de Gestion de Prestamos
;  Para compilar: abrir con Inno Setup Compiler en Windows
;  Requisito previo: haber corrido PyInstaller (dist/AGP/)
; ===========================================================

#define AppName      "AGP Sistema de Prestamos"
#define AppVersion   "1.0"
#define AppPublisher "AGP"
#define AppExeName   "AGP.exe"
#define AppDir       "dist\AGP"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\AGP
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir=.
OutputBaseFilename=AGP-Installer
; SetupIconFile=assets\icon.ico  <- convierte icon.png a .ico con https://convertico.com y descomenta esta linea
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
; No requiere admin si no es necesario
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
; Mostrar licencia (opcional, puedes quitar esta linea si no tienes)
; LicenseFile=LICENSE.txt
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName}

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear icono en el Escritorio"; GroupDescription: "Iconos adicionales:"; Flags: checkedonce

[Files]
; Copiar toda la carpeta compilada por PyInstaller
Source: "{#AppDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Acceso directo en el menu inicio
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"
; Acceso directo en el escritorio (si el usuario lo eligio)
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon
; Desinstalar desde el menu inicio
Name: "{group}\Desinstalar {#AppName}"; Filename: "{uninstallexe}"

[Run]
; Ejecutar la app al terminar la instalacion (opcional)
Filename: "{app}\{#AppExeName}"; Description: "Iniciar {#AppName} ahora"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Limpiar datos al desinstalar (quitar si no quieres borrar la BD)
; Type: filesandordirs; Name: "{app}\data"
