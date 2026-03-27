# build_client.spec
import sys
from pathlib import Path

ROOT = Path(".").resolve()

a = Analysis(
    ["client/app.py"],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        ("core", "core"),
        ("client", "client"),
        ("tutoriais", "tutoriais"),
        ("tutorials.json", "."),
        ("version.json", "."),
        ("blocked_serials.json", "."),
    ],
    hiddenimports=[
        "core.editals_data",
        "core.database",
        "core.utils",
        "core.license_core",
        "core.tutorials_sync",
        "client.updater",
        "PySide6.QtMultimedia",
        "PySide6.QtMultimediaWidgets",
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="EditalSystem",
    debug=False,
    strip=False,
    upx=True,
    console=False,
    icon="assets/icon.ico" if Path("assets/icon.ico").exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name="EditalSystem",
)
