# -*- mode: python ; coding: utf-8 -*-
# sb3_converter.spec – PyInstaller build configuration
#
# Build commands:
#   Windows : pyinstaller sb3_converter.spec
#   macOS   : pyinstaller sb3_converter.spec
#   Linux   : pyinstaller sb3_converter.spec
#
# Output ends up in  dist/SB3Converter[.exe]

import sys
import platform

block_cipher = None

# The single source-of-truth for the app name across all platforms
APP_NAME = "SB3Converter"

a = Analysis(
    # Entry point – uses the package CLI module
    ["sb3_converter/cli.py"],
    pathex=["."],
    binaries=[],
    datas=[
        # Bundle the web UI so users can open index.html from the dist folder
        ("index.html", "."),
    ],
    hiddenimports=[
        "tkinter",
        "tkinter.filedialog",
        "tkinter.messagebox",
    ],
    hookspath=[],
    hooksconfig={},
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # no terminal window on Windows/macOS
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Windows-specific: embed a manifest for high-DPI awareness
    uac_admin=False,
)

# macOS: wrap the executable in a .app bundle
if platform.system() == "Darwin":
    app = BUNDLE(
        exe,
        name=f"{APP_NAME}.app",
        icon=None,
        bundle_identifier="com.suisbetter.sb3converter",
        info_plist={
            "NSHighResolutionCapable": True,
            "CFBundleShortVersionString": "1.0.0",
            "CFBundleVersion": "1.0.0",
        },
    )
