# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
from PyInstaller.utils.hooks import collect_all

ROOT = Path(SPECPATH)

pymupdf_datas, pymupdf_binaries, pymupdf_hiddenimports = collect_all("pymupdf")

datas = [
    (str(ROOT / "sozak_pdf_designer.html"), "."),
    (str(ROOT / "sozak-pdf-body.css"), "."),
    (str(ROOT / "README.md"), "."),
    (str(ROOT / "assets"), "assets"),
    (str(ROOT / "presets"), "presets"),
] + pymupdf_datas

a = Analysis(
    [str(ROOT / "sozak_pdf_designer.py")],
    pathex=[str(ROOT)],
    binaries=pymupdf_binaries,
    datas=datas,
    hiddenimports=pymupdf_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Sozak PDF Layout Designer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Sozak PDF Layout Designer",
)

app = BUNDLE(
    coll,
    name="Sozak PDF Layout Designer.app",
    icon=str(ROOT / "assets" / "SozakPDFLayoutDesigner.icns"),
    bundle_identifier="com.sozak.pdflayoutdesigner",
    info_plist={
        "CFBundleDisplayName": "Sozak PDF Layout Designer",
        "CFBundleName": "Sozak PDF Layout Designer",
        "CFBundleShortVersionString": "0.10.0",
        "CFBundleVersion": "0.10.0",
        "LSMinimumSystemVersion": "12.0",
        "NSHighResolutionCapable": True,
        "LSApplicationCategoryType": "public.app-category.productivity",
    },
)
