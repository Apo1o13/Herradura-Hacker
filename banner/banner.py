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

# ── ASCII Art ─────────────────────────────────────────────────────────────────
_LOGO = [
    r"  (((  (((  (((  WiFi  )))  )))  )))",
    r"   \\   __ _____  _______  ___  ",
    r"    \\ /  |  ___||  ___  ||   \ ",
    r"     \\|  | |__  | |___| ||    |",
    r"     /\|  |  __| |  ___  ||    |",
    r"    // \  | |___ | |   | ||___/ ",
    r"   //   \_|_____||_|   |_||_|   ",
    r"  ///  HERRADURA HACK  v5.0  \\\ ",
]

_SIGNAL = [
    r"    )  )  )  )))  (  (  (    ",
    r"   )  ) ╔═══════════╗ (  (   ",
    r"  )  ) ╔╣ ▓▓▓▓░░░░░ ╠╗ (  ( ",
    r"  )  ) ║╚╦═══════════╦╝║ (  (",
    r"  )  ) ║ ║  [ARMED]  ║ ║ (  (",
    r"  )  ) ║╔╩═══════════╩╗║ (  (",
    r"  )  ) ╚╣ TARGET LOCK ╠╝ (  (",
    r"   )  ) ╚═════════════╝ (  ) ",
    r"    )  )  )  )))  (  (  (    ",
]

def banner():
    os.system("clear")
    tw = _tw()

    # ── Logo central ─────────────────────────────────────────────────────────
    now = datetime.datetime.now().strftime("%Y-%m-%d  %H:%M:%S")

    # Elige logo según ancho de terminal
    if tw >= 100:
        art = _SIGNAL
        art_colors = [
            DIM, RED, RED, RED, f"{GREEN}", f"{RED}", f"{GREEN}", DIM, DIM
        ]
    else:
        art = _LOGO
        art_colors = [
            DIM, GREEN, GREEN, GREEN, GREEN, GREEN, GREEN, RED
        ]

    print()
    for line, col in zip(art, art_colors):
        pad = " " * max(0, (tw - len(line)) // 2)
        print(f"{col}{pad}{line}{END}")
    print()

    # ── Título estilo "terminal breach" ──────────────────────────────────────
    breach_art = [
        f"  {DIM}╔{'─'*20}╗                    ╔{'─'*20}╗{END}",
        f"  {DIM}│{END}{RED}  0x48 0x41 0x43 0x4B{END}  {DIM}│                    │{END}{GREEN}  WiFi  Pentest Suite {END}{DIM}│{END}",
        f"  {DIM}╚{'─'*20}╝                    ╚{'─'*20}╝{END}",
    ]
    for line in breach_art:
        pad = " " * max(0, (tw - 58) // 2)
        print(f"{pad}{line}")
    print()

    # ── Líneas de título ──────────────────────────────────────────────────────
    def _cline(text_vis, text_col):
        pad = " " * max(0, (tw - len(text_vis)) // 2)
        print(f"{pad}{text_col}")

    _cline(
        "[ HERRADURA HACK ]──────────────────────[ v5.0 ]",
        f"{DIM}[{END} {RED}HERRADURA{END} {WHITE}HACK{END} {DIM}]{'─'*22}[{END} {GREEN}v5.0{END} {DIM}]{END}"
    )
    _cline(
        "[ by Apo1o13 ]────────────────────────[ KALI LINUX ]",
        f"{DIM}[{END} {CYAN}by Apo1o13{END} {DIM}]{'─'*22}[{END} {YELLOW}KALI LINUX{END} {DIM}]{END}"
    )
    _cline(
        f"[ {now} ]──────────────────[ USE ONLY ON AUTHORIZED TARGETS ]",
        f"{DIM}[{END} {DIM}{now}{END} {DIM}]{'─'*6}[{END} {DIM}USE ONLY ON AUTHORIZED TARGETS{END} {DIM}]{END}"
    )
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
