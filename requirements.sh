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

    echo -e "\n${WHITE}─── DRIVERS ADAPTADORES WiFi ──────────────────${END}"
    # Prerequisitos para compilar drivers
    instalar dkms              "Dynamic Kernel Module Support"
    instalar build-essential   "compilador gcc/make"
    LOCAL_HEADERS="linux-headers-$(uname -r)"
    info "Instalando: ${WHITE}${LOCAL_HEADERS}${END}  ${DIM}headers del kernel actual${END}"
    if sudo apt-get install -y "$LOCAL_HEADERS" -qq 2>/dev/null; then
        ok "${LOCAL_HEADERS} instalado."
    else
        warn "Headers no disponibles. Puede que no se puedan compilar drivers."
    fi

    # Drivers para adaptadores comunes
    instalar firmware-atheros  "TP-Link TL-WN722N v1 / Alfa AWUS036NHA (AR9271)"
    instalar rfkill            "desbloquear adaptadores USB"

    # realtek-rtl88xxau-dkms: TP-Link TL-WN722N v2/v3, Alfa AWUS036ACH, T2U, T3U
    if apt-cache show realtek-rtl88xxau-dkms &>/dev/null; then
        instalar realtek-rtl88xxau-dkms "TP-Link TL-WN722N v2/v3, Alfa AWUS036ACH, Archer T2U"
    else
        warn "realtek-rtl88xxau-dkms no en repos. Instalando rtl8188eus desde GitHub..."
        if ! lsmod | grep -q 8188eu && ! lsmod | grep -q rtl8812au; then
            sudo git clone https://github.com/aircrack-ng/rtl8188eus /tmp/rtl8188eus 2>/dev/null
            if [ -d /tmp/rtl8188eus ]; then
                (cd /tmp/rtl8188eus && sudo make && sudo make install) 2>/dev/null && \
                    ok "rtl8188eus (TL-WN722N v2/v3) instalado." || \
                    warn "No se pudo compilar rtl8188eus. Inténtalo manualmente."
            fi
        else
            ok "Driver Realtek ya cargado en el sistema."
        fi
    fi

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
    info "Instalando módulos Python via apt (compatible Kali 2024+)..."
    instalar python3-colorama "colores en terminal (PEP668 safe)"
    instalar python3-scapy    "manipulación de paquetes de red"
    instalar python3-pip      "gestor de paquetes Python (opcional)"
    # Fallback pip con --break-system-packages solo si apt falla
    if ! python3 -c "import colorama" 2>/dev/null; then
        warn "colorama no encontrado via apt, intentando pip..."
        sudo pip3 install colorama --break-system-packages -q 2>/dev/null && ok "colorama (pip)" || \
        warn "Instala manualmente: sudo apt install python3-colorama"
    else
        ok "colorama disponible."
    fi

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
