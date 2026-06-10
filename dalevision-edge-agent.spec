# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules


repo_root = Path.cwd()
src_root = repo_root / "src"


a = Analysis(
    ['src\\run_agent.py'],
    pathex=[str(src_root)],
    binaries=[],
    datas=[
        ('scripts\\install-service.ps1', 'scripts'),
        ('scripts\\install-user.ps1', 'scripts'),
        ('scripts\\uninstall-service.ps1', 'scripts'),
        ('scripts\\uninstall-user.ps1', 'scripts'),
        ('scripts\\verify-service.ps1', 'scripts'),
        ('scripts\\update.ps1', 'scripts'),
        ('scripts\\internal\\Start_DaleVision_Agent.ps1', 'scripts\\internal'),
        ('scripts\\internal\\Start_DaleVision_Agent.bat', 'scripts\\internal'),
        ('release\\run_agent.cmd', '.'),
    ],
    hiddenimports=collect_submodules('dalevision_edge_agent') + [
        'lap',
        'charset_normalizer',
        'chardet',
    ],
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
    name='dalevision-edge-agent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
