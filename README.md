ParShine 🐉

ParShine is a modern, high-performance GTK4/Libadwaita frontend for managing Sunshine on Linux.

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![GTK4](https://img.shields.io/badge/UI-GTK4%2FLibadwaita-62a0ea.svg)](https://www.gtk.org/)

English | Português
🌐 English
🚀 Installation & Setup
1. AppImage (Recommended / Easiest)

The fastest way to run ParShine without worrying about dependencies.

    Download the latest .AppImage from the Releases page.

    Give it execution permission:
    Bash

    chmod +x ParShine-x86_64.AppImage

    Run it:
    Bash

    ./ParShine-x86_64.AppImage

2. From Source (Manual / Development)

If you prefer running from source, we recommend using a Virtual Environment (venv) to avoid system conflicts.

Prerequisites: Ensure you have python3-pip, python3-venv, and the GTK4/Libadwaita development libraries installed on your system.
Bash

# Clone the repository
git clone https://github.com/FaroshRyujinden/ParShine.git
cd ParShine

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies inside the venv
pip install --upgrade pip
pip install -r requirements.txt

# Run the app
python main.py

    Note: To run it again later, remember to run source .venv/bin/activate first.

✨ Features

    Dashboard: Real-time monitoring of connected devices.

    PIN Pairing: Direct Moonlight pairing via UI.

    Full Config: Video (NVENC, VA-API, Software), Input, and Network settings.

    System Info: Built-in hardware monitor (CPU/GPU/Mem).

    Customization: Libadwaita accent colors and Dark/Light mode support.

🇧🇷 Português (BR)
🚀 Instalação e Execução
1. AppImage (Recomendado)

A maneira mais rápida de usar o ParShine sem se preocupar com dependências de sistema.

    Baixe o .AppImage mais recente na página de Releases.

    Dê permissão de execução ao arquivo:
    Bash

    chmod +x ParShine-x86_64.AppImage

    Execute:
    Bash

    ./ParShine-x86_64.AppImage

2. Código Fonte (Manual / Desenvolvimento)

Para rodar via código, recomendamos o uso de um Ambiente Virtual (venv) para isolar as bibliotecas.

Pré-requisitos: Você precisará do python3-pip, python3-venv e das bibliotecas de desenvolvimento do GTK4/Libadwaita da sua distro.
Bash

# Clone o repositório
git clone https://github.com/FaroshRyujinden/ParShine.git
cd ParShine

# Criar e ativar o ambiente virtual
python -m venv .venv
source .venv/bin/activate

# Instalar dependências dentro do venv
pip install --upgrade pip
pip install -r requirements.txt

# Executar o projeto
python main.py

    Dica: Sempre que for rodar o código novamente, lembre-se de ativar o ambiente com source .venv/bin/activate.

✨ Funcionalidades

    Painel: Monitoramento em tempo real de dispositivos conectados.

    Pareamento PIN: Pareie o Moonlight sem abrir o navegador.

    Configuração Total: Vídeo (NVENC, VA-API), Controles e Rede.

    Info do Sistema: Monitor de hardware integrado.

    Customização: Suporte a cores de destaque e modo escuro nativo.

🛠️ Tech Stack

    Python (Logic)

    PyGObject (GTK4 / Libadwaita)

    Requests (Sunshine API communication)

📜 License / Licença

Distributed under the GPL v3.0 License.

Created with ❤️ by Farosh Ryujinden
