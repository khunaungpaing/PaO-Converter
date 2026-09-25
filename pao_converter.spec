# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build specification for Pa-O Converter."""

import os
import sys
from pathlib import Path

# Add project root to sys.path so we can import version
ROOT = Path(SPECPATH).resolve()
sys.path.insert(0, str(ROOT))

from core.version import __version__, APP_NAME, APP_ID

block_cipher = None

# Platform-specific icon selection
if sys.platform == "darwin":
    icon_file = os.path.join("assets", "img", "app.icns")
elif sys.platform.startswith("win"):
    icon_file = os.path.join("assets", "img", "app.ico")
else:
    icon_file = os.path.join("assets", "img", "app.png")

a = Analysis(
    ['main.py'],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        ('assets/fonts/*.ttf', 'assets/fonts'),
        ('assets/img/*.png', 'assets/img'),
        ('assets/img/*.icns', 'assets/img'),
        ('assets/img/*.ico', 'assets/img'),
        ('LICENSE', '.'),
    ],
    hiddenimports=[
        'docx',
        'fitz',
        'regex',
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'scipy'],
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
    name='PaOConverter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PaOConverter',
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name='PaOConverter.app',
        icon='assets/img/app.icns',
        bundle_identifier=APP_ID,
        info_plist={
            'CFBundleName': APP_NAME,
            'CFBundleDisplayName': APP_NAME,
            'CFBundleIdentifier': APP_ID,
            'CFBundleVersion': __version__,
            'CFBundleShortVersionString': __version__,
            'NSHighResolutionCapable': True,
            'LSMinimumSystemVersion': '10.15.0',
            'NSHumanReadableCopyright': '© 2026 Pa-O Language Community',
        },
    )
