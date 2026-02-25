# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

hiddenimports = (
    collect_submodules('flask') +
    collect_submodules('jinja2') +
    collect_submodules('werkzeug') +
    [
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
        'app_web',
        'fpdf',
        'openpyxl',
        'dateutil',
    ]
)

a = Analysis(
    ['main_web.py'],
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
    console=False,
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
