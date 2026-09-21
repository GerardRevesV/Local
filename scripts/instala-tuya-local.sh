#!/usr/bin/env bash
#
# instala-tuya-local.sh — posa la integració «tuya-local» a HA, en una versió fixada.
#
#   bash scripts/instala-tuya-local.sh
#
# QUÈ RESOL
# ─────────
# El deshumidificador (Qlima D825) és un aparell Tuya. «tuya-local» el parla
# EN LOCAL, per la xarxa del router, sense passar pel núvol de Tuya: el llindar
# d'humitat, engegar-lo sense tallar-li el corrent, i els codis P1/P2.
# Tasca B.1c de docs/domotica/fases.md · decisió a docs/domotica/inventari.md
#
# PER QUÈ AIXÒ I NO HACS
# ──────────────────────
# Les versions d'aquest projecte es fixen i s'actualitzen a posta, amb un
# commit datat: així ho fem amb HA (etiqueta) i amb el matter-server (digest).
# HACS convida a actualitzar des de la interfície sense pensar-hi, i demana
# vincular un compte de GitHub. Aquí la versió i la suma SHA-256 són a sota:
# si el paquet que arriba no és exactament aquell, NO s'instal·la res.
#
# ⚠️ ACTUALITZAR és canviar VERSIO i SHA256 en un commit, i tornar a córrer
#    això. La suma es treu així, a casa:
#      curl -sL https://codeload.github.com/make-all/tuya-local/tar.gz/refs/tags/<VERSIO> | sha256sum
#    I es mira abans que el «homeassistant» del seu hacs.json no passi de la
#    versió d'HA que tenim fixada al docker-compose.yml.
#
# ⚠️ NO REINICIA HA. Carregar una integració nova sí que el demana, i un
#    reinici és un forat a l'històric: es decideix a part, i es fa a mà.
#
# El codi de tercers NO es versiona (config/custom_components/ és al
# .gitignore): el que es versiona és AQUEST fitxer, que diu quin codi exacte hi
# ha d'haver. Idempotent: si ja hi és la mateixa versió, no fa res.

set -euo pipefail

VERSIO="2026.9.1"
SHA256="6d786cd69f8beeb9c1a67658d735aa7840d0ceaff09e5eb2c8cae9f1d9c2b06d"
URL="https://codeload.github.com/make-all/tuya-local/tar.gz/refs/tags/${VERSIO}"

ARREL="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
[ -f "$ARREL/docker-compose.yml" ] || { echo "Executa'l des de dins del repositori." >&2; exit 2; }
DESTI="$ARREL/config/custom_components/tuya_local"
MARCA="$DESTI/.versio-local"

ok()   { printf '  \033[32m✓\033[0m %s\n' "$*"; }
mal()  { printf '  \033[31m✗\033[0m %s\n' "$*" >&2; }
avis() { printf '  \033[33m⚠\033[0m %s\n' "$*"; }

if [ -f "$MARCA" ] && grep -qx "$VERSIO $SHA256" "$MARCA"; then
  ok "tuya-local $VERSIO ja hi és. No cal fer res."
  exit 0
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

curl -fsSL --retry 3 -o "$TMP/paquet.tar.gz" "$URL" \
  || { mal "No s'ha pogut baixar $URL"; exit 1; }

REAL="$(sha256sum "$TMP/paquet.tar.gz" | cut -d' ' -f1)"
if [ "$REAL" != "$SHA256" ]; then
  mal "La suma NO quadra: s'esperava $SHA256"
  mal "                   i ha arribat $REAL"
  mal "No s'instal·la res. Si GitHub ha canviat el paquet, cal revisar-lo a mà."
  exit 1
fi
ok "Paquet de tuya-local $VERSIO verificat (SHA-256)"

tar -xzf "$TMP/paquet.tar.gz" -C "$TMP" "tuya-local-${VERSIO}/custom_components/tuya_local"
NOU="$TMP/tuya-local-${VERSIO}/custom_components/tuya_local"
grep -q "\"version\": \"${VERSIO}\"" "$NOU/manifest.json" \
  || { mal "El manifest no diu la versió $VERSIO"; exit 1; }
echo "$VERSIO $SHA256" > "$NOU/.versio-local"

# Es canvia de cop: primer la còpia nova al costat, després el relleu. Així HA
# mai no troba mitja integració si arrenca enmig.
mkdir -p "$(dirname "$DESTI")"
rm -rf "$DESTI.nou" "$DESTI.vell"
cp -a "$NOU" "$DESTI.nou"
[ -d "$DESTI" ] && mv "$DESTI" "$DESTI.vell"
mv "$DESTI.nou" "$DESTI"
rm -rf "$DESTI.vell"
ok "Instal·lada a config/custom_components/tuya_local"

avis "HA encara no la veu: carregar una integració nova demana REINICIAR HA."
avis "Abans: check_config. Després, a la interfície: Afegeix integració → Tuya Local."
