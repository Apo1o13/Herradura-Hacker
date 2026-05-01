#!/bin/bash
# Herradura Hack v5.0 - Instalador de dependencias
# Creador: Apo1o13

RED='\e[1;31m'
GREEN='\e[1;32m'
YELLOW='\e[1;33m'
CYAN='\e[1;36m'
WHITE='\e[1;97m'
DIM='\e[2m'
END='\e[0m'

clear
echo -e "${WHITE}╔══════════════════════════════════════════╗${END}"
echo -e "${WHITE}║   Herradura Hack v5.0 — Dependencias     ║${END}"
echo -e "${WHITE}║   Creador: Apo1o13                       ║${END}"
echo -e "${WHITE}╚══════════════════════════════════════════╝${END}"
echo ""

ok()   { echo -e " ${GREEN}[✔]${END} $1"; }
warn() { echo -e " ${YELLOW}[!]${END} $1"; }
info() { echo -e " ${CYAN}[*]${END} $1"; }

instalar() {
    local pkg="$1"
    local desc="$2"
    info "Instalando: ${WHITE}${pkg}${END}  ${DIM}${desc}${END}"
    if sudo apt-get install -y "$pkg" -qq 2>/dev/null; then
        ok "${pkg} instalado."
    else
        warn "${pkg} no disponible en repositorios. Ver nota al final."
    fi
}

dependencias() {

    info "Actualizando repositorios..."
    sudo apt-get update -qq

    echo -e "\n${WHITE}─── NÚCLEO WiFi ───────────────────────────────${END}"
    instalar aircrack-ng     "airmon, airodump, aireplay, aircrack"
    instalar wireless-tools  "iwconfig, iwlist"
    instalar iw              "gestión de interfaces"
    instalar xterm           "ventanas terminales auxiliares"

    echo -e "\n${WHITE}─── ATAQUES WPS ───────────────────────────────${END}"
    instalar reaver          "WPS brute force + Pixie Dust"
    instalar bully           "WPS brute force alternativo"

    echo -e "\n${WHITE}─── PMKID / HASHCAT ───────────────────────────${END}"
    instalar hcxdumptool     "captura PMKID sin clientes"
    instalar hcxtools        "conversión pcapng → hc22000"
    instalar hashcat         "crackeo GPU WPA/WPA2/PMKID"

    echo -e "\n${WHITE}─── AP FALSO / KARMA / ENTERPRISE ────────────${END}"
    instalar hostapd         "Evil Twin + KARMA AP"
    instalar dnsmasq         "DHCP + DNS para APs falsos"
    instalar mdk4            "Fake AP beacon flood / probe response"

    echo -e "\n${WHITE}─── POST-EXPLOTACIÓN ──────────────────────────${END}"
    instalar nmap            "escaneo de puertos + scripts vuln"
    instalar arp-scan        "descubrimiento de dispositivos en LAN"
    instalar tshark          "análisis de capturas / probe harvester"

    echo -e "\n${WHITE}─── ENTERPRISE / MSCHAPv2 ─────────────────────${END}"
    instalar asleap          "crackeo MSCHAPv2 WPA Enterprise"

    # hostapd-wpe (Kali/Parrot tienen paquete, otros distros requieren compilar)
    if apt-cache show hostapd-wpe &>/dev/null; then
        instalar hostapd-wpe "servidor RADIUS falso para WPA Enterprise"
    else
        warn "hostapd-wpe no disponible por apt."
        warn "En Kali: sudo apt install hostapd-wpe"
        warn "Manual:  https://github.com/OpenSecurityResearch/hostapd-wpe"
    fi

    echo -e "\n${WHITE}─── PYTHON ────────────────────────────────────${END}"
    info "Instalando módulos Python..."
    sudo pip3 install colorama -q && ok "colorama"

    echo -e "\n${WHITE}─── WORDLISTS ─────────────────────────────────${END}"
    if apt-cache show wordlists &>/dev/null; then
        instalar wordlists "rockyou.txt y otros diccionarios"
        # Descomprimir rockyou si está comprimido
        if [ -f /usr/share/wordlists/rockyou.txt.gz ]; then
            info "Descomprimiendo rockyou.txt..."
            sudo gunzip /usr/share/wordlists/rockyou.txt.gz 2>/dev/null
            ok "rockyou.txt listo en /usr/share/wordlists/"
        fi
    else
        warn "Instale manualmente: sudo apt install wordlists"
    fi

    echo -e "\n${YELLOW}[+] Vulnerabilidades modernas (FragAttacks/KRACK)${END}"
    warn "dragonslayer/fragattacks requieren compilación manual:"
    warn "  git clone https://github.com/vanhoefm/dragonslayer"
    warn "  git clone https://github.com/vanhoefm/fragattacks"

    echo ""
    echo -e "${WHITE}╔══════════════════════════════════════════╗${END}"
    echo -e "${WHITE}║  ✔ Instalación completada                ║${END}"
    echo -e "${WHITE}║                                          ║${END}"
    echo -e "${WHITE}║  Ejecute:                                ║${END}"
    echo -e "${WHITE}║  sudo python3 herradura.py               ║${END}"
    echo -e "${WHITE}╚══════════════════════════════════════════╝${END}"
    echo ""
}

dependencias
