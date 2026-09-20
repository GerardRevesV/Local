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

# Situar-se a l'arrel del repositori. Si no es pot, s'ha de plantar aquí:
# un guió de salut que no troba els fitxers informaria de fallades falses,
# i això és pitjor que no comprovar res.
ARREL="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." 2>/dev/null && pwd)"
if [ ! -f "${ARREL:-}/docker-compose.yml" ]; then
  ARREL="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel 2>/dev/null || true)"
fi
if [ ! -f "${ARREL:-}/docker-compose.yml" ]; then
  echo "No trobo l'arrel del repositori (hi falta docker-compose.yml)." >&2
  echo "Executa'l des de dins del repositori: bash scripts/comprova.sh" >&2
  exit 2
fi
cd "$ARREL"

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

# ──────────────────────────────────────────────────────── els contenidors ───
t "Els contenidors — TOTS ELS QUE HI HA D'HAVER"

# ⚠️ Aquí hi havia el forat més car del guió: es mirava
#       docker compose ps --format '{{.Status}}' | head -1
#    i es donava per bo. Amb UN contenidor passava; des que n'hi ha DOS, això
#    comprovava un i callava sobre l'altre. Si el matter-server queia, el
#    guió deia «Tot correcte» i el hub deixava d'enviar lectures en silenci.
#
# ⚠️ I el «head -1» era pitjor del que sembla: «docker compose ps» SENSE «-a»
#    només llista els que corren. Un contenidor aturat no surt a la llista:
#    desapareix. O sigui que si el primer queia i el segon seguia viu, el
#    «head -1» agafava l'estat del SEGON i l'imprimia com si fos del primer.
#    Un fals verd amb el contenidor mort. Per això va «-a», i per servei.
#
# La llista va ESCRITA i no surt de «docker compose config --services»: si
# algú treu un servei del compose, volem que això ho canti, no que s'adapti
# en silenci. Que l'stack passés d'un contenidor a dos sense que el guió se
# n'adonés és exactament l'error que estem arreglant.
ESPERATS="homeassistant matter-server"

for s in $ESPERATS; do
  estat=$(docker compose ps -a --format '{{.Status}}' "$s" 2>/dev/null | head -1)
  case "$estat" in
    Up*)         ok "$s: $estat" ;;
    Restarting*) mal "$s EN BUCLE DE REINICI: $estat" ;;
    # 137 = mort pel kernel per memòria. Vegeu «Quan el sostre es toca» a
    # docs/domotica/home-assistant.md.
    "Exited (137)"*) mal "$s ATURAT PER MEMÒRIA (codi 137): $estat" ;;
    Exited*)     mal "$s ATURAT: $estat" ;;
    Created*)    mal "$s creat però mai arrencat: $estat" ;;
    Paused*)     mal "$s EN PAUSA: $estat" ;;
    "")          mal "$s no existeix — ni aturat" ;;
    *)           mal "$s en estat inesperat: $estat" ;;
  esac
done

# I a l'inrevés: un servei nou al compose que ningú no hagi afegit a la
# llista de dalt. És com va començar tot això.
reals=$(docker compose config --services 2>/dev/null)
if [ -n "$reals" ]; then
  for s in $reals; do
    case " $ESPERATS " in
      *" $s "*) ;;
      *) mal "«$s» és al docker-compose.yml i NO es comprova — afegeix-lo a ESPERATS" ;;
    esac
  done
fi

# ─────────────────────────────────────────────────────── home assistant ─────
t "Home Assistant"
codi=$(curl -s -o /dev/null -w '%{http_code}' -m 10 http://127.0.0.1:8123 2>/dev/null)
[ "$codi" = 200 ] && ok "respon a 8123" || mal "8123 no respon (codi $codi)"

# ⚠️ Cal mirar el CODI DE SORTIDA, no només el text. Si `docker compose exec`
# falla (contenidor mort, dimoni caigut), el missatge no conté «ERROR» ni
# «Failed», i només buscant text s'imprimiria «check_config net» amb el
# contenidor apagat. Un fals verd aquí és el més car de tot el guió.
sortida=$(docker compose exec -T homeassistant python -m homeassistant \
            --script check_config -c /config 2>&1); codi_cc=$?
sortida=$(printf '%s' "$sortida" | sed -e 's/\x1b\[[0-9;]*m//g')
if [ "$codi_cc" -ne 0 ]; then
  mal "check_config NO s'ha pogut executar (codi $codi_cc):"
  printf '%s\n' "$sortida" | head -2 | sed 's/^/      /'
elif printf '%s' "$sortida" | grep -qiE 'ERROR|Failed|Fatal'; then
  mal "check_config amb errors:"
  printf '%s\n' "$sortida" | grep -iE 'ERROR|Failed|Fatal' | head -3 | sed 's/^/      /'
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

# ─────────────────────────────────────────────── el sostre de memòria ───────
t "El sostre de memòria — 4 GB soldats, sense camí d'ampliació"

# Sostres esperats, en MB. Han de quadrar amb docker-compose.yml: si algú
# desplega un compose sense sostre, aquí ha de sonar l'alarma i no passar
# desapercebut. Un contenidor sense sostre pot endur-se la màquina sencera.
for par in "homeassistant:1536" "matter-server:512"; do
  c="${par%%:*}"; esperat="${par##*:}"
  if ! docker inspect "$c" >/dev/null 2>&1; then
    mal "$c: el contenidor no existeix"
    continue
  fi
  lim=$(docker inspect -f '{{.HostConfig.Memory}}' "$c" 2>/dev/null || echo 0)
  lim_mb=$(( ${lim:-0} / 1024 / 1024 ))
  if [ "$lim_mb" -eq 0 ]; then
    mal "$c SENSE sostre de memòria — una fuita s'enduria tota la màquina"
  elif [ "$lim_mb" -ne "$esperat" ]; then
    avis "$c: sostre $lim_mb MB, i el compose en diu $esperat — algú no ha recreat el contenidor"
  else
    ok "$c: sostre $lim_mb MB"
  fi

  # ⚠️ «.State.OOMKilled» NO és prou. Amb «restart: unless-stopped» el
  # contenidor es torna a aixecar tot sol, i en aixecar-se l'estat es
  # renova: un OOM de matinada pot tenir OOMKilled=false a les nou del
  # matí. És útil si el trobes aturat; no serveix com a registre. El rastre
  # que dura és el del kernel, aquí sota.
  if [ "$(docker inspect -f '{{.State.OOMKilled}}' "$c" 2>/dev/null)" = true ]; then
    mal "$c: l'última aturada va ser per MEMÒRIA — hi ha un forat a l'històric"
  fi
  rc=$(docker inspect -f '{{.RestartCount}}' "$c" 2>/dev/null)
  [ "${rc:-0}" -gt 0 ] 2>/dev/null \
    && avis "$c: $rc reinicis des que es va crear el contenidor" \
    || true
done

# El registre que sobreviu al reinici. El journal té sostre de 200 MB
# (prepara-host.sh), o sigui que 7 dies hi caben de llarg.
if journalctl -k -n 1 >/dev/null 2>&1; then
  oom=$(journalctl -k --since "-7 days" 2>/dev/null \
          | grep -ciE 'oom-kill:|Out of memory: Killed process' || true)
  [ "${oom:-0}" -eq 0 ] \
    && ok "cap mort per memòria al kernel en 7 dies" \
    || mal "$oom mort(s) per memòria al kernel en 7 dies — mira'n l'hora i cerca el forat"
else
  avis "no puc llegir el journal del kernel — cal ser del grup «adm» o «systemd-journal»"
fi

sw=$(cat /proc/sys/vm/swappiness 2>/dev/null || echo "?")
[ "$sw" = 10 ] && ok "vm.swappiness=10" \
               || avis "vm.swappiness=$sw — s'espera 10 (vegeu prepara-host.sh)"
free -m | awk '/^Mem:/{
  if ($7 < 400) printf "  \033[33m⚠\033[0m RAM: només %s MB disponibles de %s MB\n",$7,$2;
  else          printf "  \033[32m✓\033[0m RAM: %s MB disponibles de %s MB\n",$7,$2 }'

# PSI: el senyal honest de si la màquina PATEIX per memòria, per sobre del que
# digui «free». «avg60» per sobre de zero ja vol dir esperes reals.
if [ -r /proc/pressure/memory ]; then
  psi=$(awk '/^some/{for(i=1;i<=NF;i++){if($i ~ /^avg60=/){sub(/avg60=/,"",$i); print $i}}}' \
          /proc/pressure/memory 2>/dev/null | head -1)
  case "${psi:-0}" in
    0.00|0|"") ok "sense pressió de memòria (PSI avg60 = ${psi:-0})" ;;
    *)         avis "PRESSIÓ de memòria: PSI avg60 = $psi" ;;
  esac
fi

# ───────────────────────────────────────────────────────────── entitats ─────
t "Les entitats que la lògica necessita"
TOK=~/.ha_token
if [ ! -r "$TOK" ]; then
  avis "sense ~/.ha_token: em salto la comprovació d'entitats"
else
  T=$(tr -d '\n\r' < "$TOK")
  # Noms fixos a /tmp fallarien si el guió el llança un altre usuari (cron,
  # root): el fitxer ja existiria i seria d'algú altre, i el redirigit petaria
  # amb un «l'API no respon» que seria mentida.
  REAL=$(mktemp); REF=$(mktemp)
  trap 'rm -f "$REAL" "$REF"' EXIT
  curl -s -m 15 -H "Authorization: Bearer $T" http://127.0.0.1:8123/api/states \
    | python3 -c 'import sys,json;print("\n".join(sorted(x["entity_id"] for x in json.load(sys.stdin))))' \
    > "$REAL" 2>/dev/null

  if [ ! -s "$REAL" ]; then
    mal "l'API no respon o el testimoni no val"
  else
    ok "$(wc -l < "$REAL") entitats a HA"
    grep -oE "(states|state_attr|is_state)\(\s*'[a-z_]+\.[a-z0-9_]+'" config/packages/rosada.yaml \
      | grep -oE "[a-z_]+\.[a-z0-9_]+" | sort -u > "$REF"
    trencades=0; pendents=0
    while read -r e; do
      grep -qx "$e" "$REAL" && continue
      case "$e" in
        *_temperatura|*_humitat|*superficie|sensor.aemet_*) pendents=$((pendents+1)) ;;
        *) mal "referència TRENCADA: $e"; trencades=$((trencades+1)) ;;
      esac
    done < "$REF"
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
