# ParShine 🐉

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![GTK4](https://img.shields.io/badge/UI-GTK4%2FLibadwaita-62a0ea.svg)](https://www.gtk.org/)

**ParShine** is a modern, high-performance GTK4/Libadwaita frontend for managing **Sunshine** (the open-source remote desktop host) on Linux. It provides a beautiful and intuitive interface to configure your streaming server without touching complex configuration files.

---

## 🌐 English

### ✨ Features
- **Dashboard:** Monitor connected devices and active streaming sessions in real-time.
- **PIN Pairing:** Easily pair new Moonlight clients directly from the interface.
- **Full Configuration:**
    - **Video:** Adjust resolutions, bitrates, FPS, and choose between NVIDIA NVENC, AMD VA-API, or Software encoders.
    - **Input:** Configure gamepads (Xbox/DS4/DS5), motion sensors, touchpad, and keyboard/mouse precision.
    - **Network:** Manage UPnP, encryption, bind addresses, and port settings.
- **Advanced Options:** FEC percentage, QP parameters, CPU threads, and HEVC/AV1 support.
- **System Info:** Built-in hardware monitor showing Distro, CPU, GPU, and Memory.
- **Customization:** Dynamic accent colors, Dark/Light mode, and support for both English and Portuguese.

### 🚀 Getting Started

#### Prerequisites
- **Sunshine** host installed and running.
- **Python 3.10+**
- **GTK4** and **Libadwaita** libraries.

#### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/farosh/parshine.git
   cd parshine
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python main.py
   ```

### 🛠️ Technologies
- **Language:** Python
- **UI Framework:** GTK4 / Libadwaita (PyGObject)
- **Backend Communication:** Requests (Sunshine API)

---

## 🇧🇷 Português

**ParShine** é uma interface moderna e de alta performance em GTK4/Libadwaita para gerenciar o **Sunshine** (servidor de desktop remoto open-source) no Linux. Ele oferece uma interface bonita e intuitiva para configurar seu servidor de streaming sem precisar editar arquivos de configuração complexos.

### ✨ Funcionalidades
- **Painel:** Monitore dispositivos conectados e sessões de streaming ativas em tempo real.
- **Pareamento via PIN:** Pareie novos clientes Moonlight facilmente direto pela interface.
- **Configuração Completa:**
    - **Vídeo:** Ajuste resoluções, bitrates, FPS e escolha entre codificadores NVIDIA NVENC, AMD VA-API ou Software.
    - **Controles:** Configure gamepads (Xbox/DS4/DS5), sensores de movimento, touchpad e precisão de teclado/mouse.
    - **Rede:** Gerencie UPnP, criptografia, endereços de vinculação e configurações de portas.
- **Opções Avançadas:** Porcentagem de FEC, parâmetros de QP, threads de CPU e suporte a HEVC/AV1.
- **Info do Sistema:** Monitor de hardware integrado exibindo Distro, CPU, GPU e Memória.
- **Customização:** Cores de destaque dinâmicas, Modo Escuro/Claro e suporte para Inglês e Português.

### 🚀 Como Começar

#### Pré-requisitos
- **Sunshine** instalado e em execução.
- **Python 3.10+**
- Bibliotecas **GTK4** e **Libadwaita**.

#### Instalação
1. Clone o repositório:
   ```bash
   git clone https://github.com/farosh/parshine.git
   cd parshine
   ```
2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
3. Execute o aplicativo:
   ```bash
   python main.py
   ```

### 🛠️ Tecnologias
- **Linguagem:** Python
- **Framework de UI:** GTK4 / Libadwaita (PyGObject)
- **Comunicação Backend:** Requests (Sunshine API)

---

## 📜 License / Licença
Distributed under the **GPL v3.0 License**. See `LICENSE` for more information.

*Created with ❤️ by Farosh Ryujinden*
