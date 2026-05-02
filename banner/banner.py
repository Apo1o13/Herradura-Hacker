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
    # ─── helpers internos ────────────────────────────────────────────────────
    def _r2(lv, lc, rv, rc):
        """Fila de dos columnas de igual ancho (INNER // 2 cada una)."""
        COL = (INNER - 1) // 2          # ancho por columna
        pad_l = COL - len(lv)
        pad_r = INNER - COL - 1 - len(rv)
        m = _margin()
        return (f"{m}{CYAN}│{END} {lc}{' ' * max(0,pad_l)}"
                f"{CYAN}│{END} {rc}{' ' * max(0,pad_r)}{CYAN}│{END}")

    def _r1(vis, col):
        """Fila de ancho completo."""
        return _row(vis, col)

    def _blank():
        return _row(" " * INNER, " " * INNER)

    # ─── cabecera ────────────────────────────────────────────────────────────
    print(_top())

    # [W] — fila completa destacada
    wv = " [W]  MODO GUIADO COMPLETO  \u2190 todos los ataques en automatico "
    wc = f" {GREEN}[W]{END}  {WHITE}MODO GUIADO COMPLETO{END}  {DIM}\u2190 todos los ataques en automatico{END} "
    print(_r1(wv, wc))

    # ─── AUTOMATICOS ─────────────────────────────────────────────────────────
    print(_sep(title="AUTOMATICOS"))
    print(_r2(
        "[31] Auto-Pwner          ataque total auto",
        f"{RED}[31]{END} {CYAN}Auto-Pwner         {END} {DIM}ataque total auto{END}",
        "[33] Auditoria Express   escanea + analiza",
        f"{RED}[33]{END} {CYAN}Auditoria Express  {END} {DIM}escanea + analiza{END}",
    ))
    print(_r2(
        "[35] Exploit Engine      auto-exploit + %",
        f"{RED}[35]{END} {GREEN}Exploit Engine     {END} {DIM}auto-exploit + %{END}",
        "[36] Exploit Masivo      varias redes auto",
        f"{RED}[36]{END} {GREEN}Exploit Masivo     {END} {DIM}varias redes auto{END}",
    ))

    # ─── ATAQUES WiFi ────────────────────────────────────────────────────────
    print(_sep(title="ATAQUES WiFi"))
    print(_r2(
        "[ 7] Handshake WPA/WPA2  captura + crack",
        f"{RED}[ 7]{END} {GREEN}Handshake WPA/WPA2{END} {DIM}captura + crack{END}",
        "[ 9] PMKID               sin clientes",
        f"{RED}[ 9]{END} {YELLOW}PMKID              {END} {DIM}sin clientes{END}",
    ))
    print(_r2(
        "[10] WPS Pixie / PIN     brute + pixie",
        f"{RED}[10]{END} {GREEN}WPS Pixie / PIN   {END} {DIM}brute + pixie{END}",
        "[15] Evil Twin + Portal  AP falso + creds",
        f"{RED}[15]{END} {RED}Evil Twin + Portal{END} {DIM}AP falso + creds{END}",
    ))
    print(_r2(
        "[21] KARMA / MANA        probe response",
        f"{RED}[21]{END} {RED}KARMA / MANA      {END} {DIM}probe response{END}",
        "[23] WPA Enterprise      RADIUS falso",
        f"{RED}[23]{END} {MAGENTA}WPA Enterprise    {END} {DIM}RADIUS falso{END}",
    ))
    print(_r2(
        "[25] WEP Full Attack     ARP replay + key",
        f"{RED}[25]{END} {GREEN}WEP Full Attack   {END} {DIM}ARP replay + key{END}",
        "[17] Auto-Crack          HS + crack auto",
        f"{RED}[17]{END} {YELLOW}Auto-Crack        {END} {DIM}HS + crack auto{END}",
    ))
    print(_r2(
        "[13] Deautenticacion     desconectar clts",
        f"{RED}[13]{END} {GREEN}Deautenticacion   {END} {DIM}desconectar clts{END}",
        "[27] SSID Oculto         revelar nombre",
        f"{RED}[27]{END} {YELLOW}SSID Oculto       {END} {DIM}revelar nombre{END}",
    ))

    # ─── AVANZADO / CVEs ─────────────────────────────────────────────────────
    print(_sep(title="AVANZADO  /  CVEs"))
    print(_r2(
        "[32] Vulns Modernas 2025 FragAttacks/WPA3",
        f"{RED}[32]{END} {RED}Vulns Modernas    {END} {DIM}FragAttacks/WPA3{END}",
        "[34] Suite CVE 2019-24   Kr00k/EAP/SSID",
        f"{RED}[34]{END} {MAGENTA}Suite CVE 2019-24 {END} {DIM}Kr00k/EAP/SSID{END}",
    ))
    print(_r2(
        "[28] Post-Explotacion    scan red interna",
        f"{RED}[28]{END} {RED}Post-Explotacion  {END} {DIM}scan red interna{END}",
        "[26] Deauth Hopping      todos los canales",
        f"{RED}[26]{END} {GREEN}Deauth Hopping    {END} {DIM}todos los canales{END}",
    ))
    print(_r2(
        "[22] Probe Harvester     que redes buscan",
        f"{RED}[22]{END} {YELLOW}Probe Harvester   {END} {DIM}que redes buscan{END}",
        "[24] Wordlist OSINT      dic por SSID",
        f"{RED}[24]{END} {YELLOW}Wordlist OSINT    {END} {DIM}dic por SSID{END}",
    ))

    # ─── HERRAMIENTAS ────────────────────────────────────────────────────────
    print(_sep(title="HERRAMIENTAS"))
    print(_r2(
        "[ 1] Monitor ON          activar modo mon",
        f"{RED}[ 1]{END} {GREEN}Monitor ON        {END} {DIM}activar modo mon{END}",
        "[ 2] Monitor OFF         desactivar mon",
        f"{RED}[ 2]{END} {GREEN}Monitor OFF       {END} {DIM}desactivar mon{END}",
    ))
    print(_r2(
        "[ 5] Escanear + CSV      guardar redes",
        f"{RED}[ 5]{END} {GREEN}Escanear + CSV    {END} {DIM}guardar redes{END}",
        "[ 6] Scan Vivo           tabla en tiempo real",
        f"{RED}[ 6]{END} {GREEN}Scan Vivo         {END} {DIM}tabla en tiempo real{END}",
    ))
    print(_r2(
        "[12] MAC Spoof           cambiar direccion",
        f"{RED}[12]{END} {GREEN}MAC Spoof         {END} {DIM}cambiar direccion{END}",
        "[20] Dependencias        chequeo + instala",
        f"{RED}[20]{END} {CYAN}Dependencias      {END} {DIM}chequeo + instala{END}",
    ))
    print(_r2(
        "[29] Historial           ver ataques/claves",
        f"{RED}[29]{END} {CYAN}Historial         {END} {DIM}ver ataques/claves{END}",
        "[30] Reporte HTML        informe profesional",
        f"{RED}[30]{END} {CYAN}Reporte HTML      {END} {DIM}informe profesional{END}",
    ))

    # ─── SALIR ───────────────────────────────────────────────────────────────
    sv = " [0]  Salir"
    sc = f" {RED}[0]{END}  {RED}Salir{END}"
    print(_r1(sv, sc))

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
