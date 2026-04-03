import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gdk, Gio, GLib

import os
import json
import subprocess
import platform
import threading
import time
import sys
from backend_api import SunshineBackend
import colorsys
import locale

CONFIG_DIR = os.path.expanduser("~/.config/projeto_p")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

def resource_path(relative_path):
    """ Busca o caminho correto para recursos (funciona no PyInstaller, AppImage e no Dev) """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    # Em AppImage ou Dev, o caminho base deve ser onde o main.py está fisicamente
    base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

class ParShineSplash(Gtk.Window):
    def __init__(self, app):
        super().__init__(application=app, decorated=False, resizable=False)
        self.set_default_size(420, 420)
        self.add_css_class("splash-window")
        
        # Overlay para permitir camadas se quisermos adicionar algo mais futuramente
        overlay = Gtk.Overlay()
        
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, valign=Gtk.Align.CENTER, halign=Gtk.Align.CENTER)
        self.box.add_css_class("splash-box")
        
        logo_path = resource_path("logo.png")
        if os.path.exists(logo_path):
            img = Gtk.Picture.new_for_filename(logo_path)
            img.set_size_request(280, 280)
            img.add_css_class("splash-logo")
            self.box.append(img)
        
        self.spinner = Gtk.Spinner(spinning=True, halign=Gtk.Align.CENTER)
        self.spinner.add_css_class("splash-spinner")
        self.spinner.set_size_request(60, 60)
        self.box.append(self.spinner)
        
        # Label para Erros e Contagem (Invisível por padrão)
        self.error_label = Gtk.Label(halign=Gtk.Align.CENTER)
        self.error_label.add_css_class("splash-error-text")
        self.error_label.set_margin_top(10)
        self.error_label.set_visible(False)
        self.box.append(self.error_label)
        
        overlay.set_child(self.box)
        self.set_child(overlay)

    def show_error(self, message):
        self.spinner.set_visible(False)
        self.error_label.set_label(message)
        self.error_label.set_visible(True)
        self.add_css_class("splash-error")

class ProjetoPApp(Adw.Application):
    def __init__(self, **kwargs):
        app_id = "io.github.farosh.parshine"
        super().__init__(application_id=app_id, **kwargs)
        self.connect('activate', self.on_activate)
        
        self.backend = SunshineBackend()
        # O backend.auto_setup() será chamado na thread _start_services
        
        # Provedor CSS persistente para cores de destaque (evita recriar a cada ciclo RGB)
        self.accent_provider = Gtk.CssProvider()
        
        # Scout Intelligence: Autodetecção de Idioma do Sistema
        try:
            # MÉTODO MODERNO: Substitui o depreciado locale.getdefaultlocale()
            import locale
            os_lang, _ = locale.getlocale(locale.LC_MESSAGES)
            if not os_lang:
                os_lang = os.environ.get('LANG', 'en')
            default_lang = "pt" if os_lang and os_lang.startswith("pt") else "en"
        except:
            default_lang = "en"

        # Estado Inicial
        self.config = {"theme_mode": 1, "accent_color": "#9b30ff", "lang": default_lang, "rgb_speed": 0.005, "known_devices": []} # 0: Light, 1: Dark, 2: Gamer
        self.load_local_config()
        self.hue = 0.0
        self.first_update_done = False
        self.last_client_info = None # Memoriza o identificador persistente
        self.was_streaming = False   # Estado anterior para notificações
        self.last_notified_client = "" 
        self.last_display_list = []  # Cache para o Anti-Flicker System
        self.last_known_conf = {}    # Memória para persistência visual durante reinícios
        
        self.presets = {
            "min_log_level": [("Verbose", "0"), ("Debug", "1"), ("Info", "2"), ("Warning", "3"), ("Error", "4"), ("Fatal", "5")],
            "encoder": [("Auto", "recommended"), ("NVIDIA NVENC", "nvenc"), ("AMD VA-API", "vaapi"), ("Software", "software")],
            "nvenc_preset": [("P1 (mais rápido)", "0"), ("P2", "1"), ("P3", "2"), ("P4 (padrão)", "3"), ("P5", "4"), ("P6", "5"), ("P7 (lento)", "6")],
            "nvenc_multipass": [("Desativado", "0"), ("Passagem única", "1"), ("Duas passagens", "2")],
            "gamepad_kind": [("Automático", "auto"), ("Xbox 360", "x360"), ("DualShock 4", "ds4"), ("Xbox One", "xone")],
            "sw_preset": [("superfast (padrão)", "superfast"), ("ultrafast", "ultrafast"), ("veryfast", "veryfast"), ("faster", "faster"), ("fast", "fast"), ("medium", "medium"), ("slow", "slow"), ("slower", "slower"), ("veryslow", "veryslow"), ("placebo", "placebo")],
            "sw_tune": [("zerolatency (padrão)", "zerolatency"), ("animation", "animation"), ("film", "film"), ("grain", "grain"), ("psnr", "psnr"), ("ssim", "ssim")],
            "hevc_mode": [("Automático (recomendado)", "1"), ("Ativado", "2"), ("Desativado", "0")],
            "av1_mode": [("Automático (recomendado)", "1"), ("Ativado", "2"), ("Desativado", "0")],
            "capture_method": [("Autodetecção (recomendado)", "recommended"), ("X11", "x11"), ("KMS", "kms"), ("NVFBC", "nvfbc")],
            "resolutions": [("1080p (1920x1080)", "1920x1080"), ("720p (1280x720)", "1280x720"), ("4K (3840x2160)", "3840x2160")],
            "fps": [("60 FPS", "60"), ("30 FPS", "30"), ("144 FPS", "144"), ("120 FPS", "120")],
            "max_bitrate": [("20 Mbps", "20000"), ("10 Mbps", "10000"), ("50 Mbps", "50000"), ("100 Mbps", "100000")],
            "locale": [("Português (Brasil)", "pt_BR"), ("English (US)", "en_US")],
            "address_family": [("IPv4", "4"), ("IPv6", "6"), ("Ambos (IPv4/v6)", "0")],
            "web_ui_allowed_origin": [("Somente LAN", "1"), ("Qualquer Origem", "0")],
            "lan_encryption": [("Desativado (padrão)", "0"), ("Ativado", "1")],
            "wan_encryption": [("Ativado (padrão)", "1"), ("Desativado", "0")]
        }
        
        self.monitors = [("Monitor Principal (Index 0)", "0")]
        self.widgets = {}
        
        self.strings = {
            "pt": {
                "monitor": "Monitor", "pin": "Parear PIN", "settings": "Opções", "pc_info": "Status PC", "about": "Sobre",
                "dash_title": "Aparelhos Conectados", "no_dev": "Nenhum aparelho", "scanning": "Buscando...",
                "dash_sub": "O Sunshine não detectou nenhum aparelho pareado no momento.", "save_btn": "Salvar e Reiniciar",
                "lang_label": "Português (🇧🇷)", "dark": "Modo Escuro", "light": "Modo Claro",
                "host_name": "Nome Host", "lang": "Idioma", "log": "Log", "video": "Vídeo", "net": "Rede",
                "res": "Resolução", "bit": "Bitrate", "sys_id": "Identidade do Sistema", 
                "distro": "Distro", "proc": "Processador", "gpu": "Gráficos", "mem": "Memória",
                "subtitle": "Sunshine Host Manager", "general": "Geral", "streaming": "TRANSMITINDO", "pair_btn": "PAREAR",
                "pair_title": "Parear Moonlight", "nv_enc": "Codificador NVIDIA", "sw_enc": "Codificador de Software",
                "va_enc": "Codificador VA-API (AMD)", "nv_pre": "Predefinição de desempenho", "nv_multi": "Modo de duas passagens",
                "nv_aq": "AQ Espacial", "nv_buff": "Aumento percentual de VBV/HRD", "nv_coder": "Prefira CAVLC ao CABAC em H.264",
                "sw_pre": "Predefinições de SW", "sw_tune": "SW Tune", "va_strict": "Impor estritamente limites de bitrate",
                "adv": "Avançado", "fec": "Porcentagem de FEC", "qp": "Parâmetro de quantização", "threads": "Threads da CPU",
                "hevc": "Suporte a HEVC", "av1": "Suporte a AV1", "cap": "Método de captura", "f_enc": "Forçar codificador",
                "sink": "Dissipador de áudio", "audio": "Transmitir Áudio", "adapter": "Nome do adaptador (VA-API)",
                "disp_id": "ID de exibição", "min_fps": "Alvo Mínimo de FPS", "fam": "Endereço da família",
                "bind": "Vincular endereço", "port": "Porto", "external": "IP externo", "timeout": "Tempo limite de ping",
                "web_ui": "IU da Web permitida", "enc_lan": "Criptografia LAN", "enc_wan": "Criptografia WAN",
                "sunshine_name_tip": "Nome do host na rede. Ex: MeuPC-Gamer", "resolutions_tip": "Resoluções suportadas. Ex: 1920x1080, 1280x720",
                "max_bitrate_tip": "Bitrate máximo em Kbps. Ex: 20000 para 20Mbps", "fps_tip": "FPS do stream. Ex: 60",
                "audio_sink_tip": "Dispositivo de som. Ex: alsa_output.pci...analog-stereo", "vaapi_device_tip": "Caminho do dispositivo VA-API. Ex: /dev/dri/renderD128",
                "disp_id_tip": "ID do monitor (entre parênteses no log). Ex: 2", "min_fps_tip": "FPS mínimo para manter o stream estável. Ex: 30",
                "bind_address_tip": "IP local para vincular o serviço. Ex: 192.168.1.5", "port_tip": "Porta base UDP. Padrão: 47989",
                "external_ip_tip": "IP público se estiver atrás de NAT. Ex: 187.x.x.x", "timeout_tip": "Tempo máximo de resposta em ms. Padrão: 10000",
                "fec_percentage_tip": "Correção de erro em rede instável. Padrão: 20", "qp_tip": "Qualidade constante (HEVC/AV1). Ex: 28",
                "min_threads_tip": "Número mínimo de núcleos de CPU para encoding. Ex: 2", "nvenc_vbr_padding_percent_tip": "Preenchimento de bitrate VBR (%). Padrão: 0",
                "locale_tip": "Idioma da interface do Sunshine.", "min_log_level_tip": "Nível de detalhe dos logs do sistema.",
                "output_name_tip": "Nome do monitor de saída para captura.", "audio_tip": "Habilitar ou desabilitar a transmissão de som.",
                "upnp_tip": "Abrir portas automaticamente no roteador.", "address_family_tip": "Protocolo de rede (IPv4 ou IPv6).",
                "web_ui_tip": "Quem pode acessar as configurações via rede.", "enc_lan_tip": "Criptografia na rede local.",
                "enc_wan_tip": "Criptografia via Internet.", "hevc_mode_tip": "Usa o codec H.265 para ganhar qualidade com menos internet.",
                "av1_mode_tip": "Usa o codec AV1 (mais moderno e eficiente).", "cap_tip": "Tecnologia usada para tirar o print da tela no Linux.",
                "f_enc_tip": "Forçar o uso de um hardware específico para codificar.", "nvenc_preset_tip": "P1 (rápido) até P7 (máxima qualidade).",
                "nvenc_multipass_tip": "Melhora a precisão do bitrate em duas passagens.", "nvenc_aq_tip": "Ajuste de qualidade baseado no conteúdo da cena.",
                "nvenc_coder_tip": "Define o algoritmo de codificação de entropia.", "sw_preset_tip": "Velocidade do encoder via processador (superfast até placebo).",
                "sw_tune_tip": "Ajustes finos para latência zero ou animação.", "vaapi_strict_tip": "Força limites rígidos de bitrate em GPUs AMD/Intel.",
                "input": "Controles", "gamepad": "Ativar Gamepad", "gamepad_kind": "Emulação de Gamepad",
                "ds4_motion": "DS4: Sensores de Movimento", "ds4_touchpad": "DS4: Touchpad",
                "random_mac": "Randomizar MAC (PS5)", "guide_timeout": "Limite Tempo Botão Início",
                "keyboard": "Ativar Teclado", "alt_win": "Mapear Alt Dir p/ Windows",
                "mouse": "Ativar Mouse", "hires_scroll": "Rolagem Alta Resolução", "native_touch": "Suporte Caneta/Toque",
                "gamer": "Modo Gamer", "rgb_speed": "Velocidade RGB",
                "input_tip": "Configure controles, mouse e teclado.", "gamepad_tip": "Permitir controladores de jogo.",
                "gamepad_kind_tip": "Tipo de controle emulado no host Sunshine.", "ds4_motion_tip": "Ativa sensores de movimento para clientes DS4.",
                "ds4_touchpad_tip": "Habilita o touchpad para clientes DS4.", "random_mac_tip": "Usa MAC aleatório para controles virtuais.",
                "guide_timeout_tip": "Tempo p/ Select atuar como botão Home (ms).", "keyboard_tip": "Permitir entrada via teclado.",
                "alt_win_tip": "Mapeia Alt Gr para a tecla Super/Windows.", "mouse_tip": "Permitir entrada via mouse.",
                "hires_scroll_tip": "Melhora a precisão do scroll em mouses compatíveis.", "native_touch_tip": "Suporte a canetas e toques nativos.",
                "device_icon_tip": "Clique para trocar o tipo de dispositivo", "offline": "DESCONECTADO"
            },
            "en": {
                "monitor": "Monitor", "pin": "Pair PIN", "settings": "Settings", "pc_info": "PC Status", "about": "About",
                "dash_title": "Connected Devices", "no_dev": "No devices", "scanning": "Scanning...",
                "dash_sub": "Sunshine is not reporting any paired device.", "save_btn": "Save and Restart",
                "lang_label": "English (🇺🇸)", "dark": "Dark Mode", "light": "Light Mode",
                "host_name": "Host Name", "lang": "Language", "log": "Log", "video": "Video", "net": "Network",
                "res": "Resolution", "bit": "Bitrate", "sys_id": "System Identity",
                "distro": "Distro", "proc": "Processor", "gpu": "Graphics", "mem": "Memory",
                "subtitle": "Sunshine Host Manager", "general": "General", "streaming": "STREAMING", "pair_btn": "PAIR",
                "pair_title": "Pair Moonlight", "nv_enc": "NVIDIA Encoder", "sw_enc": "Software Encoder",
                "va_enc": "VA-API Encoder (AMD)", "nv_pre": "Performance Preset", "nv_multi": "Two-pass mode",
                "nv_aq": "Spatial AQ", "nv_buff": "VBV/HRD Padding (%)", "nv_coder": "Prefer CAVLC over CABAC (H.264)",
                "sw_pre": "SW Presets", "sw_tune": "SW Tune", "va_strict": "Enforce strict bitrate limits",
                "adv": "Advanced", "fec": "FEC Percentage", "qp": "Quantization Parameter", "threads": "CPU Threads",
                "hevc": "HEVC Support", "av1": "AV1 Support", "cap": "Capture Method", "f_enc": "Force Encoder",
                "sink": "Audio Sink", "audio": "Transmit Audio", "adapter": "Adapter Name (VA-API)",
                "disp_id": "Display ID", "min_fps": "Minimum FPS Target", "fam": "Address Family",
                "bind": "Bind Address", "port": "Port", "external": "External IP", "timeout": "Ping Timeout",
                "web_ui": "Allowed Web UI Origin", "enc_lan": "LAN Encryption", "enc_wan": "WAN Encryption",
                "sunshine_name_tip": "Host name on the network. Ex: Gaming-PC", "resolutions_tip": "Supported resolutions. Ex: 1920x1080",
                "max_bitrate_tip": "Maximum bitrate in Kbps. Ex: 20000 for 20Mbps", "fps_tip": "Stream FPS. Ex: 60",
                "audio_sink_tip": "Audio sink device. Ex: alsa_output.pci...analog-stereo", "vaapi_device_tip": "VA-API device path. Ex: /dev/dri/renderD128",
                "disp_id_tip": "Monitor ID (from logs). Ex: 2", "min_fps_tip": "Minimum FPS for stream stability. Ex: 30",
                "bind_address_tip": "Local IP to bind the service. Ex: 192.168.1.5", "port_tip": "Base UDP port. Default: 47989",
                "external_ip_tip": "Public IP if behind NAT. Ex: 187.x.x.x", "timeout_tip": "Max response time in ms. Default: 10000",
                "fec_percentage_tip": "FEC percentage for unstable networks. Default: 20", "qp_tip": "Constant Quality (HEVC/AV1). Ex: 28",
                "min_threads_tip": "Minimum CPU threads for encoding. Ex: 2", "nvenc_vbr_padding_percent_tip": "VBR bitrate padding (%). Default: 0",
                "locale_tip": "Sunshine interface language.", "min_log_level_tip": "System log detail level.",
                "output_name_tip": "Capture output monitor name.", "audio_tip": "Enable or disable sound transmission.",
                "upnp_tip": "Automatically open router ports.", "address_family_tip": "Network protocol (IPv4 or IPv6).",
                "web_ui_tip": "Who can access settings via network.", "enc_lan_tip": "Encryption on local network.",
                "enc_wan_tip": "Encryption over Internet.", "hevc_mode_tip": "Use H.265 codec for better quality at lower bitrates.",
                "av1_mode_tip": "Use AV1 codec (most modern and efficient).", "cap_tip": "Technology used for screen capture on Linux.",
                "f_enc_tip": "Force the use of a specific encoding hardware.", "nvenc_preset_tip": "P1 (fast) to P7 (max quality).",
                "nvenc_multipass_tip": "Improves bitrate accuracy in two passes.", "nvenc_aq_tip": "Quality adjustment based on scene content.",
                "nvenc_coder_tip": "Defines the entropy coding algorithm.", "sw_preset_tip": "Software encoding speed (superfast to placebo).",
                "sw_tune_tip": "Fine tuning for zero latency or animation.", "vaapi_strict_tip": "Enforce strict bitrate limits on AMD/Intel GPUs.",
                "input": "Input", "gamepad": "Enable Gamepad", "gamepad_kind": "Gamepad Type",
                "ds4_motion": "DS4: Motion Sensors", "ds4_touchpad": "DS4: Touchpad",
                "random_mac": "Randomize MAC (PS5)", "guide_timeout": "Guide Button Timeout",
                "keyboard": "Enable Keyboard", "alt_win": "Map Right Alt to Windows",
                "mouse": "Enable Mouse", "hires_scroll": "High Resolution Scroll", "native_touch": "Native Touch/Pen Support",
                "gamer": "Gamer Mode", "rgb_speed": "RGB Speed",
                "input_tip": "Configure gamepad, mouse and keyboard.", "gamepad_tip": "Allow client game controllers.",
                "gamepad_kind_tip": "The type of gamepad emulated on the host.", "ds4_motion_tip": "Enable motion sensors for DS4 clients.",
                "ds4_touchpad_tip": "Enable touchpad support for DS4 clients.", "random_mac_tip": "Randomize MAC for virtual controllers.",
                "guide_timeout_tip": "Delay for Select to act as Guide/Home button (ms).", "keyboard_tip": "Allow keyboard input from client.",
                "alt_win_tip": "Remap Right Alt key to Windows key.", "mouse_tip": "Allow mouse input from client.",
                "hires_scroll_tip": "Improved scroll precision on compatible hardware.", "native_touch_tip": "Native pen and touch support.",
                "device_icon_tip": "Click to change device icon", "offline": "OFFLINE"
            }
        }
        
        if "lang" not in self.config: self.config["lang"] = "pt"
        
        # Serviços em Segundo Plano
        threading.Thread(target=self._start_services, daemon=True).start()

    def _start_services(self):
        try:
            # Novo método unificado do backend (checa instalação, setup e execução)
            self.backend.auto_setup()
        except Exception as e:
            print(f"DEBUG: Falha na inicialização automática dos serviços: {e}")

    def load_local_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    self.config.update(json.load(f))
            except: pass

    def on_activate(self, app):
        self._load_css()
        
        # 1. Mostra a Splash Screen imediatamente
        self.splash = ParShineSplash(app)
        self.splash.present()
        
        # 2. VALIDAÇÃO DE INSTALAÇÃO
        if not self.backend.is_installed():
            self.countdown = 5
            self._handle_missing_sunshine()
            return

        # 3. Defer a criação da janela principal para manter a splash fluída
        GLib.timeout_add(100, self._init_main_ui, app)

    def _handle_missing_sunshine(self):
        if self.countdown > 0:
            msg = f"Sunshine não instalado!\nRedirecionando em {self.countdown}s..."
            self.splash.show_error(msg)
            self.countdown -= 1
            GLib.timeout_add_seconds(1, self._handle_missing_sunshine)
        else:
            # Abre o GitHub e fecha a aplicação
            url = "https://github.com/LizardByte/Sunshine"
            print(f"DEBUG: Sunshine não instalado. Abrindo {url}")
            subprocess.Popen(["xdg-open", url])
            self.quit()

    def _init_main_ui(self, app):
        self.win = Adw.ApplicationWindow(application=app)
        self.win.set_title("ParShine")
        self.win.set_icon_name("io.github.farosh.parshine")
        self.win.set_default_size(1050, 800)
        
        # Scout Discovery System V7 (God Mode Clean)
        display = Gdk.Display.get_default()
        monitors_model = display.get_monitors()
        self.monitors = [] # Lista limpa
        
        total_mons = monitors_model.get_n_items()
        is_wayland = "WAYLAND_DISPLAY" in os.environ
        
        for i in range(total_mons):
            m = monitors_model.get_item(i)
            model = m.get_model() or "Display"
            manufacturer = m.get_manufacturer() or ""
            name = f"🖥️ {manufacturer} {model}".strip()
            
            # Reversão automática para Wayland (O segredo do sucesso)
            target_id = str((total_mons - 1) - i) if is_wayland else str(i)
            self.monitors.append((name, target_id))

        # Smart Memory Selection

        # Smart Memory Selection
        last_monitor = self.config.get("last_monitor_name", "")
        self.selected_monitor_idx = 0 
        if last_monitor:
            for idx, (label, val) in enumerate(self.monitors):
                if last_monitor in label:
                    self.selected_monitor_idx = idx
                    break
        # Tema e Cores
        style_mgr = Adw.StyleManager.get_default()
        mode = self.config.get("theme_mode", 1)
        style_mgr.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT if mode == 0 else Adw.ColorScheme.FORCE_DARK)
        
        # --- SISTEMA DE TRADUÇÃO ---
        if "lang" not in self.config: self.config["lang"] = "pt"

        def tr(key): return self.strings[self.config["lang"]].get(key, key)
        self.tr = tr

        # Layout Principal
        self.split_view = Adw.NavigationSplitView()
        
        # --- SIDEBAR ---
        sidebar_page = Adw.NavigationPage(title="Menu")
        sb_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sb_box.add_css_class("sidebar-box")
        top_spacer = Gtk.Box(); top_spacer.set_size_request(-1, 20); sb_box.append(top_spacer)
        
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        
        self.sidebar_btns = []
        
        # Ícones da Sidebar com Emojis (Dashboard, PIN, Input, Settings, Status, Info)
        first_btn = None
        for i, emoji in enumerate(["🌎", "🔑", "🎮", "⚙️", "🐧", "🐉"]):
            b = Gtk.ToggleButton(); b.add_css_class("sidebar-btn")
            lbl = Gtk.Label(label=emoji); lbl.add_css_class("sidebar-emoji")
            b.set_child(lbl)
            for m in ['start', 'end']: getattr(b, f"set_margin_{m}")(12); b.set_margin_bottom(12)
            self.sidebar_btns.append(b)
            if first_btn: b.set_group(first_btn)
            else: first_btn = b; b.set_active(True)
            b.connect("toggled", self.on_nav_toggled)
            sb_box.append(b)

        sb_box.append(Gtk.Box(vexpand=True))

        # Botão Idioma
        self.l_btn = Gtk.Button(); self.l_btn.add_css_class("sidebar-btn"); self.l_btn.set_hexpand(True)
        self.l_btn.set_margin_bottom(10)
        for m in ['start', 'end']: getattr(self.l_btn, f"set_margin_{m}")(12)
        l_box = Gtk.Box(spacing=10, halign=Gtk.Align.CENTER)
        self.l_img = Gtk.Image.new_from_icon_name("preferences-desktop-locale-symbolic"); self.l_img.set_pixel_size(20)
        self.l_lbl = Gtk.Label(); l_box.append(self.l_img); l_box.append(self.l_lbl)
        self.l_btn.set_child(l_box); self.l_btn.connect("clicked", self.toggle_lang); sb_box.append(self.l_btn)

        # Botão Dark Mode
        self.t_btn = Gtk.Button(); self.t_btn.add_css_class("sidebar-btn"); self.t_btn.set_hexpand(True); self.t_btn.set_margin_bottom(10)
        for m in ['start', 'end']: getattr(self.t_btn, f"set_margin_{m}")(12)
        self.t_box = Gtk.Box(spacing=10, halign=Gtk.Align.CENTER)
        self.t_img = Gtk.Image(); self.t_img.set_pixel_size(20); self.t_lbl = Gtk.Label()
        self.t_box.append(self.t_img); self.t_box.append(self.t_lbl); self.t_btn.set_child(self.t_box)
        self.t_btn.connect("clicked", self.toggle_theme); sb_box.append(self.t_btn)
        
        # Color Bar
        self.c_btn = Gtk.ColorButton()
        self.c_btn.add_css_class("sidebar-btn")
        self.c_btn.add_css_class("color-bar")
        self.c_btn.set_hexpand(True)
        for m in ['start', 'end']: getattr(self.c_btn, f"set_margin_{m}")(12)
        self.c_btn.set_margin_bottom(20)
        rgba = Gdk.RGBA()
        rgba.parse(self.config.get("accent_color", "#9b30ff"))
        self.c_btn.set_property("rgba", rgba)
        self.c_btn.connect("color-set", self.on_color_set)
        sb_box.append(self.c_btn)
        
        self.apply_accent_color(self.config.get("accent_color"))
        self._update_theme_icon()
        
        sidebar_page.set_child(sb_box)
        self.split_view.set_sidebar(sidebar_page)
        
        # Aba Dispositivos (Grid)
        self.m_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        for m in ['top', 'bottom', 'start', 'end']: getattr(self.m_box, f"set_margin_{m}")(40)
        dash_sc = Gtk.ScrolledWindow(); dash_sc.set_child(self.m_box); self.stack.add_named(dash_sc, "devices")
        # O build_dash() será chamado automaticamente pelo on_nav_toggled do primeiro botão
        self._update_lang_ui()
        # --- VIEWS ---
        
        
        # O PIN agora é dinâmico via p_box
        
        # Aba Configurações (Settings)
        sett_main = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        # Header Fixo
        self.s_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        self.s_header.add_css_class("action-header")
        self.s_save_btn = Gtk.Button(label="Salvar e Reiniciar") # Será traduzido no refresh
        self.s_save_btn.add_css_class("accent-button"); self.s_save_btn.set_hexpand(True)
        self.s_save_btn.set_margin_top(20); self.s_save_btn.set_margin_bottom(10)
        self.s_save_btn.set_margin_start(40); self.s_save_btn.set_margin_end(40)
        self.s_save_btn.connect("clicked", self.on_save_clicked)
        self.s_header.append(self.s_save_btn)
        sett_main.append(self.s_header)
        
        self.s_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        for m in ['top', 'bottom', 'start', 'end']: getattr(self.s_box, f"set_margin_{m}")(40)
        sett_sc = Gtk.ScrolledWindow(); sett_sc.set_child(self.s_box); sett_sc.set_vexpand(True)
        sett_main.append(sett_sc)
        self.stack.add_named(sett_main, "settings")
        
        # Aba Input (Controles)
        input_main = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        # Header Fixo
        self.v_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        self.v_header.add_css_class("action-header")
        self.v_save_btn = Gtk.Button(label="Salvar e Reiniciar")
        self.v_save_btn.add_css_class("accent-button"); self.v_save_btn.set_hexpand(True)
        self.v_save_btn.set_margin_top(20); self.v_save_btn.set_margin_bottom(10)
        self.v_save_btn.set_margin_start(40); self.v_save_btn.set_margin_end(40)
        self.v_save_btn.connect("clicked", self.on_save_clicked)
        self.v_header.append(self.v_save_btn)
        input_main.append(self.v_header)

        self.v_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        for m in ['top', 'bottom', 'start', 'end']: getattr(self.v_box, f"set_margin_{m}")(40)
        input_sc = Gtk.ScrolledWindow(); input_sc.set_child(self.v_box); input_sc.set_vexpand(True)
        input_main.append(input_sc)
        self.stack.add_named(input_main, "input")
        
        # PIN
        self.p_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=30)
        self.p_box.set_valign(Gtk.Align.CENTER); self.p_box.set_halign(Gtk.Align.CENTER)
        p_sc = Gtk.ScrolledWindow(); p_sc.set_child(self.p_box); self.stack.add_named(p_sc, "pin")
        
        # Info do Sistema
        self.i_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        for m in ['top', 'bottom', 'start', 'end']: getattr(self.i_box, f"set_margin_{m}")(45)
        info_sc = Gtk.ScrolledWindow(); info_sc.set_child(self.i_box); self.stack.add_named(info_sc, "pc_info")
        
        # Sobre
        self.a_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        for m in ['top', 'bottom', 'start', 'end']: getattr(self.a_box, f"set_margin_{m}")(45)
        about_sc = Gtk.ScrolledWindow(); about_sc.set_child(self.a_box); self.stack.add_named(about_sc, "about")
        
        # --- CONTENT PAGE CONTEXT ---
        content_page = Adw.NavigationPage(title="Monitor")
        
        # ToolbarView (HeaderBar + Content)
        toolbar_view = Adw.ToolbarView()
        
        header_bar = Adw.HeaderBar()
        # Title Widget with Subtitle
        title_widget = Adw.WindowTitle(title="ParShine", subtitle="Sunshine Host Manager")
        self.title_widget = Adw.WindowTitle(title="ParShine", subtitle="Sunshine Host Manager")
        header_bar.set_title_widget(self.title_widget)
        
        toolbar_view.add_top_bar(header_bar)
        toolbar_view.set_content(self.stack)
        
        content_page.set_child(toolbar_view)
        
        self.split_view.set_content(content_page)
        
        # Condição de Colapso (Responsivo)
        self.win.set_content(self.split_view)
        
        self._update_lang_ui()
        self.build_dash()
        
        # 3. Inicia o monitoramento e o ciclo RGB (Apenas uma vez)
        GLib.timeout_add(50, self._rgb_cycle_timer)
        GLib.timeout_add_seconds(1, self.refresh_loop)
        
        # 4. Aguarda um pouco mais na splash para garantir que o backend subiu
        GLib.timeout_add(2200, self._finish_splash)
        
        return False # Para o timeout_add inicial

    def _finish_splash(self):
        # Efeito de Fade Out
        if hasattr(self, 'splash'):
            self.splash.box.add_css_class("splash-fade-out")
            GLib.timeout_add(800, self._reveal_main)
        return False

    def _reveal_main(self):
        if hasattr(self, 'splash'):
            self.splash.destroy()
        self.win.present()
        return False

    def on_nav_toggled(self, b):
        if not b.get_active(): return
        index = self.sidebar_btns.index(b)
        self.widgets = {} 
        self.first_update_done = False 
        self.last_display_list = [] # Limpa o cache para forçar o redesenho ao trocar de aba
        
        # Limpa todos os boxes dinâmicos
        for box in [self.i_box, self.m_box, self.p_box, self.v_box, self.s_box, self.a_box]:
            while (c := box.get_first_child()): box.remove(c)
        
        pages = ["devices", "pin", "input", "settings", "pc_info", "about"]
        self.stack.set_visible_child_name(pages[index])
        
        # Usa o cache alimentado pelo background (Instantâneo e Seguro)
        conf = self.last_known_conf
            
        if index == 0: self.build_dash()
        elif index == 1: self.build_pin()
        elif index == 2: self.build_input(conf)
        elif index == 3: self.build_settings(conf)
        elif index == 4: self.build_status()
        elif index == 5: self.build_about()

    def toggle_lang(self, b):
        self.config["lang"] = "en" if self.config["lang"] == "pt" else "pt"
        self._update_lang_ui()
        self.last_display_list = [] # Redesenho imediato do dashboard
        
        # Limpa os containers antes de redesenhar
        while (child := self.s_box.get_first_child()): self.s_box.remove(child)
        while (child := self.i_box.get_first_child()): self.i_box.remove(child)

        # Redesenha imediatamente usando o cache reativo
        conf = self.last_known_conf
        self.build_settings(conf)
        self.title_widget.set_subtitle(self.tr("subtitle"))
        if hasattr(self, "pin_title"): self.pin_title.set_label(self.tr("pair_title"))
        if hasattr(self, "pair_btn"): self.pair_btn.set_label(self.tr("pair_btn"))
        
        self.s_save_btn.set_label(self.tr("save_btn"))
        self.v_save_btn.set_label(self.tr("save_btn"))
        # Reset para forçar preenchimento no próximo refresh
        self.first_update_done = False

    def _update_lang_ui(self):
        tr = self.tr
        self.l_lbl.set_label(tr("lang_label"))
        self._update_theme_icon()
        if hasattr(self, "dash_label"):
            self.dash_label.set_label(f"{tr('dash_title')}: 0") # Reset visual base

    def _add_decoration(self, box):
        logo_file = resource_path("logo.png")
        if os.path.exists(logo_file):
            img = Gtk.Image.new_from_file(logo_file)
            img.set_pixel_size(128); img.set_margin_bottom(20); img.set_halign(Gtk.Align.CENTER)
            box.append(img)
        else:
            # Placeholder se não houver logo
            spacer = Gtk.Box(); spacer.set_size_request(-1, 20); box.append(spacer)

    def build_status(self):
        while (c := self.i_box.get_first_child()): self.i_box.remove(c)
        self._add_decoration(self.i_box)
        tr = self.tr
        
        # Identidade do Sistema (Info Síncrona)
        l = Gtk.Label(label=tr("sys_id"), xalign=0); l.add_css_class("heading"); self.i_box.append(l)
        cl = Gtk.ListBox(); cl.add_css_class("card"); cl.set_selection_mode(0); cl.set_show_separators(True)
        
        distro = platform.freedesktop_os_release().get('PRETTY_NAME', 'Linux')
        cpu = subprocess.getoutput("grep 'model name' /proc/cpuinfo | head -1 | cut -d: -f2").strip() or "CPU"
        gpu = subprocess.getoutput("lspci | grep -i vga | cut -d: -f3-").split("[")[-1].split("]")[0] or "GPU"
        ram = subprocess.getoutput("grep MemTotal /proc/meminfo | awk '{print int($2/1024/1024+0.5) \" GB\"}'") or "8 GB"
        
        for k, v in [("distro", distro), ("proc", cpu), ("gpu", gpu), ("mem", ram), ("Kernel", platform.release())]:
            label_key = k.lower() if k.lower() in self.strings["pt"] else k
            r = Adw.ActionRow(title=tr(label_key)); r.add_suffix(Gtk.Label(label=str(v), selectable=True)); cl.append(r)
        
        self.i_box.append(cl)
    def build_dash(self):
        while (c := self.m_box.get_first_child()): self.m_box.remove(c)
        self._add_decoration(self.m_box)
        # Recria o label e flowbox que foram limpos
        self.dash_label = Gtk.Label(xalign=0); self.dash_label.add_css_class("heading")
        self.m_box.append(self.dash_label)
        self.dev_flow = Gtk.FlowBox(valign=Gtk.Align.START, max_children_per_line=3, selection_mode=0)
        self.m_box.append(self.dev_flow)
        
    def build_pin(self):
        while (c := self.p_box.get_first_child()): self.p_box.remove(c)
        self._add_decoration(self.p_box)
        self.pin_title = Gtk.Label(label=self.tr("pair_title")); self.pin_title.add_css_class("main-title")
        self.p_box.append(self.pin_title)
        
        self.pin_entry = Gtk.Entry(); self.pin_entry.set_placeholder_text("0000"); self.pin_entry.set_max_length(4)
        self.pin_entry.set_width_chars(10); self.pin_entry.set_alignment(0.5); self.pin_entry.add_css_class("card")
        self.pin_entry.set_halign(Gtk.Align.CENTER); self.p_box.append(self.pin_entry)
        
        pair_btn = Gtk.Button(label=self.tr("pair_btn")); pair_btn.add_css_class("accent-button")
        pair_btn.set_size_request(240, 50); pair_btn.set_halign(Gtk.Align.CENTER)
        pair_btn.connect("clicked", self.on_pair_clicked); self.p_box.append(pair_btn)
        self.pair_btn = pair_btn

    def build_about(self):
        while (c := self.a_box.get_first_child()): self.a_box.remove(c)
        logo_file = resource_path("logo.png")
        
        # Centralizador
        self.a_box.set_valign(Gtk.Align.CENTER)
        
        if os.path.exists(logo_file):
            img = Gtk.Image.new_from_file(logo_file)
            img.set_pixel_size(160); img.set_margin_bottom(30); img.set_halign(Gtk.Align.CENTER)
            self.a_box.append(img)
            
            l1 = Gtk.Label(label="ParShine v1.0"); l1.add_css_class("main-title")
            l1.set_halign(Gtk.Align.CENTER); self.a_box.append(l1)
            
            l2 = Gtk.Label(label="Created by Farosh Ryujinden"); l2.set_opacity(0.8); l2.add_css_class("heading")
            l2.set_halign(Gtk.Align.CENTER); self.a_box.append(l2)
            
            # Box de Links
            link_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20, halign=Gtk.Align.CENTER)
            link_box.set_margin_top(20)
            
            # Github
            gh_btn = Gtk.LinkButton.new_with_label("https://github.com/FaroshRyujinden", "🐲 GitHub")
            gh_btn.add_css_class("flat"); link_box.append(gh_btn)
            
            # Website
            ws_btn = Gtk.LinkButton.new_with_label("https://faroshryujinden.atlasnetwork.com.br/", "⚡ Website")
            ws_btn.add_css_class("flat"); link_box.append(ws_btn)
            
            self.a_box.append(link_box)
        else:
            sp = Adw.StatusPage(icon_name="help-about-symbolic", title="ParShine v1.0", description="Created by Farosh Ryujinden")
            self.a_box.append(sp)

    def build_input(self, conf):
        tr = self.tr
        self._add_decoration(self.v_box)
        def set_tip(w, k):
            tip = tr(k + "_tip")
            if tip != k + "_tip": w.set_tooltip_text(tip)

        l = Gtk.Label(label=tr("input"), xalign=0); l.add_css_class("heading"); self.v_box.append(l)
        c = Gtk.ListBox(); c.add_css_class("card"); c.set_selection_mode(0); c.set_show_separators(True)
        
        # Helper pra setar valor inicial
        def set_val(k, w):
            v = conf.get(k, "false")
            if isinstance(w, Adw.SwitchRow): w.set_active(str(v).lower() in ["1", "true"])
            elif isinstance(w, Adw.EntryRow): w.set_text(str(v))

        # Gamepad
        sw_gp = Adw.SwitchRow(title=tr("gamepad")); self.widgets["gamepad"] = sw_gp; set_tip(sw_gp, "gamepad"); set_val("gamepad", sw_gp); c.append(sw_gp)
        
        for t, k, o in [(tr("gamepad_kind"), "gamepad_kind", self.presets["gamepad_kind"])]:
            r = Adw.ActionRow(title=t); sl = Gtk.StringList.new([opt[0] for opt in o]); dd = Gtk.DropDown(model=sl)
            dd.set_valign(Gtk.Align.CENTER)
            
            # Sincronização Síncrona
            val = conf.get(k)
            for idx, opt in enumerate(o):
                if str(val) == str(opt[1]): dd.set_selected(idx); break
                
            r.add_suffix(dd); self.widgets[k] = (dd, None, o); set_tip(r, k); c.append(r)
        
        sw_mot = Adw.SwitchRow(title=tr("ds4_motion")); self.widgets["motion_as_ds4"] = sw_mot; set_tip(sw_mot, "ds4_motion"); set_val("motion_as_ds4", sw_mot); c.append(sw_mot)
        sw_tp = Adw.SwitchRow(title=tr("ds4_touchpad")); self.widgets["touchpad_as_ds4"] = sw_tp; set_tip(sw_tp, "ds4_touchpad"); set_val("touchpad_as_ds4", sw_tp); c.append(sw_tp)
        sw_mac = Adw.SwitchRow(title=tr("random_mac")); self.widgets["ds5_inputtino_randomize_mac"] = sw_mac; set_tip(sw_mac, "random_mac"); set_val("ds5_inputtino_randomize_mac", sw_mac); c.append(sw_mac)
        
        r_tout = Adw.EntryRow(title=tr("guide_timeout")); self.widgets["back_button_timeout"] = r_tout; set_tip(r_tout, "guide_timeout"); set_val("back_button_timeout", r_tout); c.append(r_tout)
        
        # Teclado e Mouse
        sw_kb = Adw.SwitchRow(title=tr("keyboard")); self.widgets["keyboard"] = sw_kb; set_tip(sw_kb, "keyboard"); set_val("keyboard", sw_kb); c.append(sw_kb)
        sw_alt = Adw.SwitchRow(title=tr("alt_win")); self.widgets["key_rightalt_to_key_win"] = sw_alt; set_tip(sw_alt, "alt_win"); set_val("key_rightalt_to_key_win", sw_alt); c.append(sw_alt)
        sw_ms = Adw.SwitchRow(title=tr("mouse")); self.widgets["mouse"] = sw_ms; set_tip(sw_ms, "mouse"); set_val("mouse", sw_ms); c.append(sw_ms)
        sw_sc = Adw.SwitchRow(title=tr("hires_scroll")); self.widgets["hires_scrolling"] = sw_sc; set_tip(sw_sc, "hires_scroll"); set_val("hires_scrolling", sw_sc); c.append(sw_sc)
        sw_tch = Adw.SwitchRow(title=tr("native_touch")); self.widgets["native_touch"] = sw_tch; set_tip(sw_tch, "native_touch"); set_val("native_touch", sw_tch); c.append(sw_tch)
        
        self.v_box.append(c)

    def build_settings(self, conf):
        tr = self.tr
        while (c := self.s_box.get_first_child()): self.s_box.remove(c)
        self._add_decoration(self.s_box)
        def set_tip(w, k):
            tip = tr(k + "_tip")
            if tip != k + "_tip": w.set_tooltip_text(tip)

        # Grupo: Geral
        l = Gtk.Label(label=tr("general"), xalign=0); l.add_css_class("heading"); self.s_box.append(l)
        c = Gtk.ListBox(); c.add_css_class("card"); c.set_selection_mode(0); c.set_show_separators(True)
        r_h = Adw.EntryRow(title=tr("host_name")); self.widgets["sunshine_name"] = r_h; set_tip(r_h, "sunshine_name"); c.append(r_h)
        for t, k, o in [(tr("log"), "min_log_level", self.presets["min_log_level"])]:
            r = Adw.ActionRow(title=t); sl = Gtk.StringList.new([opt[0] for opt in o]); dd = Gtk.DropDown(model=sl)
            dd.set_valign(Gtk.Align.CENTER); r.add_suffix(dd); self.widgets[k] = (dd, None, o); set_tip(r, k); c.append(r)
        
        # Controle de Velocidade RGB (Apenas Visual)
        self.speed_row = Adw.ActionRow(title=tr("rgb_speed"))
        self.speed_btn = Gtk.Button(); self.speed_btn.set_valign(Gtk.Align.CENTER)
        self.speed_btn.add_css_class("flat"); self.speed_btn.connect("clicked", self.cycle_rgb_speed)
        self.speed_row.add_suffix(self.speed_btn)
        self._update_speed_label()
        c.append(self.speed_row)
        
        self.s_box.append(c)

        # Grupo: Vídeo e Áudio
        l = Gtk.Label(label=tr("video"), xalign=0); l.add_css_class("heading"); self.s_box.append(l)
        c = Gtk.ListBox(); c.add_css_class("card"); c.set_selection_mode(0); c.set_show_separators(True)
        
        conf = self.backend.get_config() or {}
        
        for t, k, o in [(tr("monitor"), "output_name", self.monitors), (tr("res"), "resolutions", self.presets["resolutions"]), (tr("bit"), "max_bitrate", self.presets["max_bitrate"]), (tr("fps"), "fps", self.presets["fps"])]:
            r = Adw.ActionRow(title=t); sl = Gtk.StringList.new([opt[0] for opt in o]); dd = Gtk.DropDown(model=sl)
            dd.set_valign(Gtk.Align.CENTER)
            
            # Sincronização Inteligente (Sempre escolhe o certo ao abrir)
            sel_idx = 0
            if k == "output_name":
                sel_idx = self.selected_monitor_idx
            
            # Se o valor na config do Sunshine bater com alguma opção, usa ela
            val = conf.get(k)
            for idx, opt in enumerate(o):
                if str(val) == str(opt[1]):
                    sel_idx = idx
                    break
            
            dd.set_selected(sel_idx)
            r.add_suffix(dd); self.widgets[k] = (dd, None, o); set_tip(r, k); c.append(r)
        
        sw_audio = Adw.SwitchRow(title=tr("audio")); self.widgets["audio"] = sw_audio; set_tip(sw_audio, "audio"); c.append(sw_audio)
        r_sink = Adw.EntryRow(title=tr("sink")); self.widgets["audio_sink"] = r_sink; set_tip(r_sink, "audio_sink"); c.append(r_sink)
        r_va = Adw.EntryRow(title=tr("adapter")); self.widgets["vaapi_device"] = r_va; set_tip(r_va, "vaapi_device"); c.append(r_va)
        r_disp = Adw.EntryRow(title=tr("disp_id")); self.widgets["display_id"] = r_disp; set_tip(r_disp, "display_id"); c.append(r_disp)
        r_minf = Adw.EntryRow(title=tr("min_fps")); self.widgets["min_fps"] = r_minf; set_tip(r_minf, "min_fps"); c.append(r_minf)
        self.s_box.append(c)
        
        # Grupo: Rede
        l = Gtk.Label(label=tr("net"), xalign=0); l.add_css_class("heading"); self.s_box.append(l)
        c = Gtk.ListBox(); c.add_css_class("card"); c.set_selection_mode(0); c.set_show_separators(True)
        sw_upnp = Adw.SwitchRow(title="UPnP"); self.widgets["upnp"] = sw_upnp; set_tip(sw_upnp, "upnp"); c.append(sw_upnp)
        for t, k, o in [(tr("fam"), "address_family", self.presets["address_family"]), (tr("web_ui"), "web_ui_allowed_origin", self.presets["web_ui_allowed_origin"]), (tr("enc_lan"), "lan_encryption", self.presets["lan_encryption"]), (tr("enc_wan"), "wan_encryption", self.presets["wan_encryption"])]:
            r = Adw.ActionRow(title=t); sl = Gtk.StringList.new([opt[0] for opt in o]); dd = Gtk.DropDown(model=sl)
            dd.set_valign(Gtk.Align.CENTER)
            
            val = conf.get(k)
            sel_idx = 0
            for idx, opt in enumerate(o):
                if str(val) == str(opt[1]):
                    sel_idx = idx
                    break
            dd.set_selected(sel_idx)
            r.add_suffix(dd); self.widgets[k] = (dd, None, o); set_tip(r, k); c.append(r)
        r_bind = Adw.EntryRow(title=tr("bind")); self.widgets["bind_address"] = r_bind; set_tip(r_bind, "bind_address"); c.append(r_bind)
        r_port = Adw.EntryRow(title=tr("port")); self.widgets["port"] = r_port; set_tip(r_port, "port"); c.append(r_port)
        r_ext = Adw.EntryRow(title=tr("external")); self.widgets["external_ip"] = r_ext; set_tip(r_ext, "external_ip"); c.append(r_ext)
        r_tout = Adw.EntryRow(title=tr("timeout")); self.widgets["ping_timeout"] = r_tout; set_tip(r_tout, "ping_timeout"); c.append(r_tout)
        self.s_box.append(c)
        
        # Grupo: Avançado
        l = Gtk.Label(label=tr("adv"), xalign=0); l.add_css_class("heading"); self.s_box.append(l)
        c = Gtk.ListBox(); c.add_css_class("card"); c.set_selection_mode(0); c.set_show_separators(True)
        for t, k, o in [(tr("hevc"), "hevc_mode", self.presets["hevc_mode"]), (tr("av1"), "av1_mode", self.presets["av1_mode"]), (tr("cap"), "capture_method", self.presets["capture_method"]), (tr("f_enc"), "encoder", self.presets["encoder"])]:
            r = Adw.ActionRow(title=t); sl = Gtk.StringList.new([opt[0] for opt in o]); dd = Gtk.DropDown(model=sl)
            dd.set_valign(Gtk.Align.CENTER)

            val = conf.get(k)
            sel_idx = 0
            for idx, opt in enumerate(o):
                if str(val) == str(opt[1]):
                    sel_idx = idx
                    break
            dd.set_selected(sel_idx)
            r.add_suffix(dd); self.widgets[k] = (dd, None, o); set_tip(r, k); c.append(r)
        r_fec = Adw.EntryRow(title=tr("fec")); self.widgets["fec_percentage"] = r_fec; set_tip(r_fec, "fec_percentage"); c.append(r_fec)
        r_qp = Adw.EntryRow(title=tr("qp")); self.widgets["qp"] = r_qp; set_tip(r_qp, "qp"); c.append(r_qp)
        r_thr = Adw.EntryRow(title=tr("threads")); self.widgets["min_threads"] = r_thr; set_tip(r_thr, "min_threads"); c.append(r_thr)
        self.s_box.append(c)
        
        # Grupo: NVIDIA NVENC
        l = Gtk.Label(label=tr("nv_enc"), xalign=0); l.add_css_class("heading"); self.s_box.append(l)
        c = Gtk.ListBox(); c.add_css_class("card"); c.set_selection_mode(0); c.set_show_separators(True)
        for t, k, o in [(tr("nv_pre"), "nvenc_preset", self.presets["nvenc_preset"]), (tr("nv_multi"), "nvenc_multipass", self.presets["nvenc_multipass"])]:
            r = Adw.ActionRow(title=t); sl = Gtk.StringList.new([opt[0] for opt in o]); dd = Gtk.DropDown(model=sl)
            dd.set_valign(Gtk.Align.CENTER); r.add_suffix(dd); self.widgets[k] = (dd, None, o); set_tip(r, k); c.append(r)
        sw_aq = Adw.SwitchRow(title=tr("nv_aq")); self.widgets["nvenc_aq"] = sw_aq; set_tip(sw_aq, "nvenc_aq"); c.append(sw_aq)
        r_buff = Adw.EntryRow(title=tr("nv_buff")); self.widgets["nvenc_vbr_padding_percent"] = r_buff; set_tip(r_buff, "nvenc_vbr_padding_percent"); c.append(r_buff)
        sw_coder = Adw.SwitchRow(title=tr("nv_coder")); self.widgets["nvenc_coder"] = sw_coder; set_tip(sw_coder, "nvenc_coder"); c.append(sw_coder)
        self.s_box.append(c)
        
        # Grupo: Software
        l = Gtk.Label(label=tr("sw_enc"), xalign=0); l.add_css_class("heading"); self.s_box.append(l)
        c = Gtk.ListBox(); c.add_css_class("card"); c.set_selection_mode(0); c.set_show_separators(True)
        for t, k, o in [(tr("sw_pre"), "sw_preset", self.presets["sw_preset"]), (tr("sw_tune"), "sw_tune", self.presets["sw_tune"])]:
            r = Adw.ActionRow(title=t); sl = Gtk.StringList.new([opt[0] for opt in o]); dd = Gtk.DropDown(model=sl)
            dd.set_valign(Gtk.Align.CENTER); r.add_suffix(dd); self.widgets[k] = (dd, None, o); set_tip(r, k); c.append(r)
        self.s_box.append(c)
        
        # Grupo: VA-API
        l = Gtk.Label(label=tr("va_enc"), xalign=0); l.add_css_class("heading"); self.s_box.append(l)
        c = Gtk.ListBox(); c.add_css_class("card"); c.set_selection_mode(0); c.set_show_separators(True)
        sw_va = Adw.SwitchRow(title=tr("va_strict")); self.widgets["vaapi_strict_rc_buffer"] = sw_va; set_tip(sw_va, "vaapi_strict"); c.append(sw_va)
        self.s_box.append(c)

    def refresh_loop(self):
        threading.Thread(target=self._async_refresh, daemon=True).start()
        return True

    def _async_refresh(self):
        d = self.backend.get_devices()
        c = self.backend.get_config() # PESCA ATIVA: Busca config a cada 1 segundo
        s = self.backend.is_streaming()
        cli = self.backend.get_streaming_client() if s else None
        active_uuid = self.backend.get_active_uuid() if s else None
        
        if s:
            if cli and cli['name'] not in ["Aparelho em Rede", "Aparelho Remoto"]:
                self.last_client_info = cli
        else: self.last_client_info = None

        if active_uuid and not getattr(self, 'last_logged_uuid', None) == active_uuid:
            print(f"DEBUG REFRESH: Nova Sessão Detectada! ID: {active_uuid}")
            self.last_logged_uuid = active_uuid
        elif not active_uuid:
            self.last_logged_uuid = None
        
        GLib.idle_add(self.update_ui, d, c, s, self.last_client_info or cli, active_uuid)

    def update_ui(self, devs, config_data, is_st, client_info, active_uuid):
        self.current_session_id = active_uuid # Armazena para o botão de expulsar
        # --- ATUALIZAÇÃO REATIVA DO CACHE (Safe Sync) ---
        if config_data and len(config_data) > 5:
            self.last_known_conf = config_data
            
            # --- AUTO-SYNC DE CAMPOS VAZIOS (v1.7) ---
            # Se você estiver na aba de opções/input e o campo estiver vazio, o parShine preenche de volta sozinho!
            if self.stack.get_visible_child_name() in ["settings", "input"]:
                for k, w in self.widgets.items():
                    val = config_data.get(k)
                    if val is not None and isinstance(w, Adw.EntryRow):
                        # Evita sobrescrever se o usuário estiver digitando (foco)
                        if not w.get_text(): 
                            w.set_text(str(val))
            
        # --- SISTEMA DE NOTIFICAÇÕES E MEMÓRIA ---
        if "known_devices" not in self.config: self.config["known_devices"] = []
        
        current_connected_name = client_info['name'] if (is_st and client_info) else None
        
        # 1. Se alguém conectou, atualiza a memória
        if current_connected_name:
            found = False
            for dev in self.config["known_devices"]:
                if dev['name'] == current_connected_name:
                    dev['last_seen'] = time.time()
                    found = True; break
            if not found:
                # Novo dispositivo descoberto!
                self.config["known_devices"].append({
                    "name": current_connected_name,
                    "type": client_info.get('type', 'remote'),
                    "last_seen": time.time()
                })
                self._save_config_to_disk()

        # 2. Notificações (Lógica já existente)
        if is_st and not self.was_streaming:
            self.send_system_notification("📡 Transmissão Iniciada", f"{current_connected_name} está conectado.")
            self.last_notified_client = current_connected_name
        elif not is_st and self.was_streaming:
            self.send_system_notification("🔌 Transmissão Encerrada", f"{self.last_notified_client} se desconectou.")
            self.last_notified_client = ""
        
        self.was_streaming = is_st

        tr = self.tr
        
        # --- CÁLCULO DA LISTA ATUAL ---
        display_list = []
        seen_names = set()

        # Primeiro: Dispositivos da memória (prioridade visual)
        for d in self.config.get("known_devices", []):
            name = d['name']
            is_active = (is_st and name == current_connected_name)
            display_list.append({
                "name": name,
                "type": d.get('type', 'remote'),
                "status": "online" if is_active else "offline"
            })
            seen_names.add(name)

        # Segundo: Dispositivos pareados que ainda não estão na memória
        if devs:
            for d in devs:
                name = d.get('name', 'Poco')
                if name not in seen_names:
                    display_list.append({"name": name, "type": "mobile", "status": "offline"})
                    seen_names.add(name)

        # --- ANTI-FLICKER SYSTEM: Comparação Inteligente ---
        if display_list == self.last_display_list:
            # Nada mudou? Então não fazemos o 'pisca-pisca' visual
            return
        
        self.last_display_list = display_list
        self.dash_label.set_label(f"{tr('dash_title')}: {len(display_list)}")

        # --- RECONSTRUÇÃO DA INTERFACE (Apenas se houver mudança real) ---
        while (child := self.dev_flow.get_first_child()):
            self.dev_flow.remove(child)

        if not display_list:
            sp = Adw.StatusPage(icon_name="video-display-symbolic", title=tr("no_dev"), description=tr("dash_sub"))
            self.dev_flow.append(sp)
        else:
            for dev in display_list:
                is_online = (dev['status'] == "online")
                # SE houver um active_uuid global, e o dispositivo estiver offline no state mas for o único da lista
                # ou se o is_st estiver True, forca o status 'conectado' para o dispositivo que está transmitindo
                if is_st and (dev['name'] == current_connected_name or len(display_list) == 1):
                    is_online = True
                
                # Container Principal com Overlay para o botão flutuante
                tile_overlay = Gtk.Overlay()
                tile_overlay.add_css_class("device-tile")
                if not is_online: tile_overlay.add_css_class("device-offline")

                # Box interna com os dados do dispositivo
                tile_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
                
                # Ícone Interativo (Botão de Alternância de Tipo)
                icon_map = {"pc": "🖥️", "mobile": "📱"}
                current_type = dev.get('type', 'remote')
                icon_char = icon_map.get(current_type, "🖥️")
                
                icon_btn = Gtk.Button(label=icon_char)
                icon_btn.add_css_class("device-icon-button")
                icon_btn.add_css_class("flat")
                icon_btn.set_tooltip_text(tr("device_icon_tip"))
                icon_btn.connect("clicked", self.on_device_type_toggle, dev['name'])
                tile_box.append(icon_btn)
                
                name_lbl = Gtk.Label(label=dev['name'], xalign=0.5); tile_box.append(name_lbl)
                
                badge = Gtk.Label()
                if is_online:
                    badge.set_label(tr("streaming"))
                    badge.add_css_class("success-label")
                    
                    # Botão EX PUS LAR (Emoji ❌ no Topo Direito)
                    kick_btn = Gtk.Button(label="❌")
                    kick_btn.add_css_class("kick-button")
                    kick_btn.add_css_class("flat")
                    kick_btn.set_tooltip_text("Desconectar Dispositivo")
                    kick_btn.set_halign(Gtk.Align.END)
                    kick_btn.set_valign(Gtk.Align.START)
                    kick_btn.set_margin_top(-10) # Ajuste fino de posição
                    kick_btn.set_margin_end(-10) 
                    kick_btn.connect("clicked", self.on_kick_clicked)
                    tile_overlay.add_overlay(kick_btn)
                else:
                    badge.set_label(tr("offline"))
                    badge.add_css_class("offline-label")
                
                tile_box.append(badge)
                tile_overlay.set_child(tile_box)
                self.dev_flow.append(tile_overlay)

    def on_device_type_toggle(self, b, device_name):
        """Alterna o tipo do dispositivo (ícone) e salva na memória."""
        types = ["pc", "mobile"]
        for dev in self.config.get("known_devices", []):
            if dev['name'] == device_name:
                curr = dev.get('type', 'remote')
                next_type = types[(types.index(curr) + 1) % len(types)] if curr in types else "pc"
                dev['type'] = next_type
                self._save_config_to_disk()
                self.build_dash() # Atualiza visualmente
                break

    def on_kick_clicked(self, b):
        session_id = getattr(self, 'current_session_id', None)
        print(f"DEBUG FRONTEND: Clicou em expulsar! ID: {session_id}")
        
        # Só notifica UMA VEZ por tentativa ativa para evitar o erro de excesso de notificações
        if hasattr(self, 'last_kick_time') and (time.time() - self.last_kick_time < 3.0):
            print("DEBUG FRONTEND: Spam detectado, ignorando clique extra.")
            return

        self.last_kick_time = time.time()
        self.backend.terminate_session(session_id)
        self.send_system_notification("⚠️ Expulsão", "A sessão de streaming foi encerrada manualmente.")

    def on_save_clicked(self, b):
        payload = {}
        for k, w in self.widgets.items():
            if isinstance(w, tuple): 
                sel_idx = w[0].get_selected()
                payload[k] = w[2][sel_idx][1]
                # Se for o monitor, salva o nome amigável para memória futura
                if k == "output_name":
                    self.config["last_monitor_name"] = w[2][sel_idx][0]
            elif isinstance(w, Adw.SwitchRow): payload[k] = "true" if w.get_active() else "false"
            elif isinstance(w, Adw.EntryRow): payload[k] = w.get_text()
        if self.backend.save_config(payload): 
            self.last_known_conf.update(payload) # Resync imediato da memória visual
            self.backend.restart_service()

    def on_pair_clicked(self, b):
        pin = self.pin_entry.get_text()
        if len(pin) == 4 and self.backend.pair_pin(pin): self.pin_entry.set_text("")

    def toggle_theme(self, b):
        # Ciclo: 0 (Light) -> 1 (Dark) -> 2 (Gamer) -> 0
        mode = (self.config.get("theme_mode", 1) + 1) % 3
        self.config["theme_mode"] = mode
        
        style_mgr = Adw.StyleManager.get_default()
        if mode == 0:
            style_mgr.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
        else:
            style_mgr.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
            
        # Ao sair do modo gamer, reseta para a cor original (fixa)
        if mode != 2:
            fixed_color = self.config.get("accent_color", "#9b30ff")
            self.apply_accent_color(fixed_color)
            
            # Sincroniza o seletor de cores (ColorButton)
            rgba = Gdk.RGBA()
            rgba.parse(fixed_color)
            self.c_btn.set_property("rgba", rgba)
            
        self._save_config_to_disk()
        self._update_theme_icon()

    def _rgb_cycle_timer(self):
        if self.config.get("theme_mode") == 2:
            step = self.config.get("rgb_speed", 0.005)
            self.hue = (self.hue + step) % 1.0
            r, g, b = colorsys.hls_to_rgb(self.hue, 0.6, 0.8)
            hex_color = f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
            
            # Aplica visualmente
            self.apply_accent_color(hex_color)
            
            # Sincroniza o ColorButton se existir
            rgba = Gdk.RGBA()
            rgba.parse(hex_color)
            self.c_btn.set_property("rgba", rgba)
        return True

    def cycle_rgb_speed(self, b):
        speeds = [0.002, 0.005, 0.010, 0.025]
        current = self.config.get("rgb_speed", 0.005)
        idx = speeds.index(current) if current in speeds else 1
        new_speed = speeds[(idx + 1) % len(speeds)]
        self.config["rgb_speed"] = new_speed
        self._update_speed_label()
        self._save_config_to_disk()

    def _update_speed_label(self):
        speed = self.config.get("rgb_speed", 0.005)
        labels = {0.002: "🐢 Lento", 0.005: "🐇 Normal", 0.010: "🐆 Rápido", 0.025: "🔥 INSANO"}
        self.speed_btn.set_label(labels.get(speed, "🐇 Normal"))

    def _save_config_to_disk(self):
        try:
            if not os.path.exists(CONFIG_DIR): os.makedirs(CONFIG_DIR)
            with open(CONFIG_FILE, "w") as f:
                json.dump(self.config, f)
        except: pass

    def _update_theme_icon(self):
        mode = self.config.get("theme_mode", 1)
        if mode == 0:
            self.t_img.set_from_icon_name("weather-clear-symbolic")
            self.t_lbl.set_label(self.tr("light"))
        elif mode == 1:
            self.t_img.set_from_icon_name("weather-clear-night-symbolic")
            self.t_lbl.set_label(self.tr("dark"))
        else:
            self.t_img.set_from_icon_name("input-gaming-symbolic")
            self.t_lbl.set_label(self.tr("gamer"))

    def on_color_set(self, b):
        rgba = b.get_rgba(); color = f"#{int(rgba.red * 255):02x}{int(rgba.green * 255):02x}{int(rgba.blue * 255):02x}"
        self.config["accent_color"] = color; self.apply_accent_color(color)

    def apply_accent_color(self, c):
        css = f":root {{ --accent-color: {c}; }}"
        self.accent_provider.load_from_data(css.encode())

    def _load_css(self):
        try:
            display = Gdk.Display.get_default()
            # CSS Principal
            prov = Gtk.CssProvider()
            prov.load_from_path(resource_path('style.css'))
            Gtk.StyleContext.add_provider_for_display(display, prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
            
            # Provedor de Cores de Destaque (Acoplado ao Ciclo RGB)
            Gtk.StyleContext.add_provider_for_display(display, self.accent_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        except Exception as e:
            print(f"DEBUG: Erro ao carregar CSS central: {e}")

    def send_system_notification(self, title, message):
        """Envia uma notificação nativa para o sistema (GNOME, KDE, etc.)"""
        try:
            notification = Gio.Notification.new(title)
            notification.set_body(message)
            # Usa o ícone do próprio app na notificação
            icon = Gio.ThemedIcon.new("io.github.farosh.parshine")
            notification.set_icon(icon)
            self.send_notification("parshine-status", notification)
        except Exception as e:
            print(f"DEBUG: Falha ao enviar notificação: {e}")

if __name__ == '__main__':
    app = ProjetoPApp()
    app.run(None)
