"""Ponto de entrada do executavel: sobe o Streamlit e abre o navegador.

Este arquivo so e usado na geracao do .exe. Para rodar o projeto a partir do
codigo, continue usando `streamlit run app.py`.
"""

from __future__ import annotations

import os
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path

PORTA = 8501


def raiz() -> Path:
    """Pasta com app.py e a planilha. No .exe, e a pasta temporaria do PyInstaller."""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parent.parent


def porta_livre(porta: int) -> bool:
    with socket.socket() as s:
        return s.connect_ex(("127.0.0.1", porta)) != 0


def escolher_porta() -> int:
    """Evita falhar caso a 8501 ja esteja ocupada por outro programa."""
    for porta in range(PORTA, PORTA + 20):
        if porta_livre(porta):
            return porta
    return PORTA


def abrir_quando_subir(porta: int) -> None:
    url = f"http://localhost:{porta}"
    for _ in range(90):
        time.sleep(1)
        if not porta_livre(porta):
            webbrowser.open(url)
            print(f"\n  Painel aberto em {url}")
            print("  Para encerrar, feche esta janela.\n")
            return
    print("\n  Nao foi possivel iniciar o painel. Tente executar novamente.\n")


def main() -> int:
    base = raiz()
    os.chdir(base)
    sys.path.insert(0, str(base))

    porta = escolher_porta()
    print("  Preparando o Painel de Vendas. O navegador abre em alguns segundos...")
    threading.Thread(target=abrir_quando_subir, args=(porta,), daemon=True).start()

    from streamlit.web import cli as stcli

    sys.argv = [
        "streamlit",
        "run",
        str(base / "app.py"),
        f"--server.port={porta}",
        "--server.headless=true",
        "--global.developmentMode=false",
        # Sem codigo-fonte para vigiar dentro do .exe, o watcher so causaria erro.
        "--server.fileWatcherType=none",
        "--browser.gatherUsageStats=false",
    ]
    return stcli.main()


if __name__ == "__main__":
    sys.exit(main())
