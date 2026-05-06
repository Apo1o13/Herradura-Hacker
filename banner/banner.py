#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Herradura Hack v5.0 — banner.py
# Creador: Apo1o13

import os
import shutil
import datetime

# ── Colores ───────────────────────────────────────────────────────────────────
RED     = '\033[1;31m'
GREEN   = '\033[1;32m'
YELLOW  = '\033[1;33m'
CYAN    = '\033[1;36m'
WHITE   = '\033[1;37m'
MAGENTA = '\033[1;35m'
BLUE    = '\033[1;34m'
DIM     = '\033[2m'
BLINK   = '\033[5m'
END     = '\033[0m'

# ── Helpers de layout ─────────────────────────────────────────────────────────
BOX_W  = 62
INNER  = BOX_W - 1

def _tw():
    return max(shutil.get_terminal_size((80, 24)).columns, 80)

def _margin():
    return " " * max(0, (_tw() - (BOX_W + 2)) // 2)

def _row(content_visible, content_with_color):
    pad = INNER - len(content_visible)
    m = _margin()
    return f"{m}{GREEN}│{END} {content_with_color}{' ' * max(0, pad)}{GREEN}│{END}"

def _sep(char="─", title=""):
    m = _margin()
    if title:
        tv  = len(f" {title} ")
        pad = BOX_W - tv
        l   = char * (pad // 2)
        r   = char * (pad - pad // 2)
        return f"{m}{GREEN}├{DIM}{l}{END} {WHITE}{title}{END} {DIM}{r}{END}{GREEN}┤{END}"
    return f"{m}{GREEN}├{DIM}{'─' * BOX_W}{END}{GREEN}┤{END}"

def _top():
    m = _margin()
    return f"{m}{GREEN}╔{DIM}{'═' * BOX_W}{END}{GREEN}╗{END}"

def _bot():
    m = _margin()
    return f"{m}{GREEN}╚{DIM}{'═' * BOX_W}{END}{GREEN}╝{END}"

def _double_sep(title=""):
    m = _margin()
    if title:
        tv  = len(f" {title} ")
        pad = BOX_W - tv
        l   = '═' * (pad // 2)
        r   = '═' * (pad - pad // 2)
        return f"{m}{GREEN}╠{l} {RED}{title}{GREEN} {r}╣{END}"
    return f"{m}{GREEN}╠{'═' * BOX_W}╣{END}"

# ── Logo herradura (braille art) ─────────────────────────────────────────────
_LOGO_LINES = [
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
# Ancho visual del logo (cada char braille ocupa 1 col)
_LOGO_W = 22

def banner():
    os.system("clear")
    tw = _tw()
    now = datetime.datetime.now().strftime("%Y-%m-%d  %H:%M:%S")

    # ── Logo herradura centrado ───────────────────────────────────────────────
    logo_pad = " " * max(0, (tw - _LOGO_W) // 2)
    print()
    for line in _LOGO_LINES:
        print(f"{GREEN}{logo_pad}{line}{END}")
    print()

    # ── Barra de info tipo terminal ───────────────────────────────────────────
    bar_w = min(tw - 4, 72)           # ancho total incluyendo bordes │...│
    inner = bar_w - 2                 # contenido visible entre │ y │
    pad_b = " " * max(0, (tw - bar_w) // 2)

    def _bar_line(left_vis, left_col, right_vis, right_col, fill="─"):
        """Construye una fila de barra con relleno exacto."""
        gap = inner - 2 - len(left_vis) - len(right_vis)  # 2 = leading spaces
        dashes = fill * max(1, gap)
        return f"{DIM}│{END}  {left_col}{DIM}{dashes}{END}{right_col}{DIM}│{END}"

    bar_top  = f"{DIM}┌{'─'*inner}┐{END}"
    bar_bot  = f"{DIM}└{'─'*inner}┘{END}"

    line1_lv = "[root@herradura]─[WiFi Pentest Suite]"
    line1_lc = f"{RED}[root@herradura]{END}{DIM}─{END}{GREEN}[WiFi Pentest Suite]{END}"
    line1_rv = "[Apo1o13]"
    line1_rc = f"{DIM}[{END}{YELLOW}Apo1o13{END}{DIM}]{END}"

    line2_lv = "└──╼ sudo python3 herradura.py"
    line2_lc = f"{DIM}└──╼{END} {CYAN}sudo python3 herradura.py{END}"
    line2_rv = "[v5.0]"
    line2_rc = f"{DIM}[{END}{GREEN}v5.0{END}{DIM}]{END}"

    line3_lv = "[✔] TARGET ACQUIRED"
    line3_lc = f"{GREEN}[✔]{END} {WHITE}TARGET ACQUIRED{END}"
    line3_rv = f"[{now}]"
    line3_rc = f"{DIM}[{END}{DIM}{now}{END}{DIM}]{END}"

    for line in [bar_top,
                 _bar_line(line1_lv, line1_lc, line1_rv, line1_rc),
                 _bar_line(line2_lv, line2_lc, line2_rv, line2_rc),
                 _bar_line(line3_lv, line3_lc, line3_rv, line3_rc),
                 bar_bot]:
        print(f"{pad_b}{line}")
    print()


def menu():
    L_W = 29
    R_W = 30

    def _r2(nL, nameL, colL, nR, nameR, colR):
        m    = _margin()
        visL = f"{nL} {nameL}"
        visR = f"{nR} {nameR}"
        padL = " " * max(0, L_W - len(visL))
        padR = " " * max(0, R_W - len(visR))
        cL   = f"{colL}{nL}{END} {WHITE}{nameL}{END}"
        cR   = f"{colR}{nR}{END} {WHITE}{nameR}{END}"
        return (f"{m}{GREEN}│{END} {cL}{padL}"
                f"{GREEN}│{END} {cR}{padR}{GREEN}│{END}")

    # ── Cabecera ──────────────────────────────────────────────────────────────
    print(_top())
    wv = "[W]  ▶  MODO GUIADO COMPLETO  ──  ARSENAL TOTAL AUTOMATICO"
    wc = (f"{GREEN}[W]{END}  {RED}▶{END}  {WHITE}MODO GUIADO COMPLETO{END}"
          f"  {DIM}──  ARSENAL TOTAL AUTOMATICO{END}")
    print(_row(wv, wc))

    # ── AUTOMÁTICOS ───────────────────────────────────────────────────────────
    print(_double_sep(title="◈  AUTOMATICOS  ◈"))
    print(_r2("[31]", "Auto-Pwner",           RED,     "[33]", "Auditoria Express",       CYAN))
    print(_r2("[35]", "Exploit Engine AUTO",  GREEN,   "[36]", "Exploit Engine MASIVO",   GREEN))

    # ── ATAQUES WiFi ──────────────────────────────────────────────────────────
    print(_double_sep(title="◈  ATAQUES  WiFi  ◈"))
    print(_r2("[ 7]", "Handshake WPA/WPA2",   GREEN,   "[ 9]", "PMKID  (sin clientes)",   YELLOW))
    print(_r2("[10]", "WPS Pixie / PIN",       GREEN,   "[15]", "Evil Twin + Portal",      RED))
    print(_r2("[21]", "KARMA / MANA",          RED,     "[23]", "WPA Enterprise",          MAGENTA))
    print(_r2("[25]", "WEP Full Attack",       GREEN,   "[17]", "Auto-Crack",              YELLOW))
    print(_r2("[13]", "Deautenticacion",       GREEN,   "[27]", "SSID Oculto Revealer",    YELLOW))

    # ── AVANZADO / CVEs ───────────────────────────────────────────────────────
    print(_double_sep(title="◈  AVANZADO  /  CVEs  ◈"))
    print(_r2("[32]", "Vulns Modernas 2025",   RED,     "[34]", "Suite CVE 2019-2024",     MAGENTA))
    print(_r2("[28]", "Post-Explotacion",      RED,     "[26]", "Deauth Hopping",          GREEN))
    print(_r2("[22]", "Probe Harvester",       YELLOW,  "[24]", "Wordlist OSINT",          YELLOW))

    # ── HERRAMIENTAS ──────────────────────────────────────────────────────────
    print(_double_sep(title="◈  HERRAMIENTAS  ◈"))
    print(_r2("[ 1]", "Monitor ON",            GREEN,   "[ 2]", "Monitor OFF",             GREEN))
    print(_r2("[ 5]", "Escanear + CSV",        GREEN,   "[ 6]", "Scan Vivo",               GREEN))
    print(_r2("[12]", "MAC Spoof",             GREEN,   "[20]", "Dependencias",            CYAN))
    print(_r2("[29]", "Historial",             CYAN,    "[30]", "Reporte HTML",            CYAN))

    # ── Salir ─────────────────────────────────────────────────────────────────
    print(_sep())
    sv = "[0]  ■  SALIR"
    sc = f"{RED}[0]{END}  {DIM}■{END}  {RED}SALIR{END}"
    print(_row(sv, sc))
    print(_bot())
    print()


def goodbye():
    tw = _tw()

    skull = [
        "        .------.",
        "       /  o  o  \\",
        "      |    __    |",
        "      |  /    \\  |",
        "       \\ \\____/ /",
        "    ____\\______/____",
        "   /  HERRADURA HACK \\",
        "  /____________________\\",
        "   |  ||  ||  ||  ||  |",
        "   |__|__|__|__|__|__|",
    ]

    print()
    for line in skull:
        pad = " " * max(0, (tw - len(line)) // 2)
        print(f"{RED}{pad}{line}{END}")
    print()

    msg1 = "~ Cerrando sesión — Hasta la próxima ~"
    msg2 = "Herradura Hack v5.0  ·  by Apo1o13  ·  Use responsibly"
    p1 = " " * max(0, (tw - len(msg1)) // 2)
    p2 = " " * max(0, (tw - len(msg2)) // 2)
    print(f"{p1}{WHITE}{msg1}{END}")
    print(f"{p2}{DIM}{msg2}{END}")
    print()


if __name__ == "__main__":
    banner()
    menu()
