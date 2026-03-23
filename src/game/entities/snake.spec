# snake.spec
# Ficheiro de configuracao do PyInstaller.
#
# Como usar:
#   pyinstaller snake.spec
#
# Gera a pasta dist/ com o executavel Snake.exe (Windows)
# ou Snake (Linux/Mac) pronto a distribuir.

import sys
from pathlib import Path

bloco_cifra = None

# Raiz do projecto (onde este .spec esta)
RAIZ = Path(SPECPATH)

a = Analysis(
    # Ponto de entrada
    [str(RAIZ / 'main.py')],

    # PyInstaller precisa de saber onde esta o codigo fonte
    pathex=[str(RAIZ / 'src')],

    binaries=[],

    # Assets a incluir: (caminho_origem, pasta_destino_no_exe)
    datas=[
        (str(RAIZ / 'assets'), 'assets'),
    ],

    # Modulos que o PyInstaller nao deteta automaticamente
    hiddenimports=[
        'pygame',
        'game.core.caminhos',
        'game.core.records',
        'game.core.assets',
        'game.core.engine',
        'game.core.score',
        'game.maps.map',
        'game.maps.map_renderer',
        'game.modes.base_mode',
        'game.modes.og_snake',
        'game.modes.modo_1v1',
        'game.modes.player_vs_ai',
        'game.entities.snake',
        'game.entities.food',
        'game.entities.boost',
        'game.ui.menu',
        'game.ui.hud',
        'game.ui.ui_utils',
    ],

    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=bloco_cifra,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=bloco_cifra)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Snake',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,           # comprime o exe (precisa do UPX instalado, opcional)
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,      # False = sem janela de terminal a aparecer por tras
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Descomenta a linha abaixo se tiveres um icone .ico em assets/images/
    # icon=str(RAIZ / 'assets' / 'images' / 'icone.ico'),
)
