# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

hiddenimports = collect_submodules('PyQt6') + [
    'controllers.cliente_controller',
    'controllers.prestamo_controller',
    'controllers.pago_controller',
    'controllers.caja_controller',
    'controllers.reporte_controller',
    'models.cliente',
    'models.prestamo',
    'models.pago',
    'models.caja',
    'models.reporte',
    'services.amortizacion',
    'services.backup',
    'services.excel_exporter',
    'services.mora_calculator',
    'services.pdf_generator',
    'services.terminal_pago',
    'database.connection',
    'database.schema',
    'database.seed',
    'views.app',
    'views.sidebar',
    'views.dashboard',
    'views.styles',
    'views.clientes.lista_clientes',
    'views.clientes.form_cliente',
    'views.clientes.perfil_cliente',
    'views.prestamos.lista_prestamos',
    'views.prestamos.form_prestamo',
    'views.prestamos.detalle_prestamo',
    'views.caja.caja_main',
    'views.caja.apertura_caja',
    'views.caja.cierre_caja',
    'views.caja.cobro_rapido',
    'views.caja.panel_terminal',
    'views.reportes.reportes_main',
    'views.configuracion',
    'views.components.modal_confirm',
    'views.components.search_bar',
    'views.components.tabla',
    'views.components.worker',
    'fpdf',
    'openpyxl',
    'flask',
    'dateutil',
]

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('assets',    'assets'),
        ('templates', 'templates'),
        ('static',    'static'),
        ('config.py', '.'),
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AGP',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,            # sin ventana de consola
    icon='assets/icon.png',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='AGP',
)
