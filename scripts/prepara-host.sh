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
#
# El que NO fa encara, i queda per a un segon guió:
#   · unattended-upgrades només de seguretat, excloent docker-ce*
#   · Tailscale (A.3) — la clau va al seu web, és feina teva
#   · zram, si resulta que el disc és eMMC (ho decidim quan sapiguem què és)

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
sudo apt-get install -y -qq openssh-server git curl ca-certificates
sudo systemctl enable --now ssh
ok "SSH actiu. A partir d'ara pots entrar-hi des de casa i deixar de teclejar aquí."

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
