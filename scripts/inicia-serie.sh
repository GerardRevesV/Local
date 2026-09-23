#!/usr/bin/env bash
#
# inicia-serie.sh — el pas d'experimentació a la sèrie de debò.
#
#   bash scripts/inicia-serie.sh --de-debo
#   bash scripts/inicia-serie.sh --de-debo --apaga-marcador
#
# QUÈ RESOL
# ─────────
# Els sensors es proven a casa, i durant aquests dies graven a
# `sensor.soterrani_fons_temperatura` mentre són damunt d'una taula del
# menjador. Aquestes files entren a la mateixa base de dades i amb els
# mateixos noms que les de debò.
#
# Per a un arxiu que ha de servir davant d'un pèrit això és contaminació:
# dies de lectures etiquetades «Soterrani — Fons» que no són del soterrani.
# Trobat per l'altra part, posa en dubte la sèrie sencera.
#
# Aquest guió marca la frontera: arxiva el que hi ha, comença de zero, i
# deixa una data d'inici escrita i defensable.
#
# ⚠️ LA BASE DE DADES D'EXPERIMENTACIÓ NO S'ESBORRA: S'ARXIVA.
#    Conté el calibratge creuat — els dies amb tots els sensors junts són
#    l'única mesura de la desviació entre ells, i no es pot repetir un cop
#    estiguin repartits pel local.
#
# ⚠️ AMB EL MARCADOR DE CALIBRATGE ENCÈS, S'HI NEGA.
#    Mentre input_boolean.mode_calibratge és encès, la decisió diu
#    «calibratge» i res no actua: la sèrie de debò naixeria mal etiquetada.
#    El marcador no té «initial:» i HA el restaura de .storage, no de la base
#    de dades: buidar la base no l'apaga. --apaga-marcador l'apaga per l'API
#    just abans d'aturar HA, perquè el canvi on→off quedi a la base arxivada.

set -uo pipefail

ARREL="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." 2>/dev/null && pwd)"
[ -f "${ARREL:-}/docker-compose.yml" ] || {
  echo "Executa'l des de dins del repositori." >&2; exit 2; }
cd "$ARREL"

ok(){   printf '  \033[32m✓\033[0m %s\n' "$*"; }
mal(){  printf '  \033[31m✗\033[0m %s\n' "$*"; }
t(){    printf '\n\033[1;34m── %s\033[0m\n' "$*"; }

DE_DEBO=0; APAGA_MARCADOR=0
for a in "$@"; do
  case "$a" in
    --de-debo)        DE_DEBO=1 ;;
    --apaga-marcador) APAGA_MARCADOR=1 ;;
    *) echo "Opció desconeguda: $a" >&2; exit 2 ;;
  esac
done

if [ "$DE_DEBO" -ne 1 ]; then
  cat <<'AJUDA'

  inicia-serie.sh — tanca l'experimentació i comença la sèrie probatòria.

  Arxiva la base de dades actual (que conté el calibratge) i en comença una
  de nova, amb data d'inici escrita.

  ABANS D'EXECUTAR-LO, ha d'estar tot això fet:

    · Els sensors, al seu lloc DEFINITIU del local.
    · Els noms d'entitat fixats i renombrats. Canviar-ne un després
      parteix la sèrie.
    · El calibratge desplegat (custom_templates/calibratge.jinja).
    · El marcador input_boolean.mode_calibratge APAGAT. Si és encès, el
      guió s'hi nega; amb --apaga-marcador l'apaga ell just abans
      d'aturar HA, i el canvi queda a la base que s'arxiva.
    · El deshumidificador amb desguàs continu i l'endoll P110 al seu lloc.

  Si tot això hi és:      bash scripts/inicia-serie.sh --de-debo
  Amb el marcador encès:  bash scripts/inicia-serie.sh --de-debo --apaga-marcador

AJUDA
  exit 1
fi

PROBLEMES=0
t "Portes abans de tocar res"

# ── 1. El sistema ha d'estar sa ────────────────────────────────────────────
if bash scripts/comprova.sh >/dev/null 2>&1; then
  ok "comprova.sh passa"
else
  mal "comprova.sh falla — arregla-ho abans. Executa'l per veure què."
  PROBLEMES=$((PROBLEMES+1))
fi

# ── L'estat d'HA, llegit un sol cop per a les portes 2 i 3 ─────────────────
# Si no es pot llegir, les dues queden TANCADES. Abans, un testimoni caducat
# tornava un error en lloc del JSON, python petava en silenci i la porta dels
# sensors deia «tots reporten» sense haver-ne mirat cap.
HA=http://127.0.0.1:8123
MARCADOR=input_boolean.mode_calibratge
TOK=~/.ha_token
ESTATS=$(mktemp)
trap 'rm -f "$ESTATS"' EXIT
LLEGIT=0
if [ ! -r "$TOK" ]; then
  mal "sense ~/.ha_token: no puc comprovar ni els sensors ni el marcador"
  PROBLEMES=$((PROBLEMES+1))
else
  T=$(tr -d '\n\r' < "$TOK")
  if curl -sf -m 15 -H "Authorization: Bearer $T" "$HA/api/states" > "$ESTATS" \
     && python3 -c 'import sys,json; assert isinstance(json.load(open(sys.argv[1])), list)' \
          "$ESTATS" 2>/dev/null; then
    LLEGIT=1
  else
    mal "l'API d'HA no respon o el testimoni no val: no puc comprovar res"
    PROBLEMES=$((PROBLEMES+1))
  fi
fi

# L'estat d'una entitat, per l'API. «?» si no es pot llegir.
estat(){ curl -sf -m 5 -H "Authorization: Bearer $T" "$HA/api/states/$1" \
           | python3 -c 'import sys,json; print(json.load(sys.stdin)["state"])' 2>/dev/null \
         || echo "?"; }

# ── 2. Cap sensor mort ─────────────────────────────────────────────────────
# Començar la sèrie amb un sensor caigut vol dir un forat des del dia u,
# i el dia u és precisament el que es mirarà.
# La planta baixa té dos prefixos, i cap no conté l'altre: el Tapo i la seva
# humitat calibrada són sensor.baixa_*, els punts de rosada sensor.planta_baixa_*
# (noms-entitats.md). Fins al 23/09/2026 només hi havia el segon, i el sensor
# de dalt podia ser mort sense que la porta ho veiés.
if [ "$LLEGIT" -eq 1 ]; then
  morts=$(python3 -c '
import sys, json
mal = []
for e in json.load(open(sys.argv[1])):
    i = e["entity_id"]
    if i.startswith(("sensor.soterrani", "sensor.exterior",
                     "sensor.planta_baixa", "sensor.baixa_")) \
       and e["state"] in ("unavailable", "unknown", "sense_dades"):
        mal.append(i)
print("\n".join(mal))' "$ESTATS")
  if [ -n "$morts" ]; then
    mal "hi ha sensors sense lectura vàlida:"
    printf '%s\n' "$morts" | sed 's/^/      /'
    PROBLEMES=$((PROBLEMES+1))
  else
    ok "tots els sensors del local reporten"
  fi
fi

# ── 3. El marcador de calibratge, apagat ───────────────────────────────────
# Encès, la decisió diu «calibratge» i res no actua. Amb --apaga-marcador no
# es nega: l'apaga just abans d'aturar HA, un cop confirmat.
APAGAR=0
if [ "$LLEGIT" -eq 1 ]; then
  m=$(python3 -c '
import sys, json
print(next((e["state"] for e in json.load(open(sys.argv[1]))
            if e["entity_id"] == sys.argv[2]), "FALTA"))' "$ESTATS" "$MARCADOR")
  case "$m" in
    off) ok "$MARCADOR apagat" ;;
    on)
      if [ "$APAGA_MARCADOR" -eq 1 ]; then
        ok "$MARCADOR encès: l'apagaré just abans d'aturar HA (--apaga-marcador)"
        APAGAR=1
      else
        mal "$MARCADOR és ENCÈS: la sèrie començaria amb la decisió dient «calibratge»."
        echo "      Apaga'l des del tauler i torna-hi, o afegeix --apaga-marcador perquè"
        echo "      l'apagui jo just abans d'aturar HA (el canvi queda a la base arxivada)."
        PROBLEMES=$((PROBLEMES+1))
      fi ;;
    FALTA)
      mal "$MARCADOR no existeix a HA: no puc saber si la sèrie començaria bé"
      PROBLEMES=$((PROBLEMES+1)) ;;
    *)
      mal "$MARCADOR val «$m», i ha de valer «off»"
      PROBLEMES=$((PROBLEMES+1)) ;;
  esac
fi

# ── 4. L'arbre de git, net ─────────────────────────────────────────────────
if [ -z "$(git status --porcelain)" ]; then
  ok "arbre de git net"
else
  mal "l'arbre té canvis sense commitar: el que corri ha d'estar versionat"
  PROBLEMES=$((PROBLEMES+1))
fi

if [ "$PROBLEMES" -gt 0 ]; then
  printf '\n\033[1;31m  %s porta(es) tancada(es). No toco res.\033[0m\n\n' "$PROBLEMES"
  exit 1
fi

# ── Confirmació humana ─────────────────────────────────────────────────────
t "Confirmació"
DB=config/home-assistant_v2.db
MIDA=$(du -h "$DB" 2>/dev/null | cut -f1 || echo "?")
[ "$APAGAR" -eq 1 ] && echo "  Apagaré $MARCADOR."
echo "  Arxivaré la base de dades actual ($MIDA) i en començaré una de nova."
echo "  A partir d'aquest moment, la sèrie és la de debò."
echo
read -r -p "  Escriu COMENCA per continuar: " resposta
[ "$resposta" = "COMENCA" ] || { echo "  Avortat."; exit 1; }

# ── L'operació ─────────────────────────────────────────────────────────────
SEGELL=$(date +%Y%m%d-%H%M)
ARXIU=~/arxiu-experimentacio
mkdir -p "$ARXIU"

if [ "$APAGAR" -eq 1 ]; then
  t "Apagant el marcador de calibratge"
  # ABANS d'aturar, i per dues raons: el canvi on→off ha de quedar a la base
  # que s'arxiva, i HA ha de desar «off» a .storage en aturar-se, que és d'on
  # el restaurarà amb la base nova.
  curl -sf -m 15 -o /dev/null -X POST \
       -H "Authorization: Bearer $T" -H "Content-Type: application/json" \
       -d "{\"entity_id\": \"$MARCADOR\"}" "$HA/api/services/input_boolean/turn_off" \
    || { mal "no l'he pogut apagar. No he tocat res més."; exit 1; }
  for _ in $(seq 1 10); do
    m=$(estat "$MARCADOR"); [ "$m" = off ] && break; sleep 1
  done
  [ "$m" = off ] || { mal "continua «$m». No he tocat res més."; exit 1; }
  ok "apagat"
  # El recorder escriu a la base cada commit_interval segons. L'aturada neta
  # també ho buida, però no cal fiar-s'hi: s'espera un interval sencer.
  CI=$(sed -n 's/^ *commit_interval: *\([0-9][0-9]*\).*/\1/p' config/configuration.yaml | head -1)
  printf '  esperant %s s que el recorder ho desi…' "$(( ${CI:-30} + 5 ))"
  sleep $(( ${CI:-30} + 5 )); printf ' ✓\n'
fi

t "Aturant Home Assistant"
# Aturada NETA: si es mata el contenidor, SQLite queda sense tancar i la
# còpia del calibratge pot sortir amb el WAL a mitges.
docker compose stop >/dev/null 2>&1 && ok "aturat net" || { mal "no s'ha pogut aturar"; exit 1; }

t "Arxivant l'experimentació (hi és el calibratge)"
for f in "$DB" "$DB-wal" "$DB-shm"; do
  [ -f "$f" ] && cp -a "$f" "$ARXIU/$(basename "$f").$SEGELL" && ok "$(basename "$f") → $ARXIU"
done
gzip -f "$ARXIU/$(basename "$DB").$SEGELL" 2>/dev/null \
  && ok "comprimit: $(du -h "$ARXIU/$(basename "$DB").$SEGELL.gz" | cut -f1)"

t "Començant de zero"
rm -f "$DB" "$DB-wal" "$DB-shm" && ok "base de dades buidada"

docker compose start >/dev/null 2>&1 && ok "Home Assistant engegat" || { mal "no arrenca"; exit 1; }

printf '  esperant que respongui'
for _ in $(seq 1 30); do
  curl -s -o /dev/null -m 2 http://127.0.0.1:8123 && { printf ' ✓\n'; break; }
  printf '.'; sleep 5
done

# ── El marcador, un altre cop, ja amb la base nova ─────────────────────────
# HA el restaura de .storage/core.restore_state, que desa en aturar-se i cada
# 15 minuts. Una aturada que no hagi estat neta el pot tornar ENCÈS, i llavors
# la sèrie no començaria ara: no s'escriu cap data que no sigui certa.
m="?"
for _ in $(seq 1 12); do
  m=$(estat "$MARCADOR"); case "$m" in on|off) break ;; esac; sleep 5
done
if [ "$m" != off ]; then
  mal "$MARCADOR val «$m» amb la base nova: NO escric la data d'inici."
  cat <<MARCA

  L'experimentació ja és arxivada a $ARXIU i la base és nova.
  Comprova el marcador al tauler i, quan sigui «off», apunta l'inici a mà:

    date --iso-8601=seconds > config/.inici-serie

MARCA
  exit 1
fi
ok "$MARCADOR apagat, també amb la base nova"

# ── La data d'inici, escrita ───────────────────────────────────────────────
INICI=$(date --iso-8601=seconds)
echo "$INICI" > "$ARREL/config/.inici-serie"
t "Fet"
cat <<FI

  La sèrie probatòria comença el:  $INICI

  L'experimentació (i el calibratge) és a:  $ARXIU
  Aquella còpia NO és al repositori i no es perd amb la purga.

  Ara toca, i en aquest ordre:
    1. Apuntar la data d'inici a docs/domotica/home-assistant.md.
    2. Comprovar d'aquí a una hora que hi ha files noves:
         bash scripts/comprova.sh
    3. No tocar cap nom d'entitat mai més.

FI
