# Herradura Hack v5.0 — WiFi Pentesting Tool

**Creador: Apo1o13**

> Uso exclusivo para pruebas de penetración autorizadas y fines educativos.
> El autor no se hace responsable del uso indebido de esta herramienta.

```
sudo bash requirements.sh
sudo python3 herradura.py
```

## Tested On
- Kali Linux 2024+
- Parrot OS 6+
- Ubuntu 22.04 / Linux Mint 21+

---

## Módulos

### Interfaz
| Opción | Función |
|--------|---------|
| 1 | Iniciar modo monitor |
| 2 | Detener modo monitor |
| 3 | Ver interfaces WiFi |
| 4 | Reiniciar red |

### Escaneo
| Opción | Función |
|--------|---------|
| 5 | Escanear y guardar CSV |
| 6 | Escaneo en vivo (tabla visual) |
| 11 | Escanear redes con WPS habilitado |
| 16 | Vendor/OUI Lookup (fabricante por MAC) |
| 22 | Probe Request Harvester |

### Ataques WiFi
| Opción | Función |
|--------|---------|
| 7 | Capturar Handshake WPA/WPA2 |
| 8 | Descifrar clave (aircrack-ng / hashcat GPU + reglas) |
| 9 | Ataque PMKID sin clientes (hcxdumptool) |
| 10 | Ataque WPS: Bully / Reaver / Pixie Dust |
| 13 | Deautenticación |
| 15 | Evil Twin + Portal Cautivo |
| 17 | Auto-Crack (captura + crackeo automático) |
| 18 | Multi-Deauth desde CSV |
| 21 | KARMA/MANA Attack |
| 23 | WPA Enterprise Attack (hostapd-wpe + MSCHAPv2) |
| 25 | WEP Full Attack (ARP replay → aircrack) |
| 26 | Deauth Channel Hopping (todos los canales) |
| 27 | Hidden SSID Revealer |

### Post-Explotación
| Opción | Función |
|--------|---------|
| 28 | Escaneo de dispositivos + vulnerabilidades LAN |

### Automáticos / Inteligentes
| Opción | Función |
|--------|---------|
| 31 | AUTO-PWNER — ataque total con scoring |
| 32 | Vulnerabilidades Modernas 2023-2025 |
| 33 | Auditoría Express + auto-exploit opcional |
| 34 | Suite CVE 2019-2024 (Kr00k / FragAttacks / EAP / Dragonblood) |
| **35** | **Exploit Engine — auto-exploit con progreso % tiempo real** |
| **36** | **Exploit Engine MASIVO — varias redes en secuencia** |

### Utilidades
| Opción | Función |
|--------|---------|
| 12 | Falsificar MAC |
| 14 | Fake AP (beacon flood mdk4) |
| 19 | Convertir .cap → hc22000 |
| 20 | Chequeo de dependencias |
| 24 | OSINT Wordlist Generator |
| 29 | Historial de capturas (SQLite) |
| 30 | Reporte HTML profesional |

---

## Exploit Engine (opciones 35 / 36)

El motor de explotación ejecuta una cadena de ataques en orden de efectividad
mostrando porcentaje de progreso en tiempo real:

```
[EXPLOIT ENGINE] [████████████░░░░░░░░░░░░░░░░░░░░░░]  38%  PMKID capture… 62%
```

**Fases:**
1. Fingerprint + detección CVE (Kr00k, WPS, chipset Broadcom/Cypress)
2. WPS Pixie Dust (si aplica)
3. WPS Smart PIN — top 30 PINs estadísticos
4. PMKID capture + hashcat multi-regla
5. Handshake + deauth agresivo (3 rondas: 10/30/50 paquetes)
6. Cracking: SSID wordlist + best64 + rockyou + aircrack fallback

---

## CVE Implementados

| CVE | Vulnerabilidad | Módulo |
|-----|---------------|--------|
| CVE-2019-15126 | Kr00k — Broadcom/Cypress null-key decrypt | 34/35 |
| CVE-2020-24586/87/88 | FragAttacks — frame injection WPA/2/3 | 34 |
| CVE-2023-52160 | EAP Downgrade WPA2-Enterprise | 34 |
| CVE-2023-52424 | SSID Confusion + WPA3→WPA2 downgrade | 34 |
| CVE-2019-9494/9496 | Dragonblood WPA3-SAE | 32/34 |
| CVE-2024-30078 | Windows WiFi RCE — detección pasiva | 34 |
| CVE-2024-21820/21821 | Intel AX drivers — detección por OUI | 34 |

---

## Dependencias

```
aircrack-ng  hashcat      hcxdumptool  hcxtools   reaver   bully
mdk4         hostapd      hostapd-wpe  dnsmasq    xterm    iw
wireless-tools  nmap      arp-scan     tshark     asleap   wash
python3-colorama  scapy (opcional)
```

Instalar todo:
```bash
sudo bash requirements.sh
```
