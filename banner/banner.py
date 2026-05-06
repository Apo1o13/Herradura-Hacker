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
    tw  = _tw()
    BW  = max(70, min(tw - 6, 96))   # ancho dinámico según terminal
    inn = BW - 1
    m   = " " * max(0, (tw - (BW + 2)) // 2)

    # Ancho de cada columna (la caja interna se divide en 2)
    L_W = (BW - 1) // 2
    R_W = BW - 1 - L_W

    # ── Helpers locales ───────────────────────────────────────────────────────
    def top():
        return f"{m}{GREEN}╔{'═' * inn}╗{END}"

    def bot():
        return f"{m}{GREEN}╚{'═' * inn}╝{END}"

    def sep():
        return f"{m}{GREEN}├{DIM}{'─' * inn}{END}{GREEN}┤{END}"

    def dsep(title=""):
        tv  = len(f" {title} ")
        pad = inn - tv
        l   = '═' * (pad // 2)
        r   = '═' * (pad - pad // 2)
        return f"{m}{GREEN}╠{DIM}{l}{END} {RED}{title}{GREEN} {DIM}{r}{END}{GREEN}╣{END}"

    def full_row(vis, col):
        """Fila que ocupa todo el ancho (sin columna derecha)."""
        pad = inn - len(vis)
        return f"{m}{GREEN}│{END} {col}{' ' * max(0, pad)}{GREEN}│{END}"

    def row2(nL, nameL, descL, colL, nR, nameR, descR, colR):
        """Fila de dos columnas con número, nombre y descripción corta."""
        visL = f"{nL} {nameL}  {descL}"
        visR = f"{nR} {nameR}  {descR}"
        padL = " " * max(0, L_W - len(visL))
        padR = " " * max(0, R_W - len(visR))
        cL   = (f"{colL}{nL}{END} {WHITE}{nameL}{END}"
                f"  {DIM}{descL}{END}")
        cR   = (f"{colR}{nR}{END} {WHITE}{nameR}{END}"
                f"  {DIM}{descR}{END}")
        return f"{m}{GREEN}│{END} {cL}{padL}{GREEN}│{END} {cR}{padR}{GREEN}│{END}"

    # ── Cabecera ──────────────────────────────────────────────────────────────
    print(top())
    wv = "[W]  ▶  MODO GUIADO  ──  escanea, elige objetivo y ataca todo solo"
    wc = (f"{GREEN}[W]{END}  {RED}▶{END}  {WHITE}MODO GUIADO{END}"
          f"  {DIM}──  escanea, elige objetivo y ataca todo solo{END}")
    print(full_row(wv, wc))

    # ── AUTOMÁTICOS ───────────────────────────────────────────────────────────
    print(dsep("◈  AUTOMATICOS  ◈"))
    print(row2("[31]", "Auto-Pwner",           "escanea y ataca solo",      RED,
               "[33]", "Auditoria Express",    "analiza sin atacar",        CYAN))
    print(row2("[35]", "Exploit Engine AUTO",  "todos los vectores",        GREEN,
               "[36]", "Exploit Engine MASIVO","multiples redes",           GREEN))

    # ── ATAQUES WiFi ──────────────────────────────────────────────────────────
    print(dsep("◈  ATAQUES  WiFi  ◈"))
    print(row2("[ 7]", "Handshake WPA/WPA2",  "captura + crackea clave",   GREEN,
               "[ 9]", "PMKID",               "sin esperar clientes",      YELLOW))
    print(row2("[10]", "WPS Pixie / PIN",      "explota WPS del router",    GREEN,
               "[15]", "Evil Twin + Portal",   "red falsa + pagina login",  RED))
    print(row2("[21]", "KARMA / MANA",         "acepta cualquier probe",    RED,
               "[23]", "WPA Enterprise",       "captura hash MSCHAPv2",     MAGENTA))
    print(row2("[25]", "WEP Full Attack",      "ARP replay + crack",        GREEN,
               "[17]", "Auto-Crack",           "flujo completo automatico", YELLOW))
    print(row2("[13]", "Deautenticacion",      "desconecta clientes",       GREEN,
               "[27]", "SSID Oculto Revealer", "revela SSIDs escondidos",   YELLOW))

    # ── AVANZADO / CVEs ───────────────────────────────────────────────────────
    print(dsep("◈  AVANZADO  /  CVEs  ◈"))
    print(row2("[32]", "Vulns Modernas 2025",  "KRACK, Frag, Dragonblood", RED,
               "[34]", "Suite CVE 2019-2024",  "Kr00k, EAP, FragAttacks",  MAGENTA))
    print(row2("[28]", "Post-Explotacion",     "escanea la LAN interna",   RED,
               "[26]", "Deauth Hopping",       "deauth multi-canal",        GREEN))
    print(row2("[22]", "Probe Harvester",      "ve que redes buscan devs", YELLOW,
               "[24]", "Wordlist OSINT",       "diccionario por SSID",     YELLOW))

    # ── HERRAMIENTAS ──────────────────────────────────────────────────────────
    print(dsep("◈  HERRAMIENTAS  ◈"))
    print(row2("[ 1]", "Monitor ON",           "activa modo monitor",       GREEN,
               "[ 2]", "Monitor OFF",          "vuelve a managed",          GREEN))
    print(row2("[ 5]", "Escanear + CSV",       "escanea y guarda CSV",      GREEN,
               "[ 6]", "Scan Vivo",            "tabla en tiempo real",      GREEN))
    print(row2("[12]", "MAC Spoof",            "cambia tu MAC",             GREEN,
               "[20]", "Dependencias",         "verifica herramientas",     CYAN))
    print(row2("[29]", "Historial",            "claves y ataques guardados",CYAN,
               "[30]", "Reporte HTML",         "informe profesional",       CYAN))

    # ── Salir ─────────────────────────────────────────────────────────────────
    print(sep())
    sv = "[0]  ■  SALIR"
    sc = f"{RED}[0]{END}  {DIM}■{END}  {RED}SALIR{END}"
    print(full_row(sv, sc))
    print(bot())
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
