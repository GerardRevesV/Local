#!/usr/bin/env bash
#
# prepara-host.sh — deixa el portàtil del local llest per fer de servidor.
# Fase A.2 de docs/domotica/fases.md · decisions a docs/domotica/decisio-stack.md
#
# Això és el guió que estalvia escriure vint ordres a mà al portàtil.
# És idempotent: es pot tornar a executar sense trencar res.
#
#   bash scripts/prepara-host.sh
#
# El que fa:
#   1. Servidor SSH        → a partir d'aquí ja no cal tocar el teclat del portàtil
#   2. Zona horària i NTP  → sense rellotge fiable, les sèries de dades no valen
#   3. Ni suspensió ni tapa→ un servidor que dorm és un forat a l'històric
#   4. Docker CE oficial   → el de Mint va endarrerit; el de snap trenca els volums
#   5. Límit als logs      → que el journal no s'empassi el disc
#   6. Bluetooth fora      → HA hi insisteix i omple el log d'excepcions
#   7. unattended-upgrades → només seguretat, mai Docker, a les 04:30
#   8. Tailscale           → l'única via d'entrar-hi quan marxis del local
#   9. vm.swappiness=10    → el disc és NVMe i la RAM és poca: val més no moure-la
#
# El que NO fa, i queda per a tu:
#   · Desactivar l'expiració de la clau de Tailscale, que es fa al seu web (A.3).
#     Si no ho fas, d'aquí a uns mesos la clau caduca i perds l'accés al servidor.
#   · DESACTIVAR (no esborrar: es tornaria a crear) l'entrada «Bluetooth» d'HA.
#     Fet el 21/09/2026; cal refer-ho si mai canvia l'adaptador. → runbook.
#
# Ja resolt i per tant fora del guió:
#   · zram — el disc va resultar ser un SSD NVMe, no una eMMC

set -euo pipefail

log()  { printf '\n\033[1;34m▶ %s\033[0m\n' "$*"; }
ok()   { printf '  \033[32m✓\033[0m %s\n' "$*"; }
avis() { printf '  \033[33m⚠\033[0m %s\n' "$*"; }

if [[ $EUID -eq 0 ]]; then
  echo "No l'executis com a root: necessito saber quin és el teu usuari." >&2
  echo "Executa'l com tu mateix; ja demanarà sudo quan calgui." >&2
  exit 1
fi

sudo -v

# ─────────────────────────────────────────────────────────────── 1. SSH ──────
log "Servidor SSH"
sudo apt-get update -qq
sudo apt-get install -y -qq openssh-server git curl ca-certificates \
     vnstat smartmontools sqlite3 jq
sudo systemctl enable --now ssh
ok "SSH actiu. A partir d'ara pots entrar-hi des de casa i deixar de teclejar aquí."
sudo systemctl enable --now vnstat >/dev/null 2>&1 || true
# vnstat compta les dades que gasta la SIM, per dia i per mes. El comptador del
# router es perd a cada reinici; aquest no. S'instal·la ARA, per fibra: després
# de passar a la SIM, cada «apt install» es paga amb dades del pla.
ok "Eines de diagnòstic: vnstat (dades de la SIM), smartmontools (SMART), sqlite3, jq."

# ───────────────────────────────────────────────────────── 2. Rellotge ───────
log "Zona horària i sincronització de rellotge"
sudo timedatectl set-timezone Europe/Madrid
sudo timedatectl set-ntp true
# Si la pila del CMOS està morta, el rellotge arrenca el 2015 i HA gravaria
# un bloc de files amb data falsa al mig de la sèrie. Això ho impedeix.
sudo systemctl enable systemd-time-wait-sync.service 2>/dev/null \
  || avis "systemd-time-wait-sync no existeix en aquesta versió; revisa-ho a mà"
ok "$(timedatectl show -p Timezone --value) · NTP=$(timedatectl show -p NTPSynchronized --value)"

# ──────────────────────────────────────────────── 3. Res de dormir ──────────
log "Desactivar suspensió, hibernació i l'interruptor de la tapa"
sudo systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target

sudo mkdir -p /etc/systemd/logind.conf.d
sudo tee /etc/systemd/logind.conf.d/99-servidor.conf >/dev/null <<'CONF'
# El portàtil viu tancat i endollat: tancar la tapa no ha de fer res.
[Login]
HandleLidSwitch=ignore
HandleLidSwitchDocked=ignore
HandleLidSwitchExternalPower=ignore
IdleAction=ignore
CONF
sudo systemctl restart systemd-logind
ok "La tapa ja no suspèn res."
avis "L'estalvi d'energia de l'escriptori va a part: Configuració → Energia,"
avis "posa-ho tot a «Mai». systemd no mana sobre això."

# ────────────────────────────────────────────────────────── 4. Docker ────────
log "Docker CE del repositori oficial"
if ! command -v docker >/dev/null 2>&1; then
  sudo install -m 0755 -d /etc/apt/keyrings
  sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
       -o /etc/apt/keyrings/docker.asc
  sudo chmod a+r /etc/apt/keyrings/docker.asc

  # Linux Mint no és Ubuntu, però el repositori de Docker vol el nom
  # d'Ubuntu. UBUNTU_CODENAME el treu del propi sistema: és el pas que
  # falla a tothom qui copia la recepta d'Ubuntu tal qual.
  . /etc/os-release
  : "${UBUNTU_CODENAME:?No trobo UBUNTU_CODENAME a /etc/os-release}"
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu ${UBUNTU_CODENAME} stable" \
    | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null

  sudo apt-get update -qq
  sudo apt-get install -y -qq docker-ce docker-ce-cli containerd.io \
       docker-buildx-plugin docker-compose-plugin
else
  ok "Docker ja hi era"
fi

sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"
ok "$(docker --version)"

# ──────────────────────────────────────────────────────────── 5. Logs ────────
log "Posar sostre als logs del sistema"
sudo mkdir -p /etc/systemd/journald.conf.d
sudo tee /etc/systemd/journald.conf.d/99-mida.conf >/dev/null <<'CONF'
[Journal]
SystemMaxUse=200M
SystemMaxFileSize=20M
CONF
sudo systemctl restart systemd-journald
ok "Journal limitat a 200 MB."

# ──────────────────────────────────────── 6. Bluetooth fora ─────────────────
log "Apagar el Bluetooth"
# Aquest portàtil fa de servidor i els sensors parlen per 868 MHz amb el hub.
# El Bluetooth no s'usa per res, i en canvi HA hi insisteix i omple el log
# d'errors perquè el contenidor no té NET_ADMIN/NET_RAW. Donar-li aquestes
# capacitats seria regalar privilegis per una funció que no volem: més val
# treure l'adaptador de l'equació.
if systemctl list-unit-files bluetooth.service >/dev/null 2>&1; then
  sudo systemctl disable --now bluetooth 2>/dev/null || true
  ok "Bluetooth aturat i desactivat a l'arrencada"
else
  ok "No hi ha servei de Bluetooth"
fi

# ⚠️ Aturar el servei NO n'hi ha prou: el 20/09/2026, amb bluetooth.service
# desactivat, el contenidor seguia veient l'adaptador «hci0» i deixava una
# excepció de bleak a cada arrencada. El que el fa desaparèixer de debò és
# treure'n el mòdul del nucli.
sudo tee /etc/modprobe.d/99-sense-bluetooth.conf >/dev/null <<'CONF'
# Aquest portàtil fa de servidor i el Bluetooth no s'usa: els sensors parlen
# per 868 MHz amb el hub. Sense això, Home Assistant hi insisteix i omple el log.
blacklist btusb
blacklist bluetooth
CONF
ok "Mòdul de Bluetooth a la llista negra (efectiu al proper reinici)."
avis "A Home Assistant, DESACTIVA (no esborris) l'entrada «Bluetooth»: esborrada, HA"
avis "redescobreix l'adaptador i la torna a crear. Vegeu el runbook."

# ──────────────────────── 7. Actualitzacions: només seguretat ───────────────
log "unattended-upgrades — només seguretat, i mai Docker"
sudo apt-get install -y -qq unattended-upgrades
. /etc/os-release
sudo tee /etc/apt/apt.conf.d/52-local-ha >/dev/null <<CONF
// Només seguretat. La resta d'actualitzacions es fan a mà i quan convingui:
// una actualització no planificada és un forat a l'històric.
//
// ⚠️ «#clear» no és un comentari: és la directiva d'apt que BUIDA la llista.
// Sense ella, aquest bloc no substitueix el de 50unattended-upgrades sinó que
// s'hi SUMA, i hi queda «\${distro_id}:\${distro_codename}» — que a Mint és el
// seu propi dipòsit sencer, no pas seguretat. Verificat el 20/09/2026.
#clear Unattended-Upgrade::Allowed-Origins;
Unattended-Upgrade::Allowed-Origins {
        "Ubuntu:${UBUNTU_CODENAME}-security";
};
// Docker mai automàticament: reiniciar el dimoni reinicia Home Assistant.
Unattended-Upgrade::Package-Blacklist {
        "docker-ce";
        "docker-ce-cli";
        "containerd.io";
        "docker-compose-plugin";
};
Unattended-Upgrade::Automatic-Reboot "false";
CONF
sudo tee /etc/apt/apt.conf.d/20auto-upgrades >/dev/null <<'CONF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
CONF

# A les 04:30, dins la franja vall i lluny de l'exportació nocturna de les 03:40.
sudo mkdir -p /etc/systemd/system/apt-daily-upgrade.timer.d
sudo tee /etc/systemd/system/apt-daily-upgrade.timer.d/99-hora.conf >/dev/null <<'CONF'
[Timer]
OnCalendar=
OnCalendar=*-*-* 04:30
RandomizedDelaySec=15m
CONF
sudo systemctl daemon-reload
ok "Només seguretat, a les 04:30, i Docker exclòs"

# ─────────────────────────────────────────────────────── 8. Tailscale ───────
log "Tailscale"
if ! command -v tailscale >/dev/null 2>&1; then
  curl -fsSL https://tailscale.com/install.sh | sh
else
  ok "Tailscale ja hi era"
fi

if tailscale status >/dev/null 2>&1; then
  ok "Ja connectat: $(tailscale ip -4 2>/dev/null | head -1)"
else
  avis "Ara sortirà un enllaç. Obre'l i autentica't; sense això no queda connectat."
  sudo tailscale up --hostname=local-ha
  ok "Tailscale up. IP: $(tailscale ip -4 2>/dev/null | head -1)"
fi

avis "PENDENT I IMPORTANT: entra a login.tailscale.com → Machines → local-ha"
avis "i desactiva-li l'expiració de la clau (Disable key expiry). Si no, caduca"
avis "sola d'aquí a uns mesos i et quedes sense accés al local."

# ────────────────────────────────────── 9. Memòria: menys intercanvi ────────
log "Baixar vm.swappiness de 60 a 10"
# 60 és el valor per defecte d'escriptori: assumeix que canviar de finestra
# pot esperar. Aquí no hi ha ningú davant la pantalla; hi ha un «recorder»
# escrivint a SQLite cada pocs segons durant dos anys, i el que interessa és
# que el conjunt de treball es quedi a la RAM.
#
# Es pot fer perquè el disc va resultar ser un SSD NVMe i no una eMMC: la
# reserva que hi havia contra tocar l'intercanvi va caure el 20/09/2026.
#
# ⚠️ NO és treure l'intercanvi. Els 4 GB de swap segueixen sent la xarxa de
#    seguretat sota els sostres del docker-compose.yml: amb «swappiness=10»
#    el kernel hi recorre menys, no deixa de recórrer-hi.
sudo mkdir -p /etc/sysctl.d
sudo tee /etc/sysctl.d/99-memoria.conf >/dev/null <<'CONF'
# Servidor sense escriptori, RAM soldada de 4 GB, disc SSD NVMe.
vm.swappiness=10
CONF
sudo sysctl --system >/dev/null 2>&1 || sudo sysctl -p /etc/sysctl.d/99-memoria.conf >/dev/null
ok "vm.swappiness = $(cat /proc/sys/vm/swappiness)"
# ⚠️ Això canvia la POLÍTICA d'ara endavant; NO buida el que ja hi ha a
#    l'intercanvi. El que hi hagués abans hi seguirà fins que algú el toqui.
#    Si vols la foto neta, cal un reinici (o «swapoff -a && swapon -a», que
#    necessita prou RAM lliure per encabir-ho tot i aquí val més no jugar-hi).
usat=$(awk '/^SwapTotal/{t=$2} /^SwapFree/{f=$2} END{print int((t-f)/1024)}' /proc/meminfo)
if [ "${usat:-0}" -gt 0 ] 2>/dev/null; then
  avis "hi ha $usat MB ja a l'intercanvi: no es mouran fins a un reinici"
fi

# ───────────────────────────────────────────────────────── Diagnòstic ────────
log "Com ha quedat la màquina"
echo
echo "  CPU     : $(lscpu | awk -F: '/Model name/{gsub(/^ +/,"",$2); print $2; exit}')"
echo "  Nuclis  : $(nproc)"
echo "  RAM     : $(free -h | awk '/^Mem:/{print $2}')"
echo "  IP      : $(hostname -I | awk '{print $1}')"
echo "  Usuari  : $USER@$(hostname)"
echo
echo "  Discos:"
lsblk -d -o NAME,SIZE,MODEL,TRAN | sed 's/^/    /'
echo
if lsblk -d -o NAME | grep -q '^mmcblk'; then
  avis "El disc és eMMC SOLDADA → gens de fitxer d'intercanvi. Cal zram."
else
  ok "El disc NO és eMMC: és un SSD substituïble."
fi

log "Fet"
cat <<FI

  🔴 TANCA LA SESSIÓ I TORNA A ENTRAR (o reinicia) abans de res més:
     fins llavors, «docker» et seguirà demanant sudo.

  I des d'ara ja pots treballar des de casa, sense tocar aquest teclat:

     ssh $USER@$(hostname -I | awk '{print $1}')

FI
