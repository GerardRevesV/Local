#!/usr/bin/env bash
#
# bategada.sh — el senyal de vida del servidor, cap a healthchecks.io.
#
#   bash scripts/bategada.sh             envia una bategada ara (és el que fa el cron)
#   bash scripts/bategada.sh --mostra    imprimeix el cos que enviaria, sense enviar res
#   bash scripts/bategada.sh --falla     envia una FALLADA a posta, per provar el correu
#   bash scripts/bategada.sh --instala   la programa a la crontab de l'usuari
#
# QUÈ AVISA (decisio-stack.md, «Supervisió de vida»). El check «bategada» espera
# un ping cada 30 min, amb 3 h de marge:
#   · si en deixen d'arribar  → correu «DOWN», que porta el cos de l'ÚLTIM que
#     va arribar: màquina apagada, sense llum o sense xarxa. Cotxe, probablement.
#   · si n'arriba un de FALLADA → correu en el moment, amb el que falla: la
#     màquina és viva i hi pots entrar per SSH.
#
# L'estat NO es calcula aquí: és «comprova.sh --breu». Una sola llista del que
# ha d'estar bé, per mirar-ho a mà i per a l'avís. Aquí només s'ordena, s'envia
# i es recorda el que no ha pogut sortir.
#
# ⚠️ L'URL del check és un SECRET —amb ella qualsevol pot fer callar l'avís— i
#    aquest repositori és públic: viu a ~/.bategada_url, permisos 600, fora de
#    git. El check «nit» (nit.py) seguirà el mateix conveni: ~/.nit_url.

set -uo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
URL_FITXER=~/.bategada_url
ESTAT=${XDG_STATE_HOME:-$HOME/.local/state}/bategada
PERDUDES=$ESTAT/perdudes      # una línia per bategada que no ha pogut sortir
MODE=${1:-}

case "$MODE" in
  ""|--mostra|--falla|--instala) ;;
  *) echo "Ús: bash scripts/bategada.sh [--mostra | --falla | --instala]" >&2; exit 2 ;;
esac

# ─────────────────────────────────────────────────────────────── instal·lar ──
# Minuts 7 i 37: no a l'hora en punt, que és quan hi envia tothom, i lluny de
# les 03:40 de nit.py. @reboot: la primera surt 2 min després d'arrencar —HA en
# triga uns 36 s— i el correu de tornada ja diu, per l'«up», que ha reiniciat.
#
# Cron d'usuari i no un temporitzador de systemd: no demana sudo, i el que el
# temporitzador aporta de més —recuperar les passades perdudes— aquí seria
# mentir. Una bategada que no surt perquè la màquina era apagada és justament
# el senyal. Tornar-la a llançar en arrencar és el que fa el @reboot, i prou.
if [ "$MODE" = --instala ]; then
  if [ ! -s "$URL_FITXER" ]; then
    echo "Falta l'URL del check. Enganxa-la així (Ctrl-D per acabar):" >&2
    echo "    (umask 077; cat > ~/.bategada_url)" >&2
    exit 2
  fi
  chmod 600 "$URL_FITXER"
  {
    crontab -l 2>/dev/null | grep -vF 'bategada.sh'
    echo "# Avís de caiguda (healthchecks.io). El posa «bash scripts/bategada.sh --instala»."
    echo "7,37 * * * * bash $DIR/bategada.sh 2>&1 | logger -t bategada"
    echo "@reboot sleep 120 && bash $DIR/bategada.sh 2>&1 | logger -t bategada"
  } | crontab -
  echo "Programada. La crontab queda així:"
  crontab -l
  exit 0
fi

# ─────────────────────────────────────────────────────────────────── estat ──
# «timeout»: si docker es penja, comprova.sh es penjaria amb ell i la bategada
# callaria. Millor enviar que s'ha penjat, que ja és un diagnòstic.
cos=$(timeout -k 10 120 bash "$DIR/comprova.sh" --breu 2>&1); codi=$?
case "$codi" in
  124|137) cos="✗ comprova.sh no ha acabat en 2 minuts: docker o HA penjats?
$cos" ;;
esac
if [ "$MODE" = --falla ]; then
  codi=1
  cos="✗ PROVA: fallada enviada a mà amb «bategada.sh --falla». No passa res.
$cos"
fi

# Les bategades que no van poder sortir. Si n'hi ha, la màquina era VIVA
# mentre no se la sentia: el que va caure va ser la xarxa (o la llum, si
# anava amb bateria). És la diferència entre un forat a les dades i cap forat.
silenci=""
if [ -s "$PERDUDES" ]; then
  np=$(wc -l < "$PERDUDES")
  nbat=$(grep -c ' bateria$' "$PERDUDES")
  silenci="⚠ $np bategada(es) SENSE SORTIR des del $(head -1 "$PERDUDES" | cut -d' ' -f1-2): la màquina era viva, però no arribava a healthchecks.io"
  [ "$nbat" -gt 0 ] && silenci="$silenci, $nbat amb BATERIA (va caure la llum)"
fi

ara=$(date '+%d/%m %H:%M')
if [ "$codi" = 0 ]; then
  cap="OK · $ara"
else
  cap="FALLA · $ara · $(grep -c '^✗' <<<"$cos") cosa(es) per mirar"
fi

# Primer el veredicte i el que falla, després les dades: el correu es llegeix
# al mòbil i les primeres línies són les que compten. «-e» i no «[✗⚠·]»: el
# cron corre sense LANG, i en locale C una classe amb multibyte són bytes solts.
cos=$(
  printf '%s\n' "$cap"
  [ -n "$silenci" ] && printf '%s\n' "$silenci"
  grep -e '^✗' <<<"$cos"
  grep -e '^⚠' <<<"$cos"
  grep -e '^·' <<<"$cos"
  grep -v -e '^✗' -e '^⚠' -e '^·' -e '^$' <<<"$cos"
)
cos=$(head -n 60 <<<"$cos")    # un error desbocat no ha de fer un cos de 100 kB

if [ "$MODE" = --mostra ]; then
  printf '%s\n' "$cos"
  echo "(codi $codi — NO s'ha enviat)"
  exit 0
fi

# ────────────────────────────────────────────────────────────────── enviar ──
if [ ! -s "$URL_FITXER" ]; then
  echo "Falta $URL_FITXER: no sé on enviar la bategada (vegeu --instala)" >&2
  exit 2
fi
url=$(tr -d ' \r\n' < "$URL_FITXER")
mkdir -p "$ESTAT"

# «/<codi>» és l'endpoint de healthchecks.io per codi de sortida: 0 és bé,
# qualsevol altre és una fallada. L'URL entra per l'entrada estàndard
# («--config -») i no com a argument: els arguments de qualsevol procés es
# veuen amb «ps». Per això el cos va per fitxer.
f=$(mktemp); trap 'rm -f "$f"' EXIT
printf '%s\n' "$cos" > "$f"
if printf 'url = "%s/%s"\n' "$url" "$codi" | curl -fsS -m 20 --retry 3 -o /dev/null \
     -H 'Content-Type: text/plain; charset=utf-8' --data-binary @"$f" --config -; then
  echo "$(date +%s) $codi" > "$ESTAT/darrera"
  rm -f "$PERDUDES"
  echo "enviada: $cap"
else
  r=$?
  grep -q '^✗ SENSE CORRENT' <<<"$cos" && corrent=bateria || corrent=xarxa
  echo "$ara $corrent" >> "$PERDUDES"
  echo "NO enviada (curl $r): $cap" >&2
  exit 1
fi
