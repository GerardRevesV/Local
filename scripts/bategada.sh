#!/usr/bin/env bash
#
# bategada.sh — el senyal de vida del servidor, cap a healthchecks.io.
#
#   bash scripts/bategada.sh             envia una bategada ara (és el que fa el cron)
#   bash scripts/bategada.sh --mostra    imprimeix el cos que enviaria, sense enviar res
#   bash scripts/bategada.sh --falla     envia una FALLADA a posta, per provar el correu
#   bash scripts/bategada.sh --instala   la programa a la crontab de l'usuari
#
# QUÈ AVISA (decisio-stack.md, «La bategada, tal com s'ha muntat»). Cada 30 min
# s'envia el mateix cos a DOS checks:
#   · «bategada» (marge 3 h) rep SEMPRE un «/0». Només vigila el silenci: si en
#     deixen d'arribar, correu «DOWN» amb el cos de l'ÚLTIM que va arribar —
#     màquina apagada, sense llum o sense xarxa. Cotxe, probablement.
#   · «estat» (marge 1 dia) rep «/<codi>»: es posa vermell, amb correu al
#     moment, mentre hi hagi un ✗ —la màquina és viva i s'hi pot entrar per
#     SSH—, i torna a verd, amb un altre correu, quan s'arregla.
# Per què dos: healthchecks.io només avisa quan un check CANVIA d'estat. Amb un
# de sol, un ✗ que durés el deixaria en vermell, i la mort de la màquina
# passaria sense correu.
#
# L'estat NO es calcula aquí: és «comprova.sh --breu». Una sola llista del que
# ha d'estar bé, per mirar-ho a mà i per a l'avís. Aquí només s'ordena, s'envia
# i es recorda el que no ha pogut sortir.
#
# ⚠️ Les URL dels checks són SECRETES —amb elles qualsevol pot fer callar l'avís—
#    i aquest repositori és públic: viuen a ~/.bategada_url i ~/.estat_url,
#    permisos 600, fora de git. El check «nit» (nit.py) seguirà el mateix
#    conveni: ~/.nit_url.

set -uo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
URL_BAT=~/.bategada_url
URL_EST=~/.estat_url
ESTAT=${XDG_STATE_HOME:-$HOME/.local/state}/bategada
PERDUDES=$ESTAT/perdudes      # una línia per bategada que no ha pogut sortir
MODE=${1:-}

case "$MODE" in
  ""|--mostra|--falla|--instala) ;;
  *) echo "Ús: bash scripts/bategada.sh [--mostra | --falla | --instala]" >&2; exit 2 ;;
esac

# L'URL neta, o res si no n'hi ha o no té la forma d'una URL. Sense espais ni
# barra final («…//0» és un 404), i sense cometes ni barres inverses: va dins
# d'una línia de «--config», i curl se les menjaria sense dir res.
llegeix_url(){
  [ -s "$1" ] || return 1
  local u; u=$(tr -d '[:space:]' < "$1"); u=${u%/}
  [[ "$u" =~ ^https?://[A-Za-z0-9._:/-]+$ ]] || return 1
  printf '%s' "$u"
}

# ─────────────────────────────────────────────────────────────── instal·lar ──
# Minuts 7 i 37: no a l'hora en punt, que és quan hi envia tothom, i lluny de
# les 03:40 de nit.py. @reboot: la primera surt en arrencar (el guió mateix
# espera que HA hagi tingut temps d'aixecar-se), i el correu de tornada ja
# porta un temps d'engegada curt.
#
# Cron d'usuari i no un temporitzador de systemd: no demana sudo, i el que el
# temporitzador aporta de més —recuperar les passades perdudes— aquí seria
# mentir. Una bategada que no surt perquè la màquina era apagada és justament
# el senyal.
if [ "$MODE" = --instala ]; then
  if ! llegeix_url "$URL_BAT" >/dev/null; then
    echo "Falta l'URL del check «bategada», o no té forma d'URL. Enganxa-la així" >&2
    echo "(Enter i Ctrl-D per acabar):   (umask 077; cat > ~/.bategada_url)" >&2
    exit 2
  fi
  chmod 600 "$URL_BAT"
  if llegeix_url "$URL_EST" >/dev/null; then
    chmod 600 "$URL_EST"
  else
    echo "⚠ Falta ~/.estat_url: sense ella la bategada surt, però un ✗ no enviarà cap correu." >&2
  fi

  # ⚠️ Si «crontab -l» falla per una cosa que no sigui «no n'hi ha cap», s'ha
  #    de plantar aquí: seguir voldria dir instal·lar NOMÉS les línies de sota
  #    i esborrar la resta de la crontab sense dir res.
  if ! actual=$(crontab -l 2>&1); then
    case "$actual" in
      *"no crontab for"*) actual="" ;;
      *) echo "No puc llegir la crontab ($actual). No toco res." >&2; exit 2 ;;
    esac
  fi
  if ! {
    [ -n "$actual" ] && printf '%s\n' "$actual" | grep -vF 'bategada.sh'
    echo "# Avís de caiguda (healthchecks.io). El posa «bash scripts/bategada.sh --instala»."
    echo "7,37 * * * * bash $DIR/bategada.sh 2>&1 | logger -t bategada"
    echo "@reboot bash $DIR/bategada.sh 2>&1 | logger -t bategada"
  } | crontab -; then
    echo "«crontab -» ha fallat: la bategada NO ha quedat programada." >&2
    exit 2
  fi
  echo "Programada. La crontab queda així:"
  crontab -l
  exit 0
fi

# ─────────────────────────────────────────────────────────────────── estat ──
# Just després d'arrencar, HA encara no respon: una bategada dels primers
# segons —el @reboot, o un minut 7 o 37 que hi caigui— seria un ✗ fals.
# HA triga uns 36 s; s'espera fins als 150 s d'engegada.
engegada=$(cut -d. -f1 /proc/uptime 2>/dev/null || echo 999)
[ "${engegada:-999}" -lt 150 ] 2>/dev/null && sleep $(( 150 - engegada ))

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

url_bat=$(llegeix_url "$URL_BAT")
url_est=$(llegeix_url "$URL_EST")
[ -n "$url_est" ] || cos="$cos
⚠ falta ~/.estat_url, o no té forma d'URL: un ✗ NO envia cap correu"

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
# al mòbil i les primeres línies són les que compten. «-e» i no «[✗⚠·]»: en un
# locale C, una classe amb caràcters multibyte són bytes solts.
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
if [ -z "$url_bat" ]; then
  echo "Falta ~/.bategada_url, o no té forma d'URL: no sé on enviar la bategada (vegeu --instala)" >&2
  exit 2
fi
mkdir -p "$ESTAT"

# Els dos checks en UNA crida de curl i una sola connexió: el segon no paga un
# altre establiment de TLS per la SIM. Les URL entren per l'entrada estàndard
# («--config -») i no com a argument, que es veuria amb «ps»; per això el cos
# va per fitxer. Cada tram porta totes les opcions: «next» les reinicia.
f=$(mktemp); trap 'rm -f "$f"' EXIT
printf '%s\n' "$cos" > "$f"
tram(){
  printf 'url = "%s"\ndata-binary = "@%s"\nheader = "%s"\noutput = "/dev/null"\nwrite-out = "%s"\nmax-time = 20\nretry = 3\nsilent\nshow-error\n' \
    "$1" "$f" 'Content-Type: text/plain; charset=utf-8' '%{http_code}\n'
}
respostes=$(
  {
    tram "$url_bat/0"
    [ -n "$url_est" ] && { echo next; tram "$url_est/$codi"; }
  } | curl --config -
); r=$?
h_bat=$(sed -n 1p <<<"$respostes")
h_est=$(sed -n 2p <<<"$respostes")

if [ "$h_bat" != 200 ]; then
  grep -q '^✗ SENSE CORRENT' <<<"$cos" && corrent=bateria || corrent=xarxa
  echo "$ara $corrent" >> "$PERDUDES"
  echo "NO enviada (HTTP ${h_bat:-000}, curl $r): $cap" >&2
  exit 1
fi
echo "$(date +%s) $codi" > "$ESTAT/darrera"
rm -f "$PERDUDES"
if [ -n "$url_est" ] && [ "$h_est" != 200 ]; then
  echo "enviada, però l'ESTAT no ha arribat (HTTP ${h_est:-000}): $cap" >&2
  exit 1
fi
echo "enviada: $cap"
