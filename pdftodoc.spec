# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import collect_all, copy_metadata


ROOT = Path.cwd()
MODEL_NAMES = ("PP-OCRv5_server_det", "PP-OCRv5_server_rec")


def model_datas():
    base = ROOT / "assets" / "models" / "official_models"
    items = []
    for name in MODEL_NAMES:
        model_dir = base / name
        for path in model_dir.rglob("*"):
            if path.is_file():
                dest = Path("assets") / "models" / "official_models" / name / path.relative_to(model_dir).parent
                items.append((str(path), str(dest)))
    return items


datas = [(str(ROOT / "assets" / "app.ico"), "assets")]
datas += model_datas()
binaries = []
hiddenimports = ["_ssl"]

metadata_packages = (
    "paddlex",
    "paddleocr",
    "paddlepaddle",
    "imagesize",
    "opencv-contrib-python",
    "opencv-python-headless",
    "pyclipper",
    "pypdfium2",
    "python-bidi",
    "shapely",
)
for package in metadata_packages:
    datas += copy_metadata(package)

for package in ("paddleocr", "paddlex", "paddle"):
    collected = collect_all(package)
    datas += collected[0]
    binaries += collected[1]
    hiddenimports += collected[2]


a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="pdftodoc",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    icon=str(ROOT / "assets" / "app.ico"),
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
