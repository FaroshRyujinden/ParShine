import os
import subprocess
import requests
import time
import json
import socket
import urllib3

# Disable insecure warnings for self-signed localhost certs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class SunshineBackend:
    def __init__(self, username="admin", password="admin"):
        self.config_dir = os.path.expanduser("~/.config/sunshine")
        self.api_url = "https://localhost:47990/api"
        self.auth = (username, password)
        self.session = requests.Session()
        self.session.auth = self.auth
        self.session.verify = False
        self.client_cache = {} # Cache persistente para nomes de rede

    def ensure_setup(self):
        """Pre-configura o admin:admin se for a primeira vez."""
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir, exist_ok=True)
            subprocess.run(["sunshine", "--creds", "admin", "admin"], 
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def is_running(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)
                return s.connect_ex(('127.0.0.1', 47990)) == 0
        except:
            return False

    def start(self):
        if not self.is_running():
            subprocess.Popen(["sunshine"], 
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL,
                             start_new_session=True)
            for _ in range(20):
                time.sleep(0.5)
                if self.is_running(): return True
        return self.is_running()

    def get_config(self):
        try:
            r = self.session.get(f"{self.api_url}/config", timeout=2)
            if r.status_code == 200:
                return r.json()
        except: pass
        return {}

    def save_config(self, config_data):
        try:
            sanitized = {}
            for k, v in config_data.items():
                if k in ["max_bitrate", "fps", "min_log_level", "hevc_mode", "qp", "upnp", 
                         "nvenc_preset", "nvenc_multipass", "nvenc_vbr_padding_percent",
                         "nvenc_aq", "nvenc_coder", "vaapi_strict_rc_buffer",
                         "fec_percentage", "min_threads", "av1_mode", "display_id", "min_fps",
                         "address_family", "port", "web_ui_allowed_origin", "lan_encryption",
                         "wan_encryption", "ping_timeout", "audio",
                         "sunshine_name", "gamepad_kind", "capture_method", "encoder",
                         "sw_preset", "sw_tune",
                         "gamepad", "motion_as_ds4", "touchpad_as_ds4", "ds5_inputtino_randomize_mac",
                         "back_button_timeout", "keyboard", "key_rightalt_to_key_win", "mouse",
                         "hires_scrolling", "native_touch"]:
                    try:
                        if k in ["upnp", "nvenc_aq", "nvenc_coder", "vaapi_strict_rc_buffer", "audio",
                                 "gamepad", "motion_as_ds4", "touchpad_as_ds4", "ds5_inputtino_randomize_mac",
                                 "keyboard", "key_rightalt_to_key_win", "mouse", "hires_scrolling", "native_touch"]:
                            sanitized[k] = 1 if str(v).lower() == "true" else 0
                        else:
                            sanitized[k] = int(v)
                    except: sanitized[k] = v
                elif k == "resolutions":
                    # Sunshine espera uma lista de resoluções. Ex: ["1920x1080"]
                    sanitized[k] = [v] if isinstance(v, str) else v
                else:
                    sanitized[k] = v

            current = self.get_config()
            # SEGURANÇA: Se o config atual falhar ao carregar, não salve por cima (evita o crash 503)
            if not current or len(current) < 5: 
                print("ERROR: Não foi possível obter o config do Sunshine. Abortando salvamento seguro.")
                return False

            current.update(sanitized)
            
            r = self.session.post(f"{self.api_url}/config", json=current, timeout=5)
            if r.status_code != 200:
                print(f"DEBUG: Erro {r.status_code} no Sunshine: {r.text}")
            return r.status_code == 200
        except Exception as e:
            print(f"DEBUG: Erro crítico ao salvar: {e}")
            return False

    def get_devices(self):
        try:
            r = self.session.get(f"{self.api_url}/devices", timeout=2)
            if r.status_code == 200:
                return r.json()
        except: pass
        
        # Fallback: Ler do arquivo de estado do Sunshine se a API falhar
        state_file = os.path.join(self.config_dir, "sunshine_state.json")
        if os.path.exists(state_file):
            try:
                with open(state_file, "r") as f:
                    data = json.load(f)
                    return data.get("clients", [])
            except: pass
        return []

    def pair_pin(self, pin):
        try:
            r = self.session.post(f"{self.api_url}/pin", json={"pin": str(pin)}, timeout=2)
            return r.status_code == 200
        except: return False

    def is_streaming(self):
        """Detecta se há uma conexão ativa verificando se o Sunshine está gravando áudio (pactl)."""
        try:
            # Pega lista de fontes de áudio sendo gravadas em formato JSON
            res = subprocess.getoutput("pactl --format=json list source-outputs")
            if not res.strip() or res.strip() == "[]": return False
            
            data = json.loads(res)
            for item in data:
                props = item.get("properties", {})
                if props.get("application.name") == "sunshine" and not item.get("corked", True):
                    return True
            return False
        except: return False

    def get_streaming_client(self):
        """Tenta identificar o dispositivo conectado via rede, logs e tailscale."""
        try:
            remote_ip = None
            # 1. Busca IP remoto via ss ou logs
            res = subprocess.getoutput("ss -unp | grep -i sunshine | grep -v '0.0.0.0' | grep -v '127.0.0.1'")
            if res.strip():
                import re
                ips = re.findall(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', res)
                if ips: remote_ip = ips[0]
            
            if not remote_ip:
                log_path = os.path.join(self.config_dir, 'sunshine.log')
                if os.path.exists(log_path):
                    # Pega a última IP mencionada como 'Control peer address'
                    res_log = subprocess.getoutput(f"grep -i 'Control peer address' {log_path} | tail -n 1")
                    if res_log.strip():
                        import re
                        ips = re.findall(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', res_log)
                        if ips: remote_ip = ips[0]

            if not remote_ip: return None
            
            # 2. Verifica cache (melhora estabilidade visual)
            if remote_ip in self.client_cache: return self.client_cache[remote_ip]
            
            # 3. Tenta resolver via mDNS (Avahi) - Ótimo para celulares/Poco
            res_av = subprocess.getoutput(f"getent hosts {remote_ip}")
            if res_av.strip():
                name = res_av.split()[-1].split('.')[0]
                if name and name != remote_ip:
                    c_info = {"name": name, "ip": remote_ip, "type": "mobile"}
                    self.client_cache[remote_ip] = c_info
                    return c_info
            
            # 4. Tenta resolver via Tailscale
            ts_res = subprocess.getoutput("tailscale status")
            for line in ts_res.splitlines():
                if remote_ip in line:
                    parts = line.split()
                    c_info = {"name": parts[1], "ip": remote_ip, "type": parts[3] if len(parts) > 3 else "tailscale"}
                    self.client_cache[remote_ip] = c_info
                    return c_info
            
            # 5. Fallback: Hostname local
            try:
                host = socket.getfqdn(remote_ip)
                if host and host != remote_ip:
                    c_info = {"name": host.split('.')[0], "ip": remote_ip, "type": "remote"}
                    self.client_cache[remote_ip] = c_info
                    return c_info
            except: pass
            
            return {"name": f"Dispositivo ({remote_ip})", "ip": remote_ip, "type": "remote"}
        except: return None

    def get_active_uuid(self):
        """Busca o UUID do cliente que iniciou a transmissão lendo os logs do Sunshine."""
        try:
            log_file = os.path.join(self.config_dir, "sunshine.log")
            if not os.path.exists(log_file): return None
            
            # Pega as últimas 100 linhas e busca o último UUID mencionado
            res = subprocess.getoutput(f"tail -n 100 {log_file} | grep -i 'uuid' | tail -n 1")
            if not res.strip(): return None
            
            import re
            match = re.search(r'uuid\s*--\s*([a-fA-F0-9-]+)', res)
            return match.group(1).lower() if match else None
        except: 
            return None

    def restart_service(self):
        print("DEBUG: Executando restart_service...")
        try:
            self.session.post(f"{self.api_url}/restart", timeout=1)
        except:
            pass
        
        subprocess.run(["pkill", "-9", "sunshine"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Tempo de 3 segundos para estabilizar drivers multi-monitor
        time.sleep(3.0)
        
        return self.start()
