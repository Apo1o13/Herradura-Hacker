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
# Helpers de layout
# ─────────────────────────────────────────────────────────────────────────────
BOX_W  = 62          # ancho visible de la caja (sin bordes)
INNER  = BOX_W - 2   # ancho interior (sin │ de cada lado)

def _tw():
    return max(shutil.get_terminal_size((80, 24)).columns, 80)

def _margin():
    """Espacios a la izquierda para centrar la caja de BOX_W+2 chars."""
    return " " * max(0, (_tw() - (BOX_W + 2)) // 2)

def _row(content_visible, content_with_color):
    """
    Construye una línea de caja:  │ content                    │
    content_visible : string sin ANSI para medir longitud
    content_with_color : string con ANSI para imprimir
    """
    pad = INNER - len(content_visible)
    m = _margin()
    return f"{m}{CYAN}│{END} {content_with_color}{' ' * max(0, pad)}{CYAN}│{END}"

def _sep(char="─", title=""):
    m = _margin()
    if title:
        t = f" {WHITE}{title}{END} "
        tv = len(f" {title} ")
        line = char * ((BOX_W - tv) // 2) + f" {WHITE}{title}{END} " + char * ((BOX_W - tv + 1) // 2)
        return f"{m}{CYAN}├{line}┤{END}"
    return f"{m}{CYAN}├{'─' * BOX_W}┤{END}"

def _top():
    m = _margin()
    return f"{m}{CYAN}┌{'─' * BOX_W}┐{END}"

def _bot():
    m = _margin()
    return f"{m}{CYAN}└{'─' * BOX_W}┘{END}"

# ─────────────────────────────────────────────────────────────────────────────

def banner():
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

    tw = _tw()
    print()
    for line in logo_lines:
        print(f"{GREEN}{pad}{line}{END}")
    print()

    # Título — centrado respecto al ancho del terminal
    t1v = len("---< Herradura Hack v5.0 >---")
    t2v = len("---< Creador: Apo1o13 >---")
    sv  = len("Uso exclusivo para pentesting autorizado")
    lp1 = " " * max(0, (tw - t1v) // 2)
    lp2 = " " * max(0, (tw - t2v) // 2)
    lps = " " * max(0, (tw - sv) // 2)

    print(f"{lp1}{RED}---< {WHITE}Herradura Hack {GREEN}v5.0 {RED}>---{END}")
    print(f"{lp2}{RED}---< {WHITE}Creador: {GREEN}Apo1o13 {RED}>---{END}")
    print(f"{lps}{DIM}Uso exclusivo para pentesting autorizado{END}")
    print()


def menu():
    m = _margin()

    # ── Caja principal ─────────────────────────────────────────────────────────
    print(_top())

    # Modo guiado highlight
    wv = "[W]  MODO GUIADO  \u2190 empieza aqui si eres nuevo"
    wc = f"{GREEN}[W]{END}  {WHITE}MODO GUIADO{END}  {DIM}\u2190 empieza aqui si eres nuevo{END}"
    print(_row(wv, wc))

    print(_sep(title="AUTOMATICOS  RECOMENDADOS"))

    lines_auto = [
        ("[35] Exploit Engine AUTO   auto-exploit + progreso %",
         f"{RED}[35]{END} {GREEN}Exploit Engine AUTO  {END} {DIM}auto-exploit + progreso %{END}"),
        ("[36] Exploit Engine MASIVO varias redes en secuencia",
         f"{RED}[36]{END} {GREEN}Exploit Engine MASIVO{END} {DIM}varias redes en secuencia{END}"),
        ("[33] Auditoria Express     escanea -> analiza -> ataca",
         f"{RED}[33]{END} {CYAN}Auditoria Express    {END} {DIM}escanea -> analiza -> ataca{END}"),
        ("[31] Auto-Pwner            ataque total automatico",
         f"{RED}[31]{END} {CYAN}Auto-Pwner           {END} {DIM}ataque total automatico{END}"),
    ]
    for vis, col in lines_auto:
        print(_row(vis, col))

    print(_sep(title="ATAQUES WiFi"))

    lines_atk = [
        ("[7]  Handshake WPA/WPA2   [9]  PMKID (sin clientes)",
         f"{RED}[7]{END}  {GREEN}Handshake WPA/WPA2   {END}{RED}[9]{END}  {YELLOW}PMKID (sin clientes){END}"),
        ("[10] WPS Pixie/PIN        [15] Evil Twin + Portal",
         f"{RED}[10]{END} {GREEN}WPS Pixie/PIN        {END}{RED}[15]{END} {RED}Evil Twin + Portal{END}"),
        ("[21] KARMA/MANA           [23] WPA Enterprise",
         f"{RED}[21]{END} {RED}KARMA/MANA           {END}{RED}[23]{END} {MAGENTA}WPA Enterprise{END}"),
        ("[17] Auto-Crack           [25] WEP Full Attack",
         f"{RED}[17]{END} {YELLOW}Auto-Crack           {END}{RED}[25]{END} {GREEN}WEP Full Attack{END}"),
        ("[13] Deautenticacion      [27] Hidden SSID Revealer",
         f"{RED}[13]{END} {GREEN}Deautenticacion      {END}{RED}[27]{END} {YELLOW}Hidden SSID Revealer{END}"),
    ]
    for vis, col in lines_atk:
        print(_row(vis, col))

    print(_sep(title="AVANZADO   CVEs"))

    lines_adv = [
        ("[32] Vulns Modernas 2025  [34] Suite CVE 2019-2024",
         f"{RED}[32]{END} {RED}Vulns Modernas 2025  {END}{RED}[34]{END} {MAGENTA}Suite CVE 2019-2024{END}"),
        ("[28] Post-Explotacion     [26] Deauth Hopping",
         f"{RED}[28]{END} {RED}Post-Explotacion     {END}{RED}[26]{END} {GREEN}Deauth Hopping{END}"),
    ]
    for vis, col in lines_adv:
        print(_row(vis, col))

    print(_sep(title="HERRAMIENTAS"))

    lines_tools = [
        ("[1] Monitor ON   [2] Monitor OFF   [5] Escanear",
         f"{RED}[1]{END} {GREEN}Monitor ON   {END}{RED}[2]{END} {GREEN}Monitor OFF   {END}{RED}[5]{END} {GREEN}Escanear{END}"),
        ("[12] MAC Spoof   [20] Dependencias  [6] Scan Vivo",
         f"{RED}[12]{END} {GREEN}MAC Spoof   {END}{RED}[20]{END} {CYAN}Dependencias  {END}{RED}[6]{END} {GREEN}Scan Vivo{END}"),
        ("[37] Setup Adaptador  [38] Lista adaptadores soportados",
         f"{RED}[37]{END} {GREEN}Setup Adaptador  {END}{RED}[38]{END} {GREEN}Lista adaptadores soportados{END}"),
        ("[29] Historial   [30] Reporte HTML   [0] Salir",
         f"{RED}[29]{END} {CYAN}Historial   {END}{RED}[30]{END} {CYAN}Reporte HTML   {END}{RED}[0]{END} {RED}Salir{END}"),
    ]
    for vis, col in lines_tools:
        print(_row(vis, col))

    print(_bot())
    print()


def goodbye():
    skull = [
        "        ░░░░░░░░░░░░░░░░░░░░░░░░",
        "      ░░                        ░░",
        "    ░░    ████████████████████    ░░",
        "   ░░   ██                    ██   ░░",
        "   ░░  ██  ██████    ██████  ██  ░░",
        "   ░░  ██  ██████    ██████  ██  ░░",
        "   ░░  ██                    ██  ░░",
        "   ░░   ██   ████████████   ██   ░░",
        "   ░░    ██████        ██████    ░░",
        "   ░░    ██ ████████████ ██    ░░",
        "   ░░    ████            ████    ░░",
        "      ░░                        ░░",
        "        ░░░░░░░░░░░░░░░░░░░░░░░░",
    ]
    tw = _tw()
    print()
    for line in skull:
        pad = " " * max(0, (tw - len(line)) // 2)
        print(f"{RED}{pad}{line}{END}")
    print()

    msg1 = "~ Hasta la proxima ~"
    msg2 = "Herradura Hack v5.0 — Apo1o13"
    p1 = " " * max(0, (tw - len(msg1)) // 2)
    p2 = " " * max(0, (tw - len(msg2)) // 2)
    print(f"{p1}{WHITE}{msg1}{END}")
    print(f"{p2}{DIM}{msg2}{END}")
    print()


banner()
menu()
