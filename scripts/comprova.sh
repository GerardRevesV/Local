#!/usr/bin/env bash
#
# comprova.sh — radiografia del servidor en una sola ordre.
#
# Des de casa:   ssh local-ha "cd ~/Local && bash scripts/comprova.sh"
# Al servidor:   bash scripts/comprova.sh
#
# Surt amb codi != 0 si troba res que estigui malament de debò, de manera que
# també es pot encadenar com a porta abans de donar un canvi per bo.
#
# No toca res. Només mira.

set -uo pipefail
cd "$(dirname "$0")/.."

t(){ printf '\n\033[1;34m── %s\033[0m\n' "$*"; }
ok(){   printf '  \033[32m✓\033[0m %s\n' "$*"; }
avis(){ printf '  \033[33m⚠\033[0m %s\n' "$*"; }
mal(){  printf '  \033[31m✗\033[0m %s\n' "$*"; PROBLEMES=$((PROBLEMES+1)); }
PROBLEMES=0

# ───────────────────────────────────────────────────────────── màquina ──────
t "Màquina"
ok "$(uptime -p) · càrrega$(uptime | sed 's/.*load average://')"
df -h / | awk 'NR==2{printf "  \033[32m✓\033[0m disc: %s lliures de %s (%s ple)\n",$4,$2,$5}'
if [ -d /sys/class/power_supply/BAT0 ] || [ -d /sys/class/power_supply/BAT1 ]; then
  B=$(ls -d /sys/class/power_supply/BAT* 2>/dev/null | head -1)
  now=$(cat "$B/energy_full" 2>/dev/null || echo 0)
  des=$(cat "$B/energy_full_design" 2>/dev/null || echo 0)
  cap=$(cat "$B/capacity" 2>/dev/null || echo "?")
  if [ "$des" -gt 0 ] 2>/dev/null; then
    salut=$(( now * 100 / des ))
    [ "$salut" -lt 60 ] && avis "bateria: $salut % de salut — el marge davant un tall s'escurça" \
                        || ok "bateria: $salut % de salut, càrrega actual $cap %"
  fi
fi

# ───────────────────────────────────────────────────────────── serveis ──────
t "Serveis que han de sobreviure un reinici"
for s in ssh docker tailscaled; do
  [ "$(systemctl is-active "$s" 2>&1)" = active ] && ok "$s actiu" || mal "$s ATURAT"
done
for s in sleep.target suspend.target; do
  [ "$(systemctl is-enabled "$s" 2>&1)" = masked ] && ok "$s emmascarat" || mal "$s NO emmascarat — la màquina es pot adormir"
done
grep -qh "^HandleLidSwitch=ignore" /etc/systemd/logind.conf.d/*.conf 2>/dev/null \
  && ok "la tapa no suspèn" || mal "la tapa SUSPÈN — tancar-la aturaria el registre"

# ─────────────────────────────────────────────────────── home assistant ─────
t "Home Assistant"
estat=$(docker compose ps --format '{{.Status}}' 2>/dev/null | head -1)
[ -n "$estat" ] && ok "contenidor: $estat" || mal "el contenidor no corre"
codi=$(curl -s -o /dev/null -w '%{http_code}' -m 10 http://127.0.0.1:8123 2>/dev/null)
[ "$codi" = 200 ] && ok "respon a 8123" || mal "8123 no respon (codi $codi)"

sortida=$(docker compose exec -T homeassistant python -m homeassistant \
            --script check_config -c /config 2>&1 | sed -e 's/\x1b\[[0-9;]*m//g')
if echo "$sortida" | grep -qiE 'ERROR|Failed|Fatal'; then
  mal "check_config amb errors:"; echo "$sortida" | grep -iE 'ERROR|Failed|Fatal' | head -3 | sed 's/^/      /'
else
  ok "check_config net"
fi

# ──────────────────────────────────────────── el recorder, que és el moll ───
t "L'històric — la línia que no té arreglada"
dies=$(docker compose exec -T homeassistant \
         grep -oP 'purge_keep_days:\s*\K[0-9]+' /config/configuration.yaml 2>/dev/null | head -1)
[ "$dies" = 730 ] && ok "purge_keep_days: 730, vist des de dins del contenidor" \
                  || mal "purge_keep_days és «$dies», hauria de ser 730"
db=config/home-assistant_v2.db
[ -f "$db" ] && ok "base de dades: $(du -h "$db" | cut -f1)" || avis "encara no hi ha base de dades"

# ───────────────────────────────────────────────────────────── entitats ─────
t "Les entitats que la lògica necessita"
TOK=~/.ha_token
if [ ! -r "$TOK" ]; then
  avis "sense ~/.ha_token: em salto la comprovació d'entitats"
else
  T=$(tr -d '\n\r' < "$TOK")
  curl -s -m 15 -H "Authorization: Bearer $T" http://127.0.0.1:8123/api/states \
    | python3 -c 'import sys,json;print("\n".join(sorted(x["entity_id"] for x in json.load(sys.stdin))))' \
    > /tmp/_real.txt 2>/dev/null

  if [ ! -s /tmp/_real.txt ]; then
    mal "l'API no respon o el testimoni no val"
  else
    ok "$(wc -l < /tmp/_real.txt) entitats a HA"
    grep -oE "(states|state_attr|is_state)\(\s*'[a-z_]+\.[a-z0-9_]+'" config/packages/rosada.yaml \
      | grep -oE "[a-z_]+\.[a-z0-9_]+" | sort -u > /tmp/_ref.txt
    trencades=0; pendents=0
    while read -r e; do
      grep -qx "$e" /tmp/_real.txt && continue
      case "$e" in
        *_temperatura|*_humitat|*superficie|sensor.aemet_*) pendents=$((pendents+1)) ;;
        *) mal "referència TRENCADA: $e"; trencades=$((trencades+1)) ;;
      esac
    done < /tmp/_ref.txt
    [ "$trencades" -eq 0 ] && ok "cap referència trencada a rosada.yaml"
    [ "$pendents" -gt 0 ] && avis "$pendents referències esperen maquinari (Tapo, ESP32, AEMET) — és normal fins a la integració"

    # El sensor que decideix: ha d'existir. Que digui «sense_dades» és correcte
    # mentre no hi hagi sensors; el que no pot és faltar.
    d=$(curl -s -m 10 -H "Authorization: Bearer $T" \
          http://127.0.0.1:8123/api/states/sensor.decisio_del_soterrani \
        | python3 -c 'import sys,json
try:
    d=json.load(sys.stdin); print(d.get("state","?"),"|",(d.get("attributes") or {}).get("motiu","—"))
except Exception: print("FALTA")' 2>/dev/null)
    case "$d" in
      FALTA|"") mal "sensor.decisio_del_soterrani NO EXISTEIX" ;;
      *) ok "decisió: $d" ;;
    esac
  fi
fi

# ──────────────────────────────────────────────────────────── tailscale ─────
t "Accés remot"
if command -v tailscale >/dev/null 2>&1; then
  tailscale status >/dev/null 2>&1 && ok "connectat com a $(tailscale ip -4 2>/dev/null | head -1)" \
                                   || mal "Tailscale NO connectat"
  # Directe vs DERP: per DERP funciona, però amb latència i consumint dades.
  parell=$(tailscale status 2>/dev/null | awk '$5=="active;"||/active;/{print; exit}')
  case "$parell" in
    *direct*) ok "connexió DIRECTA amb l'altre node" ;;
    *relay*|*DERP*) avis "va per DERP (relé): funciona, però amb latència i gastant dades de la SIM" ;;
    *) avis "cap node actiu ara mateix — no es pot dir si va directe" ;;
  esac
else
  mal "Tailscale no instal·lat"
fi

# ─────────────────────────────────────────────────── dades de la SIM ────────
t "Consum de dades"
if command -v vnstat >/dev/null 2>&1; then
  vnstat --oneline 2>/dev/null | awk -F';' '{printf "  avui: %s ↓ %s ↑   ·   aquest mes: %s ↓ %s ↑\n",$4,$5,$9,$10}' \
    || avis "vnstat encara no té prou historial"
else
  avis "vnstat no instal·lat — sense ell no hi ha manera de saber què gasta la SIM"
fi

# ──────────────────────────────────────────────────────────── veredicte ─────
echo
if [ "$PROBLEMES" -eq 0 ]; then
  printf '\033[1;32m  Tot correcte.\033[0m\n\n'
else
  printf '\033[1;31m  %s cosa(es) per mirar.\033[0m\n\n' "$PROBLEMES"
fi
exit $(( PROBLEMES > 0 ))
