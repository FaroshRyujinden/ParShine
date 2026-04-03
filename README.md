# ParShine 🐉

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![GTK4](https://img.shields.io/badge/UI-GTK4%2FLibadwaita-62a0ea.svg)](https://www.gtk.org/)

**ParShine** is a modern, high-performance GTK4/Libadwaita frontend for managing **Sunshine** (the open-source remote desktop host) on Linux. It provides a beautiful and intuitive interface to configure your streaming server without touching complex configuration files.

[English](#-english) | [Português (Brasil)](#-português-br)

---

## 🌐 English

<img width="1920" height="1080" alt="EN" src="https://github.com/user-attachments/assets/ec9bcb74-d524-4a31-bfed-897d942315cd" />

### 🚀 Getting Started

#### 1. AppImage (Recommended)
The easiest way to run ParShine on any Linux distro without installing dependencies.
1. Download the latest `.AppImage` from the [Releases](https://github.com/FaroshRyujinden/ParShine/releases) page.
2. Make it executable:

   ```bash
   
   chmod +x ParShine-v1.0.AppImage && ./ParShine-v1.0.AppImage

3. Running from Source (Recommended for Devs)

To avoid "externally-managed-environment" errors on distros like Arch Linux, always use a virtual environment (venv).

# Clone the repository ✌️

    git clone [https://github.com/FaroshRyujinden/ParShine.git](https://github.com/FaroshRyujinden/ParShine.git)
    cd ParShine

# Create and activate the virtual environment 🖥️

    python -m venv .venv
    source .venv/bin/activate

# Install dependencies inside the environment 👨‍💻

    pip install --upgrade pip
    pip install -r requirements.txt

# Run the app 🏃‍♂️‍➡️

    python main.py

4. Features 🌟

    Dashboard: Monitor connected devices and active streaming sessions in real-time.

    PIN Pairing: Pair new Moonlight clients directly from the interface.

    Full Configuration: Video (NVENC, VA-API, Software), Input (Xbox/DS/DualSense), and Network settings.

    Advanced Options: FEC, QP parameters, CPU threads, and HEVC/AV1 support.

    System Info: Built-in hardware monitor (Distro, CPU, GPU, and RAM).

    Customization: Dynamic accent colors and Dark/Light mode support.






## 🇧🇷 Português (BR)

<img width="1920" height="1080" alt="BR" src="https://github.com/user-attachments/assets/dacee75f-793f-4bfd-b5bd-a19f8d70af56" />

ParShine é uma interface moderna e de alta performance em GTK4/Libadwaita para gerenciar o Sunshine no Linux.

### 🚀 Como Começar
### 1. AppImage (Recomendado)

A maneira mais simples de rodar em qualquer distro sem quebrar a cabeça com dependências.
1. Baixe o .AppImage mais recente na página de [Releases](https://github.com/FaroshRyujinden/ParShine/releases).
2. Dê permissão de execução com CHMOD
   
    ```bash
   
   chmod +x ParShine-v1.0.AppImage && ./ParShine-v1.0.AppImage

3. Executando via Código Fonte (Para Usuários avançados)

Para evitar erros de ambiente gerenciado pelo sistema (comum no Arch), use um ambiente virtual (venv).

# Clone o repositório ✌️

    git clone [https://github.com/FaroshRyujinden/ParShine.git](https://github.com/FaroshRyujinden/ParShine.git)
    cd ParShine

# Cria e ativa o ambiente virtual 🖥️

    python -m venv .venv
    source .venv/bin/activate

# Instala as dependências dentro do ambiente 👨‍💻

    pip install --upgrade pip
    pip install -r requirements.txt

# Roda o aplicativo 🏃‍♂️‍➡️
    
    python main.py

4. Funcionalidades 🌟

    Painel: Monitore dispositivos e sessões ativas em tempo real.

    Pareamento PIN: Pareie novos clientes Moonlight facilmente.

    Configuração Completa: Ajustes de Vídeo (NVENC, VA-API), Controles e Rede.

    Opções Avançadas: Ajustes de FEC, QP, threads de CPU e suporte a HEVC/AV1.

    Info do Sistema: Monitor de hardware integrado (Distro, CPU, GPU e Memória).

    Customização: Cores de destaque dinâmicas e suporte a Modo Escuro.


# Technologies / Tecnologias 🛠️

    Language: Python

    UI Framework: GTK4 / Libadwaita (PyGObject)

    Backend: Requests (Sunshine API)

📜 License / Licença

Distributed under the GPL v3.0 License. See LICENSE for more information.

Created with ❤️ by Farosh Ryujinden
