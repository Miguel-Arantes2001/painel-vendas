# -*- mode: python ; coding: utf-8 -*-
"""Receita de build do executavel.

Gerar com:  pyinstaller executavel/PainelDeVendas.spec --noconfirm
"""

from pathlib import Path

from PyInstaller.utils.hooks import collect_all, copy_metadata

RAIZ = Path(SPECPATH).parent

# O app, o codigo e a planilha viajam dentro do executavel.
datas = [
    (str(RAIZ / "app.py"), "."),
    (str(RAIZ / "src"), "src"),
    (str(RAIZ / ".streamlit"), ".streamlit"),
    (str(RAIZ / "Vendas_Organizado.xlsx"), "."),
]
binaries = []
hiddenimports = []

# Streamlit e Plotly carregam arquivos por caminho em tempo de execucao,
# entao precisam ser coletados por inteiro.
for pacote in ("streamlit", "plotly", "openpyxl"):
    pacote_datas, pacote_binaries, pacote_hidden = collect_all(pacote)
    datas += pacote_datas
    binaries += pacote_binaries
    hiddenimports += pacote_hidden

# Streamlit le a propria versao instalada; sem os metadados ele nao inicia.
for pacote in ("streamlit", "plotly", "pandas", "numpy", "altair"):
    datas += copy_metadata(pacote)

analise = Analysis(
    [str(RAIZ / "executavel" / "iniciar.py")],
    pathex=[str(RAIZ)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["matplotlib", "PyQt5", "PySide2", "tkinter", "IPython", "notebook"],
    noarchive=False,
)

pyz = PYZ(analise.pure)

exe = EXE(
    pyz,
    analise.scripts,
    [],
    exclude_binaries=True,
    name="PainelDeVendas",
    debug=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
)

col = COLLECT(
    exe,
    analise.binaries,
    analise.datas,
    strip=False,
    upx=False,
    name="PainelDeVendas",
)
