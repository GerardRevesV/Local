#!/usr/bin/env bash
#
# inicia-serie.sh — el pas d'experimentació a la sèrie de debò.
#
#   bash scripts/inicia-serie.sh --de-debo
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

set -uo pipefail

ARREL="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." 2>/dev/null && pwd)"
[ -f "${ARREL:-}/docker-compose.yml" ] || {
  echo "Executa'l des de dins del repositori." >&2; exit 2; }
cd "$ARREL"

ok(){   printf '  \033[32m✓\033[0m %s\n' "$*"; }
mal(){  printf '  \033[31m✗\033[0m %s\n' "$*"; }
t(){    printf '\n\033[1;34m── %s\033[0m\n' "$*"; }

if [ "${1:-}" != "--de-debo" ]; then
  cat <<'AJUDA'

  inicia-serie.sh — tanca l'experimentació i comença la sèrie probatòria.

  Arxiva la base de dades actual (que conté el calibratge) i en comença una
  de nova, amb data d'inici escrita.

  ABANS D'EXECUTAR-LO, ha d'estar tot això fet:

    · Els sensors, al seu lloc DEFINITIU del local.
    · Els noms d'entitat fixats i renombrats. Canviar-ne un després
      parteix la sèrie.
    · Els offsets de calibratge calculats i aplicats a packages/rosada.yaml.
    · El deshumidificador amb desguàs continu i l'endoll P110 al seu lloc.

  Si tot això hi és:   bash scripts/inicia-serie.sh --de-debo

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

# ── 2. Cap sensor mort ─────────────────────────────────────────────────────
# Començar la sèrie amb un sensor caigut vol dir un forat des del dia u,
# i el dia u és precisament el que es mirarà.
TOK=~/.ha_token
if [ -r "$TOK" ]; then
  T=$(tr -d '\n\r' < "$TOK")
  morts=$(curl -s -m 15 -H "Authorization: Bearer $T" \
            http://127.0.0.1:8123/api/states \
          | python3 -c '
import sys, json
mal = []
for e in json.load(sys.stdin):
    i = e["entity_id"]
    if i.startswith(("sensor.soterrani", "sensor.exterior", "sensor.planta_baixa")) \
       and e["state"] in ("unavailable", "unknown", "sense_dades"):
        mal.append(i)
print("\n".join(mal))' 2>/dev/null)
  if [ -n "$morts" ]; then
    mal "hi ha sensors sense lectura vàlida:"
    printf '%s\n' "$morts" | sed 's/^/      /'
    PROBLEMES=$((PROBLEMES+1))
  else
    ok "tots els sensors del local reporten"
  fi
else
  mal "sense ~/.ha_token: no puc comprovar els sensors"
  PROBLEMES=$((PROBLEMES+1))
fi

# ── 3. L'arbre de git, net ─────────────────────────────────────────────────
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
echo "  Arxivaré la base de dades actual ($MIDA) i en començaré una de nova."
echo "  A partir d'aquest moment, la sèrie és la de debò."
echo
read -r -p "  Escriu COMENCA per continuar: " resposta
[ "$resposta" = "COMENCA" ] || { echo "  Avortat."; exit 1; }

# ── L'operació ─────────────────────────────────────────────────────────────
SEGELL=$(date +%Y%m%d-%H%M)
ARXIU=~/arxiu-experimentacio
mkdir -p "$ARXIU"

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
