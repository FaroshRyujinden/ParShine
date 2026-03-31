import pystray
from PIL import Image
import sys
import os
import subprocess

# Config
LOGO_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "logo.png"))

def on_quit(icon, item):
    """Fecha o ícone da bandeja e pode encerrar o Sunshine se desejado"""
    icon.stop()
    # Opcional: Matar o sunshine ao fechar a bandeja
    # subprocess.run(["pkill", "sunshine"])
    sys.exit(0)

def on_open_panel(icon, item):
    """Reabre a interface principal do Projeto P"""
    subprocess.Popen(["python3", "main.py"])

def on_restart_sunshine(icon, item):
    """Reinicia o serviço do Sunshine"""
    subprocess.run(["pkill", "sunshine"])
    subprocess.Popen(["sunshine"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def setup_tray():
    try:
        if not os.path.exists(LOGO_PATH):
            print(f"Erro: Logo não encontrado em {LOGO_PATH}")
            return

        image = Image.open(LOGO_PATH)
        menu = pystray.Menu(
            pystray.MenuItem('Abrir Painel Projeto P', on_open_panel, default=True),
            pystray.MenuItem('Reiniciar Sunshine', on_restart_sunshine),
            pystray.Menu.Separator(),
            pystray.MenuItem('Fechar Bandeja', on_quit)
        )
        icon = pystray.Icon("projeto_p_sunshine", image, "Sunshine (Projeto P)", menu)
        icon.run()
    except Exception as e:
        print(f"Erro no serviço de bandeja Sunshine: {e}")

if __name__ == "__main__":
    setup_tray()
