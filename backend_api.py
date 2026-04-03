import os
import shutil
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
        # HEADERS ANTICSRF: Crucial para evitar Erro 400 em operações de alteração de estado (DELETE/POST)
        self.session.headers.update({
            "Origin": "https://localhost:47990",
            "Referer": "https://localhost:47990/",
            "X-Requested-With": "XMLHttpRequest"
        })
        self.client_cache = {} # Cache persistente para nomes de rede

    def ensure_setup(self):
        """Pre-configura o admin:admin se for a primeira vez."""
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir, exist_ok=True)
            subprocess.run(["sunshine", "--creds", "admin", "admin"], 
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def is_installed(self):
        """Verifica se o binário do Sunshine está presente no PATH."""
        return shutil.which("sunshine") is not None

    def auto_setup(self):
        """Verifica instalação e inicia o serviço se necessário."""
        if not self.is_installed():
            print("DEBUG: Sunshine não encontrado no sistema.")
            return False
        
        self.ensure_setup()
        
        if not self.is_running():
            print("DEBUG: Sunshine detectado, mas parado. Iniciando...")
            return self.start()
        
        return True

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
        """Busca as configurações via API com fallback para leitura direta de arquivo."""
        try:
            r = self.session.get(f"{self.api_url}/config", timeout=1)
            if r.status_code == 200:
                return r.json()
        except: pass
        
        # FALLBACK: Se a API falhar (503/Restart), lê direto do arquivo de disco
        conf_path = os.path.join(self.config_dir, "sunshine.conf")
        if os.path.exists(conf_path):
            try:
                conf = {}
                with open(conf_path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if "=" in line and not line.startswith("#"):
                            parts = line.split("=", 1)
                            if len(parts) == 2:
                                k, v = parts[0].strip(), parts[1].strip()
                                # Remove aspas se existirem
                                if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                                    v = v[1:-1]
                                conf[k] = v
                return conf
            except: pass
        return {}

    def save_config(self, config_data):
        try:
            sanitized = {}
            # Lista de chaves que DEVEM ser tratadas como String (Texto)
            string_keys = ["sunshine_name", "gamepad_kind", "capture_method", "encoder", "sw_preset", "sw_tune", 
                           "nvenc_preset", "nvenc_coder", "web_ui_allowed_origin", "audio"]
            
            # Lista de chaves que DEVEM ser tratadas como Booleanos (0 ou 1)
            bool_keys = ["upnp", "nvenc_aq", "vaapi_strict_rc_buffer", "audio", "gamepad", 
                         "motion_as_ds4", "touchpad_as_ds4", "ds5_inputtino_randomize_mac",
                         "keyboard", "key_rightalt_to_key_win", "mouse", "hires_scrolling", "native_touch"]

            for k, v in config_data.items():
                if k in bool_keys:
                    sanitized[k] = 1 if str(v).lower() == "true" else 0
                elif k in string_keys:
                    sanitized[k] = str(v)
                elif k == "resolutions":
                    sanitized[k] = [v] if isinstance(v, str) else v
                else:
                    try:
                        # Tenta converter para int o que sobrar (resoluções, fps, bitrate, etc)
                        sanitized[k] = int(v)
                    except:
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

    def terminate_session(self, sid=None):
        """Força o encerramento de conexões ativas testando múltiplos endpoints e payloads."""
        print(f"DEBUG BACKEND: Início de terminate_session. ID: {sid}")
        try:
            # 1. Tenta DELETE nos endpoints comuns
            for endpoint in ["connections", "sessions", "rest/sessions", "rest/connections"]:
                if sid:
                    url = f"{self.api_url}/{endpoint}/{sid}"
                    r = self.session.delete(url, timeout=2)
                    print(f"DEBUG BACKEND: DELETE {endpoint} status: {r.status_code}")
                    if r.status_code in [200, 204]: return True
            
            # 2. Tenta POST /terminate com diferentes payloads
            targets = ["terminate", "sessions/terminate", "connections/terminate"]
            payload_keys = ["uuid", "id", "sessionId"]
            
            for target in targets:
                url = f"{self.api_url}/{target}"
                # Tentativa com Payload
                if sid:
                    for key in payload_keys:
                        payload = {key: sid}
                        r = self.session.post(url, json=payload, timeout=2)
                        print(f"DEBUG BACKEND: POST {target} ({key}) status: {r.status_code}")
                        if r.status_code in [200, 204]: return True
                
                # Tentativa SEM payload (limpeza geral)
                r = self.session.post(url, timeout=2)
                print(f"DEBUG BACKEND: POST {target} (no-body) status: {r.status_code}")
                if r.status_code in [200, 204]: return True

            # 3. Tenta via RPC se o resto falhar (algumas versões aceitam isso)
            if sid:
                 url = f"{self.api_url}/sessions"
                 r = self.session.post(url, json={"action": "terminate", "id": sid}, timeout=2)
                 print(f"DEBUG BACKEND: RPC Terminate status: {r.status_code}")
                 if r.status_code in [200, 204]: return True

            # 4. ÚLTIMO RECURSO (NÚCLEO): Se nada expulsou, reinicia o serviço inteiro
            print("DEBUG BACKEND: Todas as tentativas de expulsão falharam. Reiniciando o serviço para forçar a saída.")
            return self.restart_service()

        except Exception as e:
            print(f"DEBUG BACKEND: ERRO CRÍTICO em terminate_session: {e}")
            # Fallback mesmo em erro crítico
            return self.restart_service()
        return False

    def is_streaming(self):
        """Detecta se há uma conexão ativa via Áudio (pactl)."""
        try:
            res = subprocess.getoutput("pactl --format=json list source-outputs")
            if not res or res.strip() in ["[]", "{}", ""]: return False
            
            data = json.loads(res)
            # pactl pode retornar uma lista ou um objeto único
            items = data if isinstance(data, list) else [data]
            
            for item in items:
                if not isinstance(item, dict): continue
                props = item.get("properties", {})
                # Nome do app pode variar (sunshine ou Sunshine)
                app_name = str(props.get("application.name", "")).lower()
                if app_name == "sunshine" and not item.get("corked", True):
                    return True
        except Exception as e:
            print(f"DEBUG BACKEND: Erro ao checar streaming (PulseAudio): {e}")
            
        return False

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
        """Busca o ID da conexão ativa em múltiplos endpoints da API e logs."""
        # 1. TENTA VIA API (MODERNO E SEGURO)
        for endpoint in ["connections", "sessions", "rest/sessions", "rest/connections"]:
            try:
                r = self.session.get(f"{self.api_url}/{endpoint}", timeout=1)
                if r.status_code == 200:
                    data = r.json()
                    # O Sunshine pode retornar um objeto {"connections": [...]} OU uma lista [...]
                    conns = []
                    if isinstance(data, list): conns = data
                    elif isinstance(data, dict):
                        conns = data.get("connections", []) or data.get("sessions", []) or data.get("data", [])
                        if not conns:
                            # Tenta converter mapa de chaves se a estrutura for ID -> Dados
                            conns = [{"id": k, **v} for k, v in data.items() if isinstance(v, dict)]
                    
                    if conns:
                        # Pega o ID da primeira conexão encontrada
                        for c in conns:
                            sid = c.get("id") or c.get("uuid") or c.get("sessionId")
                            if sid: return sid
            except: pass

        # 2. FALLBACK: SCAN TOTAL DO LOG (O arquivo do user tem 100k+ linhas devido ao spam de vídeo)
        try:
            log_file = os.path.join(self.config_dir, "sunshine.log")
            if os.path.exists(log_file):
                # O grep -a força tratar como texto (evita o erro "arquivo binário coincide")
                pat = r'[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}'
                cmd = f'grep -oaE "{pat}" "{log_file}" | tail -n 1'
                res = subprocess.getoutput(cmd)
                if res.strip() and not res.strip().startswith("grep"):
                    uuid = res.strip().lower()
                    return uuid
        except Exception as e:
            print(f"DEBUG BACKEND: Falha no scan do log: {e}")
        
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
