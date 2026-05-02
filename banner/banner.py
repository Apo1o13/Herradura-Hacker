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
    # ── helper: fila de 2 columnas con anchos FIJOS y precisos ───────────────
    # BOX_W=62, INNER=60
    # Formato: │[sp][L_28chars][│][sp][R_28chars][sp]│
    #          1 + 1 + 28 + 1 + 1 + 28 + 1 = 61  → falta 1
    # Usamos: │[sp][L_28][│][sp][R_29]│  = 1+1+28+1+1+29+1 = 62  ✓
    L_W = 28   # ancho columna izquierda (visible, sin el espacio inicial)
    R_W = 29   # ancho columna derecha   (visible, sin el espacio inicial)

    def _r2(nL, nameL, colL, nR, nameR, colR):
        """
        nL/nR    : texto del número  ej. "[W]" "[35]" "[ 7]"
        nameL/R  : nombre de la opcion (string visible sin color)
        colL/R   : color ANSI para el número
        """
        m = _margin()
        visL = f"{nL} {nameL}"
        visR = f"{nR} {nameR}"
        padL = " " * max(0, L_W - len(visL))
        padR = " " * max(0, R_W - len(visR))
        cL = f"{colL}{nL}{END} {WHITE}{nameL}{END}"
        cR = f"{colR}{nR}{END} {WHITE}{nameR}{END}"
        return (f"{m}{CYAN}│{END} {cL}{padL}"
                f"{CYAN}│{END} {cR}{padR}{CYAN}│{END}")

    # ── cabecera ─────────────────────────────────────────────────────────────
    print(_top())

    # [W] fila completa (usa _row normal)
    wv = "[W]  MODO GUIADO COMPLETO  \u2192 ARSENAL TOTAL AUTOMATICO"
    wc = f"{GREEN}[W]{END}  {WHITE}MODO GUIADO COMPLETO{END}  {DIM}\u2192 ARSENAL TOTAL AUTOMATICO{END}"
    print(_row(wv, wc))

    # ── AUTOMATICOS ──────────────────────────────────────────────────────────
    print(_sep(title="AUTOMATICOS"))
    print(_r2("[31]", "Auto-Pwner",          RED,     "[33]", "Auditoria Express",   CYAN))
    print(_r2("[35]", "Exploit Engine AUTO",  GREEN,   "[36]", "Exploit Engine MASIVO", GREEN))

    # ── ATAQUES WiFi ─────────────────────────────────────────────────────────
    print(_sep(title="ATAQUES  WiFi"))
    print(_r2("[ 7]", "Handshake WPA/WPA2",  GREEN,   "[ 9]", "PMKID  (sin clientes)", YELLOW))
    print(_r2("[10]", "WPS Pixie / PIN",      GREEN,   "[15]", "Evil Twin + Portal",  RED))
    print(_r2("[21]", "KARMA / MANA",         RED,     "[23]", "WPA Enterprise",      MAGENTA))
    print(_r2("[25]", "WEP Full Attack",      GREEN,   "[17]", "Auto-Crack",          YELLOW))
    print(_r2("[13]", "Deautenticacion",      GREEN,   "[27]", "SSID Oculto Revealer",YELLOW))

    # ── AVANZADO / CVEs ──────────────────────────────────────────────────────
    print(_sep(title="AVANZADO  /  CVEs"))
    print(_r2("[32]", "Vulns Modernas 2025",  RED,     "[34]", "Suite CVE 2019-2024", MAGENTA))
    print(_r2("[28]", "Post-Explotacion",     RED,     "[26]", "Deauth Hopping",      GREEN))
    print(_r2("[22]", "Probe Harvester",      YELLOW,  "[24]", "Wordlist OSINT",      YELLOW))

    # ── HERRAMIENTAS ─────────────────────────────────────────────────────────
    print(_sep(title="HERRAMIENTAS"))
    print(_r2("[ 1]", "Monitor ON",           GREEN,   "[ 2]", "Monitor OFF",         GREEN))
    print(_r2("[ 5]", "Escanear + CSV",       GREEN,   "[ 6]", "Scan Vivo",           GREEN))
    print(_r2("[12]", "MAC Spoof",            GREEN,   "[20]", "Dependencias",        CYAN))
    print(_r2("[29]", "Historial",            CYAN,    "[30]", "Reporte HTML",        CYAN))

    # [0] fila completa
    print(_row("[0]  Salir", f"{RED}[0]{END}  {RED}Salir{END}"))

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
