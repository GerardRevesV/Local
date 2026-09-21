#!/usr/bin/env bash
#
# comprova.sh — radiografia del servidor en una sola ordre.
#
# Des de casa:   ssh local-ha "cd ~/Local && bash scripts/comprova.sh"
# Al servidor:   bash scripts/comprova.sh
#                bash scripts/comprova.sh --breu   (el cos del ping de bategada.sh)
#
# Surt amb codi != 0 si troba res que estigui malament de debò, de manera que
# també es pot encadenar com a porta abans de donar un canvi per bo.
#
# No toca res. Només mira.
#
# «--breu» és el mateix guió amb menys veu, per al cos del ping de
# healthchecks.io: sense colors ni capçaleres, dels ✓ només els que porten una
# dada, i sense les comprovacions que no toca fer cada 30 minuts. Hi ha UNA
# sola llista del que ha d'estar bé: si una comprovació nova entra aquí,
# l'avís de caiguda la hereta sense tocar-lo.

set -uo pipefail

BREU=0
case "${1:-}" in
  "")      ;;
  --breu)  BREU=1 ;;
  *)       echo "Ús: bash scripts/comprova.sh [--breu]" >&2; exit 2 ;;
esac

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

# «fet» és un ✓ que porta una dada que val la pena llegir al correu de l'avís
# (el disc, la bateria, l'edat de l'última escriptura). En mode normal és un ✓
# com els altres; en mode breu és l'únic ✓ que surt.
if [ "$BREU" = 1 ]; then
  t(){ :; }
  ok(){ :; }
  fet(){  printf '· %s\n' "$*"; }
  avis(){ printf '⚠ %s\n' "$*"; }
  mal(){  printf '✗ %s\n' "$*"; PROBLEMES=$((PROBLEMES+1)); }
else
  t(){ printf '\n\033[1;34m── %s\033[0m\n' "$*"; }
  ok(){   printf '  \033[32m✓\033[0m %s\n' "$*"; }
  fet(){  ok "$@"; }
  avis(){ printf '  \033[33m⚠\033[0m %s\n' "$*"; }
  mal(){  printf '  \033[31m✗\033[0m %s\n' "$*"; PROBLEMES=$((PROBLEMES+1)); }
fi
PROBLEMES=0

# 75 → «1 min», 7400 → «2 h 3 min». Per a edats que s'han de llegir d'un cop d'ull.
durada(){
  local s=$1
  if   [ "$s" -lt 60 ];    then echo "$s s"
  elif [ "$s" -lt 3600 ];  then echo "$((s/60)) min"
  elif [ "$s" -lt 86400 ]; then echo "$((s/3600)) h $((s%3600/60)) min"
  else                          echo "$((s/86400)) d $((s%86400/3600)) h"
  fi
}

# ───────────────────────────────────────────────────────────── màquina ──────
t "Màquina"
fet "$(uptime -p), des del $(uptime -s | cut -c1-16) · càrrega$(uptime | sed 's/.*load average://')"
read -r d_lliure d_mida d_ple < <(df -h / | awk 'NR==2{print $4, $2, $5}')
if [ "${d_ple%\%}" -lt 90 ] 2>/dev/null; then
  fet "disc: $d_lliure lliures de $d_mida ($d_ple ple)"
else
  mal "disc: només $d_lliure lliures de $d_mida ($d_ple ple) — amb el disc ple el recorder deixa d'escriure"
fi

# ⚠️ El que diu si ha caigut la llum és l'ADAPTADOR, no la bateria: una bateria
#    plena i un «Full» no volen dir que hi hagi corrent. Es busca per tipus
#    (Mains) i no pel nom, que canvia d'un portàtil a un altre (AC, ACAD, ADP1).
xarxa=""
for p in /sys/class/power_supply/*; do
  [ "$(cat "$p/type" 2>/dev/null)" = Mains ] || continue
  [ "$(cat "$p/online" 2>/dev/null)" = 1 ] && xarxa=1 || xarxa=${xarxa:-0}
done

B=$(ls -d /sys/class/power_supply/BAT* 2>/dev/null | head -1)
bateria="sense bateria"
salut=""
if [ -n "$B" ]; then
  # ⚠️ Unes bateries donen energy_* (µWh) i d'altres charge_* (µAh). La
  #    d'aquest portàtil dona charge_*, i fins al 21/09/2026 el guió només
  #    llegia energy_*: la línia de la bateria NO havia sortit mai, i callava
  #    sense dir-ho. Cal provar tots dos prefixos.
  for pre in energy charge; do
    if [ -r "$B/${pre}_full" ] && [ -r "$B/${pre}_full_design" ]; then
      ple_ara=$(cat "$B/${pre}_full"); ple_dis=$(cat "$B/${pre}_full_design")
      [ "${ple_dis:-0}" -gt 0 ] 2>/dev/null && salut=$(( ple_ara * 100 / ple_dis ))
      break
    fi
  done
  case "$(cat "$B/status" 2>/dev/null)" in
    Full)           e="plena" ;;
    Charging)       e="carregant" ;;
    Discharging)    e="DESCARREGANT" ;;
    "Not charging") e="sense carregar" ;;
    *)              e="estat desconegut" ;;
  esac
  bateria="bateria $(cat "$B/capacity" 2>/dev/null || echo "?") % ($e)${salut:+, salut $salut %}"
fi

case "$xarxa" in
  1) fet "corrent: sí · $bateria" ;;
  0) mal "SENSE CORRENT — va amb la bateria: $bateria. Ha caigut la llum o el carregador" ;;
  *) avis "no trobo l'adaptador de corrent a /sys: no puc dir si hi ha llum · $bateria" ;;
esac
if [ -n "$B" ] && [ -z "$salut" ]; then
  avis "no sé llegir la salut de la bateria ($B)"
elif [ -n "$salut" ] && [ "$salut" -lt 60 ]; then
  avis "bateria: $salut % de salut — el marge davant un tall s'escurça (llindar del SAI)"
fi

# ───────────────────────────────────────────────────────────── serveis ──────
t "Serveis que han de sobreviure un reinici"
# «cron» hi és per la bategada: si s'atura, l'avís de caiguda calla. El ping
# no pot dir-ho (és el cron qui el llança); el silenci i aquesta línia, sí.
for s in ssh docker tailscaled cron; do
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
    Up*)         fet "$s: $estat" ;;
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

# En mode breu, check_config NO: aixeca un segon Home Assistant dins del
# contenidor, amb el sostre de 1.536 MB compartit amb el que ja corre. Un cop
# després de cada canvi, bé; cada 30 minuts, és buscar-li un OOM al contenidor
# que grava. La configuració no canvia sola entre dos desplegaments.
if [ "$BREU" = 0 ]; then

# ⚠️ «</dev/null» NO és decoratiu: «docker compose exec -T» s'enganxa a
# l'entrada estàndard del guió. Si aquest arriba per una canonada —«ssh host
# bash -s», cron, un altre guió—, l'exec se l'empassa i es queda penjat fins
# que venci el temps. Passa només quan no hi ha terminal, que és justament
# quan no hi ha ningú mirant. Comprovat el 21/09/2026: 4 s amb la redirecció,
# més de 280 s sense.
#
# ⚠️ I BUSCAR-HI «Incorrect config», que no diu «ERROR» enlloc.
#    Comprovat el 21/09/2026 amb una clau invàlida posada a posta: check_config
#    surt amb CODI 0 i escriu «Incorrect config» i «Invalid config for ...»,
#    sense la paraula ERROR, Failed ni Fatal. Amb el patró antic, aquest guió
#    hauria dit «check_config net» amb la configuració rebentada. El codi de
#    sortida no serveix per a això, i el text només si s'hi busca el que toca.
#
# ⚠️ Cal mirar el CODI DE SORTIDA, no només el text. Si `docker compose exec`
# falla (contenidor mort, dimoni caigut), el missatge no conté «ERROR» ni
# «Failed», i només buscant text s'imprimiria «check_config net» amb el
# contenidor apagat. Un fals verd aquí és el més car de tot el guió.
sortida=$(docker compose exec -T homeassistant python -m homeassistant \
            --script check_config -c /config </dev/null 2>&1); codi_cc=$?
sortida=$(printf '%s' "$sortida" | sed -e 's/\x1b\[[0-9;]*m//g')
if [ "$codi_cc" -ne 0 ]; then
  mal "check_config NO s'ha pogut executar (codi $codi_cc):"
  printf '%s\n' "$sortida" | head -2 | sed 's/^/      /'
elif printf '%s' "$sortida" | grep -qiE 'ERROR|Failed|Fatal|Incorrect config|Invalid config'; then
  mal "check_config amb errors:"
  printf '%s\n' "$sortida" | grep -iE 'ERROR|Failed|Fatal|Incorrect config|Invalid config' | head -3 | sed 's/^/      /'
else
  ok "check_config net"
fi
fi

# ──────────────────────────────────────────── el recorder, que és el moll ───
t "L'històric — la línia que no té arreglada"
dies=$(docker compose exec -T homeassistant \
         grep -oP 'purge_keep_days:\s*\K[0-9]+' /config/configuration.yaml </dev/null 2>/dev/null | head -1)
[ "$dies" = 730 ] && ok "purge_keep_days: 730, vist des de dins del contenidor" \
                  || mal "purge_keep_days és «$dies», hauria de ser 730"

# Que el recorder ESCRIU es mira al disc, no a l'API: /api/states és la
# màquina d'estats en memòria, i amb el recorder mort continua dient que tot va
# bé (decisio-stack.md, «On he donat la raó», punt 1). Amb WAL, cada commit
# (commit_interval: 30 s) toca el -wal, i el .db només es mou als checkpoints:
# es pren el més recent dels dos. Encara que cap sensor canviés, HA escriu les
# estadístiques de 5 minuts, o sigui que 15 minuts sense escriure és el
# recorder aturat, o HA sense res a gravar —cosa que també és una fallada.
db=config/home-assistant_v2.db
if [ -f "$db" ]; then
  darrera=$(stat -c %Y "$db" "$db-wal" 2>/dev/null | sort -n | tail -1)
  edat=$(( $(date +%s) - ${darrera:-0} ))
  if [ "$edat" -le 900 ]; then
    fet "recorder: última escriptura fa $(durada "$edat") · base de dades $(du -h "$db" | cut -f1)"
  else
    mal "el recorder NO ESCRIU: l'última escriptura a la base de dades és de fa $(durada "$edat")"
  fi
else
  mal "no hi ha base de dades ($db)"
fi

# ─────────────────────────────────────────────── el sostre de memòria ───────
t "El sostre de memòria — 4 GB soldats, sense camí d'ampliació"

# Sostres esperats, en MB. Han de quadrar amb docker-compose.yml: si algú
# desplega un compose sense sostre, aquí ha de sonar l'alarma i no passar
# desapercebut. Un contenidor sense sostre pot endur-se la màquina sencera.
reinicis=""
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
  reinicis="${reinicis:+$reinicis, }$c ${rc:-?}"
  # En mode breu, els reinicis van a la línia de la memòria de sota: com a ⚠
  # sortirien a cada ping fins que algú recreés el contenidor.
  [ "$BREU" = 0 ] && [ "${rc:-0}" -gt 0 ] 2>/dev/null \
    && avis "$c: $rc reinicis des que es va crear el contenidor" \
    || true
done

# El registre que sobreviu al reinici. El journal té sostre de 200 MB
# (prepara-host.sh), o sigui que 7 dies hi caben de llarg.
#
# ⚠️ En mode breu, el ✗ només pel que ha passat des del ping anterior (35 min:
#    els 30 del període i marge). healthchecks.io només avisa quan el check
#    CANVIA d'estat: un OOM que fes fallar la bategada 7 dies seguits la
#    deixaria en vermell tota la setmana, i qualsevol altra caiguda d'aquells
#    dies passaria SENSE correu. Així, cada OOM dona un avís i prou. El
#    recompte de 7 dies hi va igualment, a la línia de la memòria.
oom="?"
if journalctl -k -n 1 >/dev/null 2>&1; then
  patro='oom-kill:|Out of memory: Killed process'
  oom=$(journalctl -k --since "-7 days" 2>/dev/null | grep -ciE "$patro" || true)
  if [ "$BREU" = 1 ]; then
    oom_nou=$(journalctl -k --since "-35 min" 2>/dev/null | grep -ciE "$patro" || true)
    [ "${oom_nou:-0}" -eq 0 ] \
      || mal "$oom_nou mort(s) per memòria al kernel en l'última mitja hora — hi ha un forat a l'històric"
  else
    [ "${oom:-0}" -eq 0 ] \
      && ok "cap mort per memòria al kernel en 7 dies" \
      || mal "$oom mort(s) per memòria al kernel en 7 dies — mira'n l'hora i cerca el forat"
  fi
else
  avis "no puc llegir el journal del kernel — cal ser del grup «adm» o «systemd-journal»"
fi

sw=$(cat /proc/sys/vm/swappiness 2>/dev/null || echo "?")
[ "$sw" = 10 ] && ok "vm.swappiness=10" \
               || avis "vm.swappiness=$sw — s'espera 10 (vegeu prepara-host.sh)"
read -r ram_disp ram_total < <(free -m | awk '/^Mem:/{print $7, $2}')
[ "$BREU" = 1 ] \
  && fet "memòria: $ram_disp MB disponibles de $ram_total · OOM en 7 dies: $oom · reinicis: $reinicis"
if [ "${ram_disp:-0}" -lt 400 ] 2>/dev/null; then
  avis "RAM: només $ram_disp MB disponibles de $ram_total MB"
else
  ok "RAM: $ram_disp MB disponibles de $ram_total MB"
fi

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
    fet "API d'HA: respon, $(wc -l < "$REAL") entitats"
    grep -ohE "(states|state_attr|is_state)\(\s*'[a-z_]+\.[a-z0-9_]+'" config/packages/*.yaml \
      | grep -oE "[a-z_]+\.[a-z0-9_]+" | sort -u > "$REF"
    trencades=0; pendents=0
    while read -r e; do
      grep -qx "$e" "$REAL" && continue
      case "$e" in
        *_temperatura|*_humitat|*superficie|sensor.aemet_*) pendents=$((pendents+1)) ;;
        *) mal "referència TRENCADA: $e"; trencades=$((trencades+1)) ;;
      esac
    done < "$REF"
    [ "$trencades" -eq 0 ] && ok "cap referència trencada als paquets"
    # (En mode breu no: seria un ⚠ fix a cada ping fins que arribi l'ESP32.)
    [ "$BREU" = 0 ] && [ "$pendents" -gt 0 ] \
      && avis "$pendents referències esperen maquinari (Tapo, ESP32, AEMET) — és normal fins a la integració"

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
      *) fet "decisió: $d" ;;
    esac
  fi
fi

# ──────────────────────────────────────────────────────────── tailscale ─────
t "Accés remot"
# En mode breu, sense l'adreça: el cos del ping surt cap a un servei de fora,
# i no hi ha cap motiu perquè hi vagi.
if command -v tailscale >/dev/null 2>&1; then
  if tailscale status >/dev/null 2>&1; then
    [ "$BREU" = 1 ] && fet "tailscale: connectat" \
                    || ok "connectat com a $(tailscale ip -4 2>/dev/null | head -1)"
  else
    mal "Tailscale NO connectat — des de fora no s'hi pot entrar"
  fi
  # Directe vs DERP: per DERP funciona, però amb latència i consumint dades.
  # (En mode breu no: «cap node actiu» és el normal quan ningú no hi és connectat.)
  if [ "$BREU" = 0 ]; then
    parell=$(tailscale status 2>/dev/null | awk '$5=="active;"||/active;/{print; exit}')
    case "$parell" in
      *direct*) ok "connexió DIRECTA amb l'altre node" ;;
      *relay*|*DERP*) avis "va per DERP (relé): funciona, però amb latència i gastant dades de la SIM" ;;
      *) avis "cap node actiu ara mateix — no es pot dir si va directe" ;;
    esac
  fi
else
  mal "Tailscale no instal·lat"
fi

# El mode breu acaba aquí: el que queda és per a qui mira, no per a l'avís.
[ "$BREU" = 1 ] && exit $(( PROBLEMES > 0 ))

# ─────────────────────────────────────────────────── dades de la SIM ────────
t "Consum de dades"
if command -v vnstat >/dev/null 2>&1; then
  vnstat --oneline 2>/dev/null | awk -F';' '{printf "  avui: %s ↓ %s ↑   ·   aquest mes: %s ↓ %s ↑\n",$4,$5,$9,$10}' \
    || avis "vnstat encara no té prou historial"
else
  avis "vnstat no instal·lat — sense ell no hi ha manera de saber què gasta la SIM"
fi

# ───────────────────────────────────────────────────── l'avís de caiguda ────
# El ping no pot dir que no s'envia. Això sí: si la bategada no està
# programada, si l'URL no hi és o si fa estona que no surt, es veu aquí.
t "L'avís de caiguda (healthchecks.io)"
if crontab -l 2>/dev/null | grep -v '^#' | grep -q 'scripts/bategada.sh'; then
  ok "la bategada és a la crontab"
else
  mal "la bategada NO està programada — si la màquina cau, no t'assabentes (bash scripts/bategada.sh --instala)"
fi
URL_BAT=~/.bategada_url
if [ ! -r "$URL_BAT" ]; then
  mal "falta $URL_BAT — la bategada no sap on enviar-se"
elif [ "$(stat -c %a "$URL_BAT")" != 600 ]; then
  avis "$URL_BAT té permisos $(stat -c %a "$URL_BAT"): ha de ser 600, és un secret"
else
  ok "$URL_BAT hi és, amb permisos 600"
fi
DARRERA=${XDG_STATE_HOME:-$HOME/.local/state}/bategada/darrera
if [ -r "$DARRERA" ]; then
  read -r quan codi_bat < "$DARRERA"
  edat=$(( $(date +%s) - ${quan:-0} ))
  # 45 min: el període de 30 i marge. El cron la llança als minuts 7 i 37.
  if [ "$edat" -gt 2700 ]; then
    mal "l'última bategada enviada és de fa $(durada "$edat") — mira «journalctl -t bategada»"
  elif [ "${codi_bat:-0}" != 0 ]; then
    avis "l'última bategada (fa $(durada "$edat")) va sortir com a FALLADA (codi $codi_bat)"
  else
    ok "l'última bategada va sortir fa $(durada "$edat"), verda"
  fi
else
  avis "encara no s'ha enviat cap bategada des d'aquesta màquina"
fi

# ──────────────────────────────────────────────────────────── veredicte ─────
echo
if [ "$PROBLEMES" -eq 0 ]; then
  printf '\033[1;32m  Tot correcte.\033[0m\n\n'
else
  printf '\033[1;31m  %s cosa(es) per mirar.\033[0m\n\n' "$PROBLEMES"
fi
exit $(( PROBLEMES > 0 ))
