#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Herradura Hack v5.0 — banner.py
# Creador: Apo1o13

import os
import shutil
from colorama import Style

# Colores
RED     = '\033[1;31m'
GREEN   = '\033[1;32m'
YELLOW  = '\033[1;33m'
CYAN    = '\033[1;36m'
WHITE   = '\033[1;37m'
MAGENTA = '\033[1;35m'
DIM     = '\033[2m'
END     = '\033[0m'

os.system("clear")

# ─────────────────────────────────────────────────────────────────────────────
# Centrado dinámico según ancho real del terminal
# ─────────────────────────────────────────────────────────────────────────────
def _tw():
    """Ancho del terminal (mínimo 80)."""
    return max(shutil.get_terminal_size((80, 24)).columns, 80)

def _c(text, visual_len=None):
    """Centra `text` usando `visual_len` como ancho visual (sin ANSI)."""
    tw = _tw()
    vl = visual_len if visual_len is not None else len(text)
    pad = max(0, (tw - vl) // 2)
    return " " * pad + text

# ─────────────────────────────────────────────────────────────────────────────

def banner():
    # Cada línea del logo tiene 22 caracteres braille de ancho visual
    LOGO_W = 22
    tw = _tw()
    pad = " " * max(0, (tw - LOGO_W) // 2)

    logo_lines = [
        "⠀⠀⠀⠀⢀⣠⣴⣶⣿⣿⣿⣿⣿⣿⣶⣦⣄⡀⠀⠀⠀⠀",
        "⠀⠀⢀⣴⣿⣿⠿⢿⣿⣿⣉⣉⣿⣿⡿⠿⣿⣿⣦⡀⠀⠀",
        "⠀⣴⣿⣿⣿⣇⣤⣾⣿⣿⣿⣿⣿⣿⣷⣤⣸⣿⣿⣿⣦⠀",
        "⣰⣿⡿⠋⣻⣿⣿⠟⠉⠉⠀⠀⠉⠙⠻⣿⣿⣟⠙⢿⣿⣆",
        "⣿⣿⣧⣴⣿⣿⠁⠀⠀⠀⠀⠀⠀⠀⠀⠈⣿⣿⣦⣼⣿⣿",
        "⣿⣿⣿⣿⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣿⣿⣿⣿",
        "⣿⣿⣿⣿⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣿⣿⣿⣿",
        "⢻⣿⣿⣿⣿⣧⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣼⣿⣿⣿⣿⡟",
        "⠈⣿⣿⣿⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⣿⣿⣿⠁",
        "⠀⠹⣿⣿⣿⣿⣧⠀⠀⠀⠀⠀⠀⠀⠀⣼⣿⣿⣿⣿⠏⠀",
        "⠀⠀⠹⣿⣿⣿⣿⡄⠀⠀⠀⠀⠀⠀⢠⣿⣿⣿⣿⠏⠀⠀",
        "⢠⣶⣶⣿⣿⣿⣿⣷⠀⠀⠀⠀⠀⠀⣾⣿⣿⣿⣿⣶⣶⡄",
        "⠸⣿⣿⣿⣿⣿⣿⠟⠀⠀⠀⠀⠀⠀⠻⣿⣿⣿⣿⣿⣿⠇",
    ]

    print()
    for line in logo_lines:
        print(f"{GREEN}{pad}{line}{END}")
    print()

    # Título centrado
    title1_vis = len("---< Herradura Hack v5.0 >---")
    title2_vis = len("---< Creador: Apo1o13 >---")
    sub_vis    = len("Uso exclusivo para pentesting autorizado")

    print(_c(f"{RED}---< {WHITE}Herradura Hack {GREEN}v5.0 {RED}>---{END}", title1_vis))
    print(_c(f"{RED}---< {WHITE}Creador: {GREEN}Apo1o13 {RED}>---{END}",    title2_vis))
    print(_c(f"{DIM}Uso exclusivo para pentesting autorizado{END}",          sub_vis))
    print()


def menu():
    tw = _tw()
    sep = f" {WHITE}{'─' * (tw - 2)}{END}"

    print(_c(f"\033[1;36m╔{'═'*54}╗\033[0m", 56))
    print(_c(f"\033[1;36m║\033[0m  \033[1;32m[W]\033[0m \033[1;37mMODO GUIADO\033[0m \033[2m← empieza aquí si eres nuevo\033[0m           \033[1;36m║\033[0m", 56))
    print(_c(f"\033[1;36m╚{'═'*54}╝\033[0m", 56))
    print()

    # ── RECOMENDADOS ─────────────────────────────────────────────────────────
    print(_c(f"{WHITE}── AUTOMÁTICOS (RECOMENDADOS) ─────────────────────────────{END}", 60))
    print(_c(f"{RED}[35]{END} {GREEN}Exploit Engine AUTO      {DIM}(exploit + progreso % real){END}   "
             f"{RED}[36]{END} {GREEN}Exploit Engine MASIVO  {DIM}(varias redes){END}", 90))
    print(_c(f"{RED}[31]{END} {GREEN}Auto-Pwner               {DIM}(ataque total automático){END}   "
             f"{RED}[33]{END} {CYAN}Auditoría Express      {DIM}(análisis + exploit){END}", 90))
    print()

    # ── ATAQUES ───────────────────────────────────────────────────────────────
    print(_c(f"{WHITE}── ATAQUES WiFi ────────────────────────────────────────────{END}", 62))
    rows = [
        (f"{RED}[7]{END}  {GREEN}Handshake WPA/WPA2  {DIM}(deauth){END}",
         f"{RED}[9]{END}  {YELLOW}PMKID               {DIM}(sin clientes){END}"),
        (f"{RED}[10]{END} {GREEN}WPS Pixie/PIN       {DIM}(brute){END}",
         f"{RED}[15]{END} {RED}Evil Twin           {DIM}(AP falso+portal){END}"),
        (f"{RED}[21]{END} {RED}KARMA/MANA          {DIM}(auto-conectar devs){END}",
         f"{RED}[23]{END} {MAGENTA}WPA Enterprise      {DIM}(corp/uni){END}"),
        (f"{RED}[17]{END} {YELLOW}Auto-Crack          {DIM}(captura+crack auto){END}",
         f"{RED}[25]{END} {GREEN}WEP Full Attack     {DIM}(ARP replay){END}"),
        (f"{RED}[13]{END} {GREEN}Deautenticación     {DIM}(desconectar){END}",
         f"{RED}[27]{END} {YELLOW}Hidden SSID         {DIM}(redes ocultas){END}"),
    ]
    for left, right in rows:
        print(_c(f"{left}   {right}", 90))
    print()

    # ── AVANZADO ──────────────────────────────────────────────────────────────
    print(_c(f"{WHITE}── AVANZADO & CVEs ─────────────────────────────────────────{END}", 62))
    print(_c(f"{RED}[32]{END} {RED}Vulns Modernas 2025  {DIM}(Dragonblood/KRACK){END}   "
             f"{RED}[34]{END} {MAGENTA}Suite CVE 2019-2024  {DIM}(Kr00k/Frag/EAP){END}", 90))
    print(_c(f"{RED}[28]{END} {RED}Post-Explotación     {DIM}(scan vuln+LAN){END}   "
             f"{RED}[26]{END} {GREEN}Deauth Hopping       {DIM}(todos canales){END}", 90))
    print()

    # ── HERRAMIENTAS ──────────────────────────────────────────────────────────
    print(_c(f"{WHITE}── HERRAMIENTAS ────────────────────────────────────────────{END}", 62))
    print(_c(
        f"{RED}[1]{END} {GREEN}Monitor ON{END}  "
        f"{RED}[2]{END} {GREEN}Monitor OFF{END}  "
        f"{RED}[5]{END} {GREEN}Escanear{END}  "
        f"{RED}[6]{END} {GREEN}Scan Vivo{END}  "
        f"{RED}[12]{END} {GREEN}MAC Spoof{END}", 80))
    print(_c(
        f"{RED}[20]{END} {CYAN}Dependencias{END}  "
        f"{RED}[24]{END} {CYAN}OSINT Wordlist{END}  "
        f"{RED}[29]{END} {CYAN}Historial{END}  "
        f"{RED}[30]{END} {CYAN}Reporte HTML{END}  "
        f"{RED}[0]{END} {RED}Salir{END}", 80))
    print()


def goodbye():
    print(f"""
 {WHITE}------------------------------------------------------{END}
\033[1;34m    _____  ____   ____  _____  ______     ________ _
   / ____|/ __ \\ / __ \\|  __ \\|  _ \\ \\   / /  ____| |
  | |  __| |  | | |  | | |  | | |_) \\ \x5c_/ /| |__  | |
  | | |_ | |  | | |  | | |  | |  _ < \\   / |  __| | |
  | |__| | |__| | |__| | |__| | |_) | | |  | |____|_|
   \\_____|\x5c____/ \\____/|_____/|____/  |_|  |______(_)\x1b[0m

     {RED}<{WHITE}El poder del usuario radica en su ANONIMATO{RED}>{END}

 {WHITE}------------------------------------------------------{END}
""" + WHITE + Style.NORMAL)


banner()
menu()
