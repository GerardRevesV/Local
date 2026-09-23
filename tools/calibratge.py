#!/usr/bin/env python3
"""Calcula els desplaçaments de calibratge dels sensors a partir de l'històric.

QUÈ RESOL
─────────
Els cinc sensors T/HR no diuen el mateix dins del mateix aire. Com que la
decisió és una RESTA —ΔTd = Td_interior − Td_exterior— el que fa mal no és
l'error absolut de cadascun, sinó la diferència entre ells. Això ho mesura i
en treu una correcció.

    python3 tools/calibratge.py --prova           # tests, sense dades
    python3 tools/calibratge.py --csv dades.csv   # ajusta sobre un CSV
    python3 tools/calibratge.py --descarrega      # baixa l'històric i ajusta

El procediment de l'experiment és a docs/domotica/calibratge.md. Aquí només hi
ha el càlcul.

EL MÈTODE (revisat el 23/09/2026)
────────────────────────────────
Els Tapo donen l'HR en percentatges SENCERS i la T en dècimes, i Home Assistant
només enregistra quan el valor canvia. Un 1 % d'HR són ~0,2 °C de punt de
rosada. D'aquí surt tot:

  · Es parteix la finestra en BLOCS DE 20 MINUTS i se'n fa la mitjana: la
    mitjana d'un bloc veu per sota del gra, i el bloc és prou curt perquè el
    retard del hub no hi pesi. Ni un replà promitjat sencer (un sol punt) ni
    minut a minut sobre una rampa (pendents disparats, provat amb dades reals).
  · Es descarten els blocs on l'aire es mou més de 2 punts d'HR/hora: allà el
    retard entre sensors fabrica desviacions que semblen calibratge.
  · Per sensor, AJUST INVERS (el sensor en funció de la referència) i s'inverteix:
    així la quantització no aplana el pendent.
  · Es comprova contra l'ajust minut a minut, a tots dos extrems del rang.

El procediment i el perquè de cada xifra: docs/domotica/calibratge.md, secció
«Com s'ajusta la correcció, i on s'aplica». Els números van a
config/custom_templates/calibratge.jinja, que és l'ÚNIC lloc on viuen.

Surt amb codi 1 si l'ajust no es pot donar per bo.
"""

from __future__ import annotations

import ast
import bisect
import csv
import json
import random
import re
import os
import statistics as est
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from replica import cami_historic, punt_de_rosada  # noqa: E402  (Magnus i l'històric, sense duplicar-los)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Els cinc sensors, amb el nom curt que es fa servir als informes.
SENSORS = ("soterrani_fons", "soterrani_centre", "soterrani_gran", "baixa", "exterior")
MARCADOR = "input_boolean.mode_calibratge"

PAS_GRAELLA_S = 60          # remostreig a 1 minut
MIN_MOSTRES = 60            # menys d'una hora de rampa no és una rampa
MIN_RECORREGUT_HR = 20.0    # sense aquest recorregut no s'ajusta cap pendent
# ⚠️ Era 8, i era massa poc. Amb les dades reals del 21/09/2026 (HR 49–59 %,
#    10 punts de recorregut) s'ajustava un pendent que NO millorava gens
#    l'ajust —~0,25 °C amb pendent i sense— però que extrapolat
#    al 85 % de l'hivern inventava fins a 1,5 punts d'HR de correcció (~0,3 °C
#    de Td). Amb l'HR en enters, un pendent ajustat en 10 punts és soroll; i
#    el que fa mal no és el soroll dins del rang, sinó el que fa fora d'ell.
MAX_DISPERSIO_TD = 0.30     # °C — criteri d'acceptació (vegeu calibratge.md)
MINUTS_BLOC = 20            # el bloc que es promitja per fer un punt d'ajust
RITME_MAX_BLOC = 2.0        # punts d'HR/hora: per sobre, el retard entre sensors
                            # pesa més de 0,2 punts (~6 min × 2 punts/h)
MIN_BLOCS = 10              # menys blocs que això no és una recta, és un dibuix
GRA_T = 0.05                # °C — per sota d'això, un c_t és soroll i s'escriu 0
MAX_DESVIACIO_PENDENT = 0.10  # un pendent fora d'1 ± 0,10 és un sensor encallat


# ─────────────────────────────────────────────────────────────── dades ──────
def descarrega(hores: float) -> dict[str, list[tuple[datetime, str]]]:
    """Baixa l'històric de Home Assistant. URL i testimoni per variable d'entorn.

    No es posa cap adreça al repositori: és públic.

    ⚠️ Fins al 22/09/2026 la petició no portava «end_time» (vegeu
       replica.cami_historic), i HA en torna només 24 h des de l'inici. Amb les
       72 h per defecte, l'ajust es quedava les 24 h MÉS VELLES de la finestra i
       perdia les 48 més recents —les rampes de la caixa de sal i de la nevera—
       sense cap avís. Qualsevol calibratge tret amb --descarrega abans
       d'aquesta correcció s'ha de tornar a calcular.
    """
    base = os.environ.get("HA_URL", "").rstrip("/")
    testimoni = os.environ.get("HA_TOKEN", "")
    if not testimoni and os.environ.get("HA_TOKEN_FILE"):
        testimoni = Path(os.environ["HA_TOKEN_FILE"]).read_text(encoding="utf-8").strip()
    if not base or not testimoni:
        raise SystemExit(
            "Falten HA_URL i HA_TOKEN (o HA_TOKEN_FILE).\n"
            "  export HA_URL=http://<el-teu-servidor>:8123\n"
            "  export HA_TOKEN_FILE=~/.ha_token"
        )

    entitats = [f"sensor.{n}_temperatura" for n in SENSORS]
    entitats += [f"sensor.{n}_humitat" for n in SENSORS]
    entitats.append(MARCADOR)

    url = base + cami_historic(hores, entitats, "minimal_response")
    peticio = urllib.request.Request(url, headers={"Authorization": f"Bearer {testimoni}"})
    with urllib.request.urlopen(peticio, timeout=120) as resposta:
        cru = json.load(resposta)

    return interpreta(cru)


def interpreta(cru) -> dict[str, list[tuple[datetime, str]]]:
    """Passa la resposta de /api/history a {entitat: [(quan, estat)]}.

    ⚠️ Amb «minimal_response», Home Assistant posa l'entity_id NOMÉS al primer
       punt de cada sèrie; la resta només porten «state» i «last_changed».
       Comprovat el 21/09/2026: 1 punt de cada 8. Llegir l'entity_id de cada
       punt en descartaria set de cada vuit, en silenci, i el calibratge es
       quedaria sense dades just després de les 36 hores de prova.
    """
    sortida: dict[str, list[tuple[datetime, str]]] = {}
    for serie in cru:
        if not serie:
            continue
        ent = serie[0].get("entity_id")
        if ent is None:
            continue  # sèrie sense capçalera: no sabem de qui és
        for punt in serie:
            marca = punt.get("last_changed") or punt.get("last_updated")
            if marca is None or "state" not in punt:
                continue
            sortida.setdefault(ent, []).append((_quan(marca), punt["state"]))
    return sortida


def _quan(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def carrega_csv(cami: Path) -> dict[str, list[tuple[datetime, str]]]:
    """CSV amb capçalera: marca_temps,entity_id,estat."""
    sortida: dict[str, list[tuple[datetime, str]]] = {}
    with cami.open(encoding="utf-8", newline="") as fitxer:
        for fila in csv.DictReader(fitxer):
            sortida.setdefault(fila["entity_id"], []).append(
                (_quan(fila["marca_temps"]), fila["estat"])
            )
    return sortida


def desa_csv(dades: dict[str, list[tuple[datetime, str]]], cami: Path) -> None:
    with cami.open("w", encoding="utf-8", newline="") as fitxer:
        escriptor = csv.writer(fitxer)
        escriptor.writerow(["marca_temps", "entity_id", "estat"])
        for ent, punts in sorted(dades.items()):
            for quan, estat in punts:
                escriptor.writerow([quan.isoformat(), ent, estat])


# ───────────────────────────────────────────────────────── remostreig ───────
def trams_del_marcador(dades) -> list[tuple[datetime, datetime]]:
    """Els trams amb el marcador ENCÈS, un per un.

    ⚠️ No «del primer on a l'últim off»: si l'experiment es fa en dues tandes
       amb el marcador apagat entremig, allò d'entremig no és calibratge. Amb
       la repetició de l'hivern al soterrani passarà segur.
    Si l'últim tram no s'ha tancat, acaba a l'última dada que hi hagi.
    """
    punts = sorted(dades.get(MARCADOR, []))
    trams, inici = [], None
    for quan, estat in punts:
        if estat == "on" and inici is None:
            inici = quan
        elif estat == "off" and inici is not None:
            trams.append((inici, quan))
            inici = None
    if inici is not None:
        trams.append((inici, max(q for p in dades.values() for q, _ in p)))
    return trams


def finestra_de_calibratge(dades) -> tuple[datetime, datetime] | None:
    """Del primer encès a l'últim apagat: la graella. Els forats, a trams_del_marcador."""
    trams = trams_del_marcador(dades)
    return (trams[0][0], trams[-1][1]) if trams else None


def graella(dades, inici: datetime, fi: datetime, pas_s: int = PAS_GRAELLA_S):
    """Mostres alineades a una graella comuna, amb l'últim valor conegut.

    Home Assistant només enregistra els canvis, de manera que entre dos punts
    el valor vigent és l'anterior. Això no inventa res: reprodueix el que el
    sistema tenia per bo en aquell instant.
    """
    noms = [f"sensor.{n}_temperatura" for n in SENSORS] + [f"sensor.{n}_humitat" for n in SENSORS]
    series = {}
    for nom in noms:
        punts = []
        for quan, estat in sorted(dades.get(nom, [])):
            try:
                valor = float(estat)
            except ValueError:
                # ⚠️ «unavailable» o «unknown» és un FORAT, no un «no ha canviat».
                #    Saltar-lo feia que el valor d'abans seguís vigent: un sensor
                #    amb la bateria morta quedava CONGELAT com si fos viu mentre
                #    els altres pujaven, i l'ajust en treia una desviació enorme
                #    i falsa. Amb None, aquestes files queden fora.
                valor = None
            punts.append((quan, valor))
        series[nom] = punts

    files = []
    quan = inici
    index = {nom: 0 for nom in noms}
    vigent: dict[str, float | None] = {nom: None for nom in noms}
    while quan <= fi:
        for nom in noms:
            punts = series[nom]
            while index[nom] < len(punts) and punts[index[nom]][0] <= quan:
                vigent[nom] = punts[index[nom]][1]
                index[nom] += 1
        if all(v is not None for v in vigent.values()):
            files.append((quan, dict(vigent)))
        quan += timedelta(seconds=pas_s)
    return files


def rampes(files) -> dict[str, list]:
    """Parteix la finestra en tram de baixada i tram de pujada d'humitat.

    Es fa servir la MEDIANA dels cinc: un sensor sol podria anar al revés per
    soroll, la mediana no.
    """
    if not files:
        return {"baixada": [], "pujada": []}
    med = [est.median([f[1][f"sensor.{n}_humitat"] for n in SENSORS]) for f in files]
    # Suavitzat de 15 min perquè la quantització d'1 % no talli la rampa a trossos.
    finestra = max(1, 15 * 60 // PAS_GRAELLA_S)
    suau = [est.mean(med[max(0, i - finestra):i + 1]) for i in range(len(med))]
    baixada, pujada = [], []
    for i in range(1, len(files)):
        (baixada if suau[i] < suau[i - 1] else pujada).append(files[i])
    return {"baixada": baixada, "pujada": pujada}


# ──────────────────────────────────────────────────────────── l'ajust ───────
def _minims_quadrats(x: list[float], y: list[float]) -> tuple[float, float]:
    """y ≈ a·x + b. Retorna (a, b)."""
    n = len(x)
    mx, my = sum(x) / n, sum(y) / n
    sxx = sum((v - mx) ** 2 for v in x)
    if sxx == 0:
        return 1.0, my - mx
    sxy = sum((x[i] - mx) * (y[i] - my) for i in range(n))
    a = sxy / sxx
    return a, my - a * mx


def ajusta(files) -> dict[str, dict[str, float]]:
    """Per sensor: desplaçament de T, i pendent+desplaçament d'HR cap a la mediana."""
    if len(files) < MIN_MOSTRES:
        return {}
    resultat = {}
    for nom in SENSORS:
        t_sensor, t_med, h_sensor, h_med = [], [], [], []
        for _, valors in files:
            ts = [valors[f"sensor.{n}_temperatura"] for n in SENSORS]
            hs = [valors[f"sensor.{n}_humitat"] for n in SENSORS]
            t_sensor.append(valors[f"sensor.{nom}_temperatura"])
            h_sensor.append(valors[f"sensor.{nom}_humitat"])
            t_med.append(est.median(ts))
            h_med.append(est.median(hs))
        recorregut = max(h_sensor) - min(h_sensor)
        if recorregut >= MIN_RECORREGUT_HR:
            a, b = _minims_quadrats(h_sensor, h_med)
        else:
            # Sense recorregut, un pendent seria soroll disfressat de ciència.
            a, b = 1.0, est.mean([h_med[i] - h_sensor[i] for i in range(len(h_med))])
        resultat[nom] = {
            "c_t": est.mean([t_med[i] - t_sensor[i] for i in range(len(t_med))]),
            "c_rh_a": a,
            "c_rh_b": b,
            "recorregut_hr": recorregut,
            "pendent_ajustat": recorregut >= MIN_RECORREGUT_HR,
        }
    return resultat


def _ritme_mitjana(temps, mitjana, q0, minuts) -> float:
    """|pendent| (punts d'HR/hora) de la mitjana dels cinc, en una finestra de
    3 blocs centrada en el que comença a q0.

    ⚠️ Només es fia si els DOS veïns hi són gairebé sencers (≥ 75 % de files).
       Un bloc al costat d'un tram exclòs o d'un forat té la finestra coixa:
       el pendent es calcula amb un sol costat i pot semblar lent quan no ho
       és. Passava amb dades reals: el bloc de les 14:20 del 21/09 (just abans
       del sotrac) i el de les 13:00 del 23/09 (just després de la nevera)
       entraven a l'ajust amb 1,9 punts/h quan, amb la finestra sencera, en
       feien 2,1 i 3,5 (segona revisió, 23/09/2026). Sense veïns → infinit.
    """
    minim = 0.75 * minuts
    esq_i = bisect.bisect_left(temps, q0 - timedelta(minutes=minuts))
    esq_j = bisect.bisect_left(temps, q0)
    dre_i = bisect.bisect_left(temps, q0 + timedelta(minutes=minuts))
    dre_j = bisect.bisect_left(temps, q0 + timedelta(minutes=2 * minuts))
    if esq_j - esq_i < minim or dre_j - dre_i < minim:
        return float("inf")
    i = bisect.bisect_left(temps, q0 - timedelta(minutes=minuts))
    j = bisect.bisect_right(temps, q0 + timedelta(minutes=2 * minuts))
    xs = [(temps[k] - q0).total_seconds() / 3600 for k in range(i, j)]
    p, _ = _minims_quadrats(xs, mitjana[i:j])
    return abs(p)


def blocs(files, minuts: int = MINUTS_BLOC, ritme_max: float = RITME_MAX_BLOC) -> list[dict]:
    """Parteix la finestra en blocs de «minuts» i en fa la mitjana.

    QUÈ RESOL
    ─────────
    Un replà sencer promitjat dona UN punt: mil mostres al mateix 73 % no
    allarguen el recorregut. I ajustar minut a minut sobre una rampa és pitjor
    encara —comprovat amb les dades del 21/09: pendents de 0,81 a 1,23 segons
    el sensor— perquè el recorregut és curt, el retard hi pesa i, sobretot,
    l'error de quantització viu a la variable independent.

    Els blocs són el punt mig: mitjanes de 20 minuts repartides per TOTA la
    corba. La mitjana mata la quantització (dins d'un bloc l'HR es mou i els
    sensors creuen enters), i el bloc queda prou curt perquè el retard del hub
    no hi compti.

    ⚠️ ES DESCARTEN ELS BLOCS QUE ES MOUEN MASSA DE PRESSA. Mentre l'aire canvia,
       cada sensor va endarrerit el seu temps respecte dels altres (~6 min entre
       el més ràpid i el més lent, mesurat el 23/09), i això fabrica desviacions
       que semblen calibratge i són retard: error ≈ ritme × retard. Amb el
       llindar a 2 punts/hora, aquest error queda per sota de 0,2 punts.
       El ritme es mesura amb el pendent de la MITJANA dels cinc sobre 60 minuts
       (el bloc i un de cada costat). Revisat el 23/09/2026: abans es mirava
       el primer i l'últim minut de la mediana, que és un enter, i el tall real
       anava de 4 a 6 punts/hora segons on queia el graó; deixava passar el
       transitori de després de tancar el tàper (21/09, 12:40–14:20), amb fins
       a 6 punts de divergència entre sensors.
    """
    # ⚠️ Ordenat pel rellotge: si les files arriben partides per rampes, dins de
    #    cada bloc l'ordre no és el del rellotge. Amb les dades del 21–23/09
    #    això sol va arribar a canviar 91 blocs per 98.
    files = sorted(files, key=lambda f: f[0])
    temps = [q for q, _ in files]
    mitjana = [est.mean(v[f"sensor.{n}_humitat"] for n in SENSORS) for _, v in files]
    per_bloc: dict[int, list] = {}
    for quan, valors in files:
        clau = int(quan.timestamp()) // (minuts * 60)
        per_bloc.setdefault(clau, []).append((quan, valors))
    sortida = []
    for clau in sorted(per_bloc):
        tall = per_bloc[clau]
        if len(tall) < minuts * 0.75:        # bloc incomplet: forats de dades
            continue
        ritme = _ritme_mitjana(temps, mitjana, tall[0][0], minuts)
        if ritme > ritme_max:
            continue
        med = [est.median([v[f"sensor.{n}_humitat"] for n in SENSORS]) for _, v in tall]
        sortida.append({
            "quan": tall[0][0],
            "n": len(tall),
            "ritme": ritme,
            "hr": {n: est.mean([v[f"sensor.{n}_humitat"] for _, v in tall]) for n in SENSORS},
            "t": {n: est.mean([v[f"sensor.{n}_temperatura"] for _, v in tall]) for n in SENSORS},
            "ref": est.mean(med),
            "t_ref": est.mean([est.median([v[f"sensor.{n}_temperatura"] for n in SENSORS])
                               for _, v in tall]),
        })
    return sortida


def ajusta_blocs(llista: list[dict], forca_pendent: bool = False) -> dict[str, dict[str, float]]:
    """Per sensor, la recta HR_corregida = c_rh_a·HR + c_rh_b, ajustada pels blocs.

    ⚠️ L'AJUST ES FA AL REVÉS i després s'inverteix: es busca «sensor en funció
       de la referència» i no «referència en funció del sensor». Els mínims
       quadrats suposen que la variable independent no té error, i aquí el
       sensor en té —l'HR ve en enters—. Posant-lo com a dependent, el pendent
       deixa d'aplanar-se (dilució de la regressió).

    ⚠️ Un pendent lluny d'1 no és calibratge: és un sensor encallat. Un sensor
       clavat en un valor amb un sol salt d'un punt dona a = 32 (mesurat). Es
       marca amb «pendent_absurd» i l'informe el compta com a problema.
    """
    if len(llista) < MIN_BLOCS:
        return {}
    refs = [b["ref"] for b in llista]
    recorregut = max(refs) - min(refs)
    resultat = {}
    for nom in SENSORS:
        ys = [b["hr"][nom] for b in llista]
        desplacament = est.mean([refs[i] - ys[i] for i in range(len(ys))])
        mort = False
        if recorregut >= MIN_RECORREGUT_HR or forca_pendent:
            p, q = _minims_quadrats(refs, ys)      # sensor ≈ p·ref + q
            # Un sensor que NO es mou mentre la referència recorre 20 punts no
            # té un pendent de 1: està mort. Es marca, no es disfressa.
            mort = abs(p) < 1e-9
            a, b = (1.0, desplacament) if mort else (1 / p, -q / p)
        else:
            # Sense recorregut, un pendent seria soroll disfressat de ciència.
            a, b = 1.0, desplacament
        residus = [(a * ys[i] + b) - refs[i] for i in range(len(ys))]
        resultat[nom] = {
            "c_t": est.mean([b_["t_ref"] - b_["t"][nom] for b_ in llista]),
            "c_rh_a": a,
            "c_rh_b": b,
            "recorregut_hr": recorregut,
            "pendent_ajustat": recorregut >= MIN_RECORREGUT_HR,
            "pendent_absurd": mort or abs(a - 1.0) > MAX_DESVIACIO_PENDENT,
            "residu_max": max(abs(r) for r in residus),
            "blocs": len(llista),
        }
    return resultat


def desplegable(ajust: dict[str, dict[str, float]]) -> dict[str, dict[str, float]]:
    """El que de debò s'escriu a calibratge.jinja: arrodonit, i el c_t de soroll a zero.

    ⚠️ Totes les xifres de bondat es calculen amb AQUEST, no amb l'ajust cru. Si
       no, s'informa d'una correcció que no corre: amb els c_t de ±0,02 °C que
       surten de soroll, la dispersió publicada era 0,27 i la desplegada 0,28.
    """
    sortida = {}
    for nom, c in ajust.items():
        c2 = dict(c)
        c2["c_t"] = 0.0 if abs(c["c_t"]) < GRA_T else round(c["c_t"], 2)
        c2["c_rh_a"] = round(c["c_rh_a"], 4)
        c2["c_rh_b"] = round(c["c_rh_b"], 2)
        sortida[nom] = c2
    return sortida


def ajust_final(files) -> tuple[list[dict], dict[str, dict[str, float]]]:
    """L'ÚNIC camí de les files als números: el fan servir l'informe i els tests.

    ⚠️ Hi ha un sol camí a posta. Els tests en feien servir un altre (les files
       en ordre), l'informe li passava les rampes concatenades, i un error que
       només passava per un dels dos camins no el veia ningú.
    """
    llista = blocs(files)
    return llista, desplegable(ajusta_blocs(llista))


def correccio(c: dict[str, float], hr: float) -> float:
    """Quants punts suma la correcció a una lectura crua d'HR."""
    return c["c_rh_a"] * hr + c["c_rh_b"] - hr


def dispersio_td_blocs(llista: list[dict], correccions=None, percentil: float = 0.5) -> float:
    """La dispersió de Td entre els cinc, sobre les mitjanes de cada bloc.

    QUÈ HI GUANYA, I QUÈ NO
    ───────────────────────
    Promitjant blocs marxa el soroll de la quantització (±0,5 punts d'HR per
    lectura), però NO tot el que queda és gra: el terra teòric, amb un model
    perfecte i lectures en enters, és de ~0,13 °C per blocs i ~0,17 minut a
    minut (Monte Carlo, revisió del 23/09/2026). La resta és error sistemàtic
    que el model lineal no recull. I és una xifra DINS DE MOSTRA.
    """
    pitjor = []
    for b in llista:
        tds = []
        for nom in SENSORS:
            t, rh = b["t"][nom], b["hr"][nom]
            if correccions and nom in correccions:
                c = correccions[nom]
                t = t + c["c_t"]
                rh = rh * c["c_rh_a"] + c["c_rh_b"]
            tds.append(punt_de_rosada(t, min(max(rh, 1.0), 100.0)))
        pitjor.append(max(tds) - min(tds))
    if not pitjor:
        return float("nan")
    if percentil == 0.5:
        return est.median(pitjor)
    pitjor.sort()
    return pitjor[min(len(pitjor) - 1, int(percentil * len(pitjor)))]


def dispersio_td(files, correccions=None) -> float:
    """Dispersió màxima de punt de rosada entre els cinc, en mediana temporal."""
    per_fila = []
    for _, valors in files:
        tds = []
        for nom in SENSORS:
            t = valors[f"sensor.{nom}_temperatura"]
            rh = valors[f"sensor.{nom}_humitat"]
            if correccions and nom in correccions:
                c = correccions[nom]
                t = t + c["c_t"]
                rh = rh * c["c_rh_a"] + c["c_rh_b"]
            tds.append(punt_de_rosada(t, min(max(rh, 1.0), 100.0)))
        per_fila.append(max(tds) - min(tds))
    return est.median(per_fila) if per_fila else float("nan")


def incertesa(llista: list[dict], hr: float, reps: int = 400, llavor: int = 1,
              tros: int = 6) -> tuple[dict[str, float], float]:
    """Desviació típica de la correcció a «hr», per bootstrap de blocs MÒBILS.

    Retorna (1σ per sensor, fracció de rèpliques que es queden sense els 20
    punts de recorregut).

    Es remostregen trossos de «tros» blocs seguits (nominalment 2 hores), no
    blocs solts: els blocs veïns no són independents, i remostrejar-los d'un
    en un subestima la incertesa a la meitat (revisió del 23/09/2026).

    ⚠️ Cada rèplica s'ajusta SEMPRE amb pendent. Si no, les rèpliques que per
       atzar es queden sense recorregut canvien d'estimador (només
       desplaçament) i la desviació barreja dues coses: amb les dades del
       21–23/09 passava en una de cada quatre, i inflava la incertesa de fons
       de ±0,33 a ±0,49 (segona revisió). La fracció es retorna a part, perquè
       diu una cosa certa: que el pendent depèn de pocs blocs dels extrems.
    """
    rnd = random.Random(llavor)
    n = len(llista)
    trossos = [llista[i:i + tros] for i in range(0, max(1, n - tros + 1))]
    mostres: dict[str, list[float]] = {nom: [] for nom in SENSORS}
    curtes = 0
    for _ in range(reps):
        nova = []
        while len(nova) < n:
            nova.extend(rnd.choice(trossos))
        nova = nova[:n]
        refs = [b["ref"] for b in nova]
        curtes += (max(refs) - min(refs)) < MIN_RECORREGUT_HR
        aj = ajusta_blocs(nova, forca_pendent=True)
        if not aj:
            continue
        for nom in SENSORS:
            mostres[nom].append(correccio(aj[nom], hr))
    sd = {nom: (est.pstdev(v) if len(v) > 1 else float("nan")) for nom, v in mostres.items()}
    return sd, curtes / reps


def linies_jinja(final: dict[str, dict[str, float]], rang_hr, rang_t, versio: str) -> list[str]:
    """Les línies que van a config/custom_templates/calibratge.jinja."""
    linies = [f"{{%- set VERSIO = '{versio}' -%}}", "{%- set CALIBRATGE = {"]
    for nom in SENSORS:
        c = final[nom]
        clau = f"'{nom}':"
        linies.append(f"      {clau:<19} {{'a': {c['c_rh_a']:.4f}, 'b': {c['c_rh_b']:5.2f}, "
                      f"'t': {c['c_t']:.2f}}},")
    linies.append("    } -%}")
    linies.append(f"{{%- set RANG_HR = [{rang_hr[0]:.1f}, {rang_hr[1]:.1f}] -%}}")
    linies.append(f"{{%- set RANG_T = [{rang_t[0]:.1f}, {rang_t[1]:.1f}] -%}}")
    return linies


# ───────────────────────────────────────────────────────────── informe ──────
def informe(files, versio: str | None = None) -> int:
    """Escriu l'informe i retorna quants problemes hi ha. 0 = es pot aplicar.

    EL QUE DECIDEIX (compta com a problema)
      · que hi hagi prou blocs
      · que cap pendent sigui absurd (sensor encallat)
      · la dispersió de Td PER BLOCS, amb la correcció desplegable, ≤ 0,30 °C
      · que blocs i minut a minut coincideixin, a tots dos extrems del rang
    EL QUE NOMÉS INFORMA
      · la dispersió minut a minut (hi pesa el gra de la mesura)
      · la comparació entre la rampa de pujada i la de baixada
    """
    problemes = 0
    if len(files) < MIN_MOSTRES:
        print(f"⚠ Només {len(files)} mostres: calen {MIN_MOSTRES}.")
        return 1

    llista, final = ajust_final(files)
    print(f"\n── Blocs de {MINUTS_BLOC} min: {len(llista)} utilitzables "
          f"(descartats els que es mouen més de {RITME_MAX_BLOC:g} punts d'HR/hora)")
    if not final:
        print(f"   ⚠ calen {MIN_BLOCS} blocs i no hi són: no hi ha calibratge.")
        return problemes + 1
    refs = [b["ref"] for b in llista]
    baix, alt = min(refs), max(refs)
    print(f"   referència de {baix:.1f} a {alt:.1f} % ({alt - baix:.0f} punts de recorregut)")
    if alt - baix < MIN_RECORREGUT_HR:
        print(f"   ⚠ sense {MIN_RECORREGUT_HR:.0f} punts de recorregut no s'ajusta cap pendent")

    for nom in SENSORS:
        if final[nom]["pendent_absurd"]:
            print(f"   ⚠ {nom}: pendent {final[nom]['c_rh_a']:.3f}, sensor encallat? NO s'aplica")
            problemes += 1

    # Dos mètodes independents: si no diuen el mateix, no te'n fiïs. A TOTS DOS
    # extrems: al mig, dues rectes s'assemblen sempre.
    per_minut = ajusta(files)
    print("\n── Blocs contra minut a minut (la prova de si el número és de fiar)")
    print(f"   sensor              correcció al {baix:.0f} %      al {alt:.0f} %")
    for nom in SENSORS:
        cb, cm = final[nom], per_minut[nom]
        d = [(correccio(cb, x), correccio(cm, x)) for x in (baix, alt)]
        marca = "  ⚠" if any(abs(p - q) > 1.0 for p, q in d) else ""
        print(f"   {nom:18} {d[0][0]:+6.2f} / {d[0][1]:+6.2f}    "
              f"{d[1][0]:+6.2f} / {d[1][1]:+6.2f}{marca}")
        if marca:
            problemes += 1

    # Només informa: la pujada i la baixada, comparades a una HR COMUNA. (Abans
    # es comparaven les ordenades a l'origen, que són la correcció al 0 %.)
    parts = rampes(files)
    if all(len(parts[r]) >= MIN_MOSTRES for r in parts):
        mig = (baix + alt) / 2
        aj_r = {r: ajusta(parts[r]) for r in parts}
        print(f"\n── Pujada contra baixada, al {mig:.0f} % (només informa)")
        for nom in SENSORS:
            v = [correccio(aj_r[r][nom], mig) for r in ("baixada", "pujada")]
            print(f"   {nom:18} {v[0]:+6.2f} / {v[1]:+6.2f}")

    ab_b, de_b = dispersio_td_blocs(llista), dispersio_td_blocs(llista, final)
    ab_m, de_m = dispersio_td(files), dispersio_td(files, final)
    print("\n── Dispersió de Td entre els cinc, amb la correcció que es desplega")
    print(f"   per blocs:      {ab_b:.2f} → {de_b:.2f} °C   (objectiu ≤ {MAX_DISPERSIO_TD:.2f})")
    print(f"   minut a minut:  {ab_m:.2f} → {de_m:.2f} °C   (només informa: hi pesa el gra)")
    print(f"   per blocs, p90: {dispersio_td_blocs(llista, percentil=0.9):.2f} → "
          f"{dispersio_td_blocs(llista, final, percentil=0.9):.2f} °C")
    print("   per franges d'HR (la mediana global la pot aguantar una sola franja):")
    for des, fins in ((45, 60), (60, 70), (70, 80)):
        tros = [b for b in llista if des <= b["ref"] < fins]
        if tros:
            print(f"     {des}–{fins} %: {len(tros):3} blocs · "
                  f"{dispersio_td_blocs(tros):.2f} → {dispersio_td_blocs(tros, final):.2f} °C")
    if de_b > MAX_DISPERSIO_TD:
        print("   ⚠ per blocs, per sobre de l'objectiu: el llindar ΔTd s'ha de quedar alt")
        problemes += 1

    print("\n── Incertesa de la correcció fora del rang (bootstrap de blocs de 2 h, 1σ)")
    for hr in (85.0, 90.0):
        sd, curtes = incertesa(llista, hr)
        print(f"   al {hr:.0f} %: " + "  ".join(f"{n.split('_')[-1]} ±{sd[n]:.2f}" for n in SENSORS))
    print(f"   ({curtes * 100:.0f} % de les rèpliques es queden sense {MIN_RECORREGUT_HR:.0f} punts de "
          "recorregut: el pendent depèn de pocs blocs dels extrems)")

    t_ref = [b["t_ref"] for b in llista]
    rang_hr = (round(baix, 1), round(alt, 1))
    rang_t = (round(min(t_ref), 1), round(max(t_ref), 1))
    if problemes:
        print(f"\n── ⚠ {problemes} problemes: aquest ajust NO s'ha d'enganxar enlloc.")
        return problemes
    if not versio:
        print("\n   ⚠ Falta --versio AAAA-MM-DD: sense versió, no se sabrà quines files de "
              "l'històric es van calcular amb aquests números.")
    print("\n── Per enganxar a config/custom_templates/calibratge.jinja "
          "(l'ÚNIC lloc on viuen els números)")
    for linia in linies_jinja(final, rang_hr, rang_t, versio or "AAAA-MM-DD"):
        print("   " + linia)
    for nom in SENSORS:
        if not final[nom]["pendent_ajustat"]:
            print(f"   # {nom}: sense recorregut, només desplaçament")
    return problemes


# ─────────────────────────────────────────────────────────────── tests ──────
def _sintetic(desplacaments, pas_hr=0.12, quantitza=True):
    """Sensors inventats amb un error conegut, per comprovar que el recuperem.

    Simula el que passa de debò: HR en enters, T en dècimes, i una rampa que
    baixa del 80 % al 45 % i torna a pujar.
    """
    files = []
    t0 = datetime(2026, 9, 21, tzinfo=timezone.utc)
    baixada = [80 - pas_hr * i for i in range(300)]
    # La pujada arrenca on ha acabat la baixada: aixi amb pas_hr=0 tot queda
    # PLA de debo, que es el cas que ha de refusar l'ajust del pendent.
    valors_hr = baixada + [baixada[-1] + pas_hr * i for i in range(300)]
    for i, hr_real in enumerate(valors_hr):
        valors = {}
        for nom, (dt, dh) in desplacaments.items():
            t = 21.0 + dt
            rh = hr_real + dh
            if quantitza:
                t = round(t, 1)
                rh = float(round(rh))
            valors[f"sensor.{nom}_temperatura"] = t
            valors[f"sensor.{nom}_humitat"] = rh
        files.append((t0 + timedelta(seconds=PAS_GRAELLA_S * i), valors))
    return files


def _sintetic_recta(veritat, hores=24.0, soroll=0.0, llavor=1):
    """Sensors amb error de PENDENT i desplaçament, sobre una pujada lenta.

    Cada sensor llegeix r tal que a·r + b = x, amb x l'HR de l'aire: és a dir,
    la lectura crua que caldria corregir amb (a, b). Quantitzada a enters, com
    els Tapo. Amb «soroll» (desviació típica, en punts) s'hi suma un soroll
    gaussià ABANS de quantitzar, que és el que fa que la mitjana d'un bloc
    pugui veure per sota del gra.
    """
    rnd = random.Random(llavor)
    files = []
    t0 = datetime(2026, 9, 21, tzinfo=timezone.utc)
    n = int(hores * 60)
    for i in range(n):
        x = 48.0 + 27.0 * i / n                    # 48 → 75 % en «hores»
        valors = {}
        for nom, (a, b) in veritat.items():
            cru = (x - b) / a + (rnd.gauss(0.0, soroll) if soroll else 0.0)
            valors[f"sensor.{nom}_humitat"] = float(round(cru))
            valors[f"sensor.{nom}_temperatura"] = round(26.0 + 0.5 * i / n, 1)
        files.append((t0 + timedelta(seconds=PAS_GRAELLA_S * i), valors))
    return files


ARREL = Path(__file__).resolve().parent.parent
CSV_REAL = ARREL / "docs/domotica/dades/calibratge-2026-09.csv"
JINJA_REAL = ARREL / "config/custom_templates/calibratge.jinja"
# La tanda del 21–23/09/2026, tal com es va analitzar (vegeu calibratge.md). La
# finestra acaba a l'última dada del CSV (13:33): més enllà, la graella
# arrossegaria valors sense cap lectura al darrere.
FINESTRA_REAL = ("2026-09-21T00:43+02:00", "2026-09-23T13:33+02:00")
EXCLOSOS_REALS = [("2026-09-21T11:26+02:00", "2026-09-21T12:39+02:00"),   # entre tandes, a la mà
                  ("2026-09-21T14:50+02:00", "2026-09-21T15:35+02:00"),   # el sotrac del tàper
                  ("2026-09-22T12:45+02:00", "2026-09-23T13:00+02:00")]   # la nevera: gradients
BLOCS_REALS = 84     # fixat: si canvia, ha canviat el mètode o les dades, i s'ha de saber


def llegeix_jinja(text: str) -> dict:
    """El que diu calibratge.jinja: CALIBRATGE, VERSIO, RANG_HR i RANG_T.

    ⚠️ Es llegeix el diccionari sencer amb ast.literal_eval, i abans es treuen
       els comentaris {# … #}. Amb una expressió regular, un exemple al
       comentari de capçalera («ABANS: 'soterrani_fons': {'a': 0.9399…») o una
       segona definició més avall es llegien EN COMPTES dels bons (comprovat a
       la revisió del 23/09/2026). I si hi ha dues definicions, és un error:
       Jinja es queda l'última i qui llegeix el fitxer, la primera.
    """
    net = re.sub(r"\{#.*?#\}", "", text, flags=re.S)
    sortida = {}
    for nom in ("CALIBRATGE", "VERSIO", "RANG_HR", "RANG_T"):
        trobats = re.findall(rf"\{{%-?\s*set\s+{nom}\s*=\s*(.*?)\s*-?%\}}", net, flags=re.S)
        if len(trobats) != 1:
            raise ValueError(f"calibratge.jinja: {nom} hi és {len(trobats)} vegades, n'ha de ser una")
        sortida[nom] = ast.literal_eval(trobats[0])
    return sortida


def calibratge_del_repo() -> dict[str, dict[str, float]]:
    """Els números que hi ha a custom_templates/calibratge.jinja, que és el que corre."""
    cal = llegeix_jinja(JINJA_REAL.read_text(encoding="utf-8"))["CALIBRATGE"]
    return {nom: {"c_rh_a": float(c["a"]), "c_rh_b": float(c["b"]), "c_t": float(c["t"])}
            for nom, c in cal.items()}


def _files_reals():
    """Les files de la tanda de debò, del CSV del repositori: el mateix camí que main()."""
    return files_de(carrega_csv(CSV_REAL), [(_quan(FINESTRA_REAL[0]), _quan(FINESTRA_REAL[1]))],
                    [(_quan(a), _quan(b)) for a, b in EXCLOSOS_REALS])


def _bloc(ref, hr_per_sensor, t=26.0):
    """Un bloc fet a mà, amb la forma que retorna blocs()."""
    return {"quan": None, "n": 20, "ritme": 0.0, "ref": ref, "t_ref": t,
            "hr": dict(hr_per_sensor), "t": {n: t for n in SENSORS}}


def tests() -> int:
    ok = True

    def prop(nom, condicio, detall=""):
        nonlocal ok
        ok &= bool(condicio)
        print(f"  {'OK  ' if condicio else 'FALLA'} {nom}" + (f"   ({detall})" if detall else ""))

    print("Mínims quadrats")
    a, b = _minims_quadrats([1, 2, 3, 4], [3, 5, 7, 9])
    prop("recupera y = 2x + 1", abs(a - 2) < 1e-9 and abs(b - 1) < 1e-9, f"a={a:.3f} b={b:.3f}")

    print("\nMinut a minut: recupera un error conegut (amb quantització d'1 % com la real)")
    reals = {"soterrani_fons": (0.0, 0.0), "soterrani_centre": (0.3, -2.0),
             "soterrani_gran": (-0.2, 1.5), "baixa": (0.0, 0.0), "exterior": (0.1, -1.0)}
    files = _sintetic(reals)
    res = ajusta(files)
    for nom, (dt, dh) in reals.items():
        prop(f"{nom}: desplaçament d'HR ≈ {-dh:+.1f}",
             abs(res[nom]["c_rh_b"] - (-dh)) < 0.6, f"obtingut {res[nom]['c_rh_b']:+.2f}")
        prop(f"{nom}: desplaçament de T ≈ {-dt:+.1f}",
             abs(res[nom]["c_t"] - (-dt)) < 0.15, f"obtingut {res[nom]['c_t']:+.2f}")
    abans, despres = dispersio_td(files), dispersio_td(files, res)
    prop("i la dispersió de Td baixa dins de l'objectiu", despres < abans and despres <= MAX_DISPERSIO_TD,
         f"{abans:.2f} → {despres:.2f} °C")

    print("\nSense recorregut no s'inventa cap pendent")
    res_plans = ajusta(_sintetic(reals, pas_hr=0.0))
    prop("minut a minut: cap pendent, i a = 1",
         not any(r["pendent_ajustat"] for r in res_plans.values())
         and all(r["c_rh_a"] == 1.0 for r in res_plans.values()))
    curt = ajusta(_sintetic(reals, pas_hr=10 / 300))
    prop("minut a minut: amb 10 punts d'HR, tampoc",
         not any(r["pendent_ajustat"] for r in curt.values()))
    # La mateixa guarda, però a l'ajust PER BLOCS, que és el que es desplega.
    llista_curta = blocs(_sintetic(reals, pas_hr=0.02))           # ~6 punts de recorregut
    aj_curt = ajusta_blocs(llista_curta)
    prop("per blocs: amb ~6 punts, a = 1 i només desplaçament",
         bool(aj_curt) and all(r["c_rh_a"] == 1.0 and not r["pendent_ajustat"] for r in aj_curt.values()),
         f"{len(llista_curta)} blocs")
    # La mediana dels desplaçaments (0, −2, +1,5, 0, −1) és 0: la referència és
    # l'aire de debò, i el desplaçament ha de ser el contrari de l'error.
    prop("i el desplaçament és el contrari de l'error de cada sensor",
         bool(aj_curt) and all(abs(aj_curt[n]["c_rh_b"] + reals[n][1]) < 0.3 for n in SENSORS),
         " ".join(f"{n.split('_')[-1]} {aj_curt[n]['c_rh_b']:+.2f}" for n in SENSORS) if aj_curt else "")

    print("\nBlocs: el filtre de ritme")
    # Rampes MONÒTONES de 27 punts: en «hores» hores, el ritme és 27/hores.
    # (Una rampa en V no serveix per provar-ho: al vèrtex el ritme és zero.)
    identitat = {n: (1.0, 0.0) for n in SENSORS}
    for hores, esperat, etiqueta in ((24.0, "tots", "1,1 punts/h, es queden"),
                                     (9.0, "cap", "3 punts/h, fora (> 2)"),
                                     (1.5, "cap", "18 punts/h, fora")):
        f_ = _sintetic_recta(identitat, hores=hores)
        n_blocs, n_complets = len(blocs(f_)), len(blocs(f_, ritme_max=float("inf")))
        # Els dos blocs de les puntes no tenen veí a un costat: poden sortir
        # amb un ritme estimat de menys o no sortir. No compten.
        prop(etiqueta, (n_blocs >= n_complets - 2) if esperat == "tots" else n_blocs == 0,
             f"{n_blocs} de {n_complets}")

    print("\nBlocs: sense els dos veïns sencers, el ritme no es fia")
    f_ = _sintetic_recta({n: (1.0, 0.0) for n in SENSORS}, hores=24.0)
    tots_b = blocs(f_)
    forat_a, forat_b = f_[400][0], f_[460][0]         # 60 minuts fora, al mig
    amb_forat = [f for f in f_ if not (forat_a <= f[0] <= forat_b)]
    b_forat = blocs(amb_forat)

    def _trepitja(des, fins):          # minuts d'un interval que cauen dins del forat
        return max(0.0, (min(fins, forat_b) - max(des, forat_a)).total_seconds() / 60)
    m = timedelta(minutes=MINUTS_BLOC)
    coixos = [b for b in b_forat
              if _trepitja(b["quan"] - m, b["quan"]) > 5 or _trepitja(b["quan"] + m, b["quan"] + 2 * m) > 5]
    prop("cap bloc acceptat té un veí que trepitgi el tram exclòs", not coixos and len(b_forat) < len(tots_b),
         f"{len(tots_b)} blocs sencers → {len(b_forat)} amb el forat; {len(coixos)} coixos")

    print("\nBlocs: l'ordre de les files no hi fa res")
    # ⚠️ L'error del 23/09: l'informe passava les files partides per rampes, i
    #    blocs() llegia el ritme del primer i l'últim de cada bloc tal com
    #    venien. Aquest test falla si es treu l'ordenació.
    f_ = _sintetic(reals, pas_hr=0.02)
    barrejades = list(f_)
    random.Random(7).shuffle(barrejades)
    b1, b2 = blocs(f_), blocs(barrejades)
    prop("les mateixes files barrejades donen els mateixos blocs",
         len(b1) == len(b2) and all(abs(x["ref"] - y["ref"]) < 1e-12
                                    and x["hr"] == y["hr"] for x, y in zip(b1, b2)),
         f"{len(b1)} / {len(b2)} blocs")
    parts_ = rampes(f_)
    b3 = blocs(parts_["baixada"] + parts_["pujada"])
    prop("i partides per rampes, com les passava l'informe, també", len(b3) == len(blocs(f_[1:])),
         f"{len(b3)} blocs")

    print("\nL'ajust per blocs és INVERS, i es nota")
    # Sensor = p·ref + q + soroll, amb un soroll de ±3 que no té res a veure amb
    # la referència. L'ajust invers recupera 1/p; el directe (ref en funció del
    # sensor) surt aplanat, que és l'error que l'invers existeix per evitar.
    p_real, q_real = 1.05, -2.0
    blocs_inv = []
    for k in range(200):
        ref = 48.0 + 27.0 * k / 199
        soroll = 3.0 if k % 2 else -3.0
        hr = {n: ref for n in SENSORS}
        hr["soterrani_fons"] = p_real * ref + q_real + soroll
        blocs_inv.append(_bloc(ref, hr))
    aj_inv = ajusta_blocs(blocs_inv)["soterrani_fons"]
    refs_ = [b["ref"] for b in blocs_inv]
    ys_ = [b["hr"]["soterrani_fons"] for b in blocs_inv]
    a_directe, _ = _minims_quadrats(ys_, refs_)
    prop("l'invers recupera el pendent", abs(aj_inv["c_rh_a"] - 1 / p_real) < 0.01,
         f"{aj_inv['c_rh_a']:.4f} (1/p = {1 / p_real:.4f})")
    prop("i el directe hauria sortit aplanat més d'un 10 %",
         a_directe < 0.9 / p_real, f"{a_directe:.4f}")

    print("\nL'ajust per blocs posa els cinc d'acord (amb soroll i sota el gra)")
    # ⚠️ L'eina calibra contra la MEDIANA DELS CINC, no contra l'aire de debò:
    #    el que es pot exigir no és que torni els (a, b) «veritables», sinó que,
    #    un cop corregits, els cinc diguin el mateix entre ells. En aquest joc
    #    la mediana va desplaçada ~0,3 punts de l'aire, i per això un test que
    #    comparés contra la veritat fallaria sense que l'eina fes res mal.
    veritat = {"soterrani_fons": (0.95, 5.0), "soterrani_centre": (0.96, 0.9),
               "soterrani_gran": (1.03, -1.4), "baixa": (1.00, -1.2), "exterior": (1.0, 0.3)}
    for llavor in (1, 2, 3, 4, 5):
        aj_s = ajusta_blocs(blocs(_sintetic_recta(veritat, soroll=0.3, llavor=llavor)))
        rati = [aj_s[n]["c_rh_a"] / veritat[n][0] for n in SENSORS]

        def _separacio_a(x):
            vals = [aj_s[n]["c_rh_a"] * (x - veritat[n][1]) / veritat[n][0] + aj_s[n]["c_rh_b"]
                    for n in SENSORS]
            return max(vals) - min(vals)
        dins = max(_separacio_a(x) for x in (55.0, 65.0, 73.0))
        fora = _separacio_a(90.0)
        # Tolerància: 1,5–2× el pitjor de 5 llavors. 0,15 punts d'HR són
        # ~0,03 °C de Td; al 90 %, ja extrapolant, se n'admet el doble.
        prop(f"llavor {llavor}: pendents coherents, i corregits coincideixen",
             max(rati) - min(rati) < 0.01 and dins < 0.15 and fora < 0.30,
             f"a/a_real ±{max(rati) - min(rati):.4f} · dins {dins:.3f} · al 90 % {fora:.3f} punts")

    print("\nLa T: un error propi es recupera, i el soroll s'escriu zero")
    amb_t = {"soterrani_fons": (0.3, 0.0), "soterrani_centre": (0.02, 0.0),
             "soterrani_gran": (0.0, 0.0), "baixa": (0.0, 0.0), "exterior": (0.0, 0.0)}
    aj_t = ajusta_blocs(blocs(_sintetic(amb_t, pas_hr=0.02, quantitza=False)))
    des_t = desplegable(aj_t)
    prop("fons llegeix 0,3 °C de més → c_t ≈ −0,3", abs(aj_t["soterrani_fons"]["c_t"] + 0.3) < 0.03,
         f"{aj_t['soterrani_fons']['c_t']:+.3f}")
    prop("i es desplega amb el signe bo", des_t["soterrani_fons"]["c_t"] == -0.3 * 1 or
         abs(des_t["soterrani_fons"]["c_t"] + 0.3) < 0.03, f"{des_t['soterrani_fons']['c_t']:+.2f}")
    prop("centre, 0,02 °C: soroll, s'escriu 0", des_t["soterrani_centre"]["c_t"] == 0.0,
         f"{aj_t['soterrani_centre']['c_t']:+.3f} → {des_t['soterrani_centre']['c_t']}")
    llista_t = blocs(_sintetic(amb_t, pas_hr=0.02, quantitza=False))
    prop("i aplicada, la dispersió de Td baixa (el signe és el bo)",
         dispersio_td_blocs(llista_t, des_t) < dispersio_td_blocs(llista_t) / 2,
         f"{dispersio_td_blocs(llista_t):.3f} → {dispersio_td_blocs(llista_t, des_t):.3f} °C")

    print("\nUn sensor encallat no es converteix en un pendent")
    # Clavat a 72, amb un sol salt a 73 a mig recorregut: la recta que en surt
    # té a ≈ 30. És un sensor espatllat, no un calibratge.
    blocs_enc = []
    for k in range(40):
        ref = 50.0 + 24.0 * k / 39
        hr = {n: ref for n in SENSORS}
        hr["soterrani_gran"] = 72.0 if k < 20 else 73.0
        blocs_enc.append(_bloc(ref, hr))
    aj_enc = ajusta_blocs(blocs_enc)
    prop("es marca com a absurd", aj_enc["soterrani_gran"]["pendent_absurd"],
         f"a = {aj_enc['soterrani_gran']['c_rh_a']:.1f}")
    prop("i els altres no", not any(aj_enc[n]["pendent_absurd"] for n in SENSORS if n != "soterrani_gran"))
    blocs_mort = [_bloc(b["ref"], {**b["hr"], "soterrani_gran": 72.0}) for b in blocs_enc]
    aj_mort = ajusta_blocs(blocs_mort)
    prop("un sensor que no es mou gens també es marca (no es disfressa de pendent 1)",
         aj_mort["soterrani_gran"]["pendent_absurd"], f"a = {aj_mort['soterrani_gran']['c_rh_a']}")

    print("\nLa incertesa per bootstrap")
    llista_i = blocs(_sintetic_recta(veritat, soroll=0.3, llavor=2))
    sd_i, curtes_i = incertesa(llista_i, 85.0, reps=60)
    prop("dona una desviació positiva i finita per a cada sensor",
         all(0 < sd_i[n] < 5 for n in SENSORS), " ".join(f"{sd_i[n]:.3f}" for n in SENSORS))
    prop("i diu quantes rèpliques es queden sense recorregut", 0.0 <= curtes_i <= 1.0, f"{curtes_i:.2f}")
    sd_mes, _ = incertesa(llista_i, 95.0, reps=60)
    prop("i creix com més lluny del rang", all(sd_mes[n] >= sd_i[n] for n in SENSORS if n != "exterior"))

    print("\nEl muntatge de les files: extrems dels exclosos inclosos, i sense duplicats")
    t0_ = datetime(2026, 9, 21, tzinfo=timezone.utc)
    d_ = {f"sensor.{n}_{m}": [(t0_, "50.0")] for n in SENSORS for m in ("temperatura", "humitat")}
    ff = files_de(d_, [(t0_, t0_ + timedelta(minutes=30)), (t0_ + timedelta(minutes=20), t0_ + timedelta(minutes=40))],
                  [(t0_ + timedelta(minutes=10), t0_ + timedelta(minutes=15))])
    temps_ff = [f[0] for f in ff]
    prop("dos trams que es trepitgen no dupliquen files", len(temps_ff) == len(set(temps_ff)),
         f"{len(temps_ff)} files")
    prop("i els extrems de l'exclòs queden fora (10 i 15 inclosos)",
         t0_ + timedelta(minutes=10) not in temps_ff and t0_ + timedelta(minutes=15) not in temps_ff
         and t0_ + timedelta(minutes=16) in temps_ff and len(temps_ff) == 41 - 6)

    print("\nEl marcador: trams encesos, un per un")
    t0 = datetime(2026, 9, 21, tzinfo=timezone.utc)
    dades = {MARCADOR: [(t0, "off"), (t0 + timedelta(hours=1), "on"), (t0 + timedelta(hours=37), "off")]}
    prop("un tram", trams_del_marcador(dades) == [(t0 + timedelta(hours=1), t0 + timedelta(hours=37))])
    dades2 = {MARCADOR: [(t0, "on"), (t0 + timedelta(hours=2), "off"),
                         (t0 + timedelta(hours=5), "on"), (t0 + timedelta(hours=8), "off")]}
    trams2 = trams_del_marcador(dades2)
    prop("dos trams: el forat d'entremig queda fora", len(trams2) == 2
         and trams2[0][1] == t0 + timedelta(hours=2) and trams2[1][0] == t0 + timedelta(hours=5),
         f"{len(trams2)} trams")
    dades3 = {MARCADOR: [(t0, "on")], "sensor.x": [(t0 + timedelta(hours=3), "1")]}
    prop("sense apagar: acaba a l'última dada", trams_del_marcador(dades3) == [(t0, t0 + timedelta(hours=3))])
    prop("i sense marcador, cap", trams_del_marcador({}) == [] and finestra_de_calibratge({}) is None)

    print("\ncalibratge.jinja es llegeix sencer i sense trampes")
    bo = ("{#- ABANS: 'soterrani_fons': {'a': 0.9399, 'b': 5.70, 't': 0.0} -#}\n"
          "{%- set VERSIO = '2026-09-23' -%}\n"
          "{%- set CALIBRATGE = {\n  'soterrani_fons': {'a': 0.95, 'b': 5.0, 't': 0.0},\n} -%}\n"
          "{%- set RANG_HR = [49.0, 73.0] -%}\n{%- set RANG_T = [26.0, 29.6] -%}\n")
    llegit = llegeix_jinja(bo)
    prop("un exemple dins d'un comentari no es llegeix", llegit["CALIBRATGE"]["soterrani_fons"]["a"] == 0.95)
    doble = bo + "{%- set CALIBRATGE = {'soterrani_fons': {'a': 1.0, 'b': 0.0, 't': 0.0}} -%}\n"
    try:
        llegeix_jinja(doble)
        prop("dues definicions són un error", False)
    except ValueError:
        prop("dues definicions són un error", True)

    print("\nEl que escriu l'informe és el que s'ha calculat")
    import contextlib
    import io
    f_ = _sintetic_recta(veritat, soroll=0.3, llavor=1)
    sortida = io.StringIO()
    with contextlib.redirect_stdout(sortida):
        codi = informe(f_, "2026-01-01")
    text = sortida.getvalue()
    tros = text[text.index("{%- set VERSIO"):]
    tros = "\n".join(l.strip() for l in tros.splitlines() if l.strip().startswith(("{%", "'", "}")))
    del_text = {n: {"c_rh_a": c["a"], "c_rh_b": c["b"], "c_t": c["t"]}
                for n, c in llegeix_jinja(tros)["CALIBRATGE"].items()}
    _, final_ = ajust_final(f_)
    prop("les línies per enganxar són les de l'ajust",
         all(abs(del_text[n]["c_rh_a"] - final_[n]["c_rh_a"]) < 1e-9
             and abs(del_text[n]["c_rh_b"] - final_[n]["c_rh_b"]) < 1e-9 for n in SENSORS))
    prop("i porten la versió i el rang", "'2026-01-01'" in text and "RANG_HR" in text)
    prop("i no diuen res de rosada.yaml", "set c_rh_a" not in text)

    print("\nL'eina també sap dir que NO (codi ≠ 0)")
    import random as _r
    soroll = _r.Random(3)
    dolentes = []
    for q, v in _sintetic_recta(veritat, soroll=0.3, llavor=1):
        v = dict(v)
        v["sensor.soterrani_gran_humitat"] = float(round(v["sensor.soterrani_gran_humitat"] + soroll.gauss(0, 6)))
        dolentes.append((q, v))
    with contextlib.redirect_stdout(io.StringIO()) as sortida_no:
        codi_no = informe(dolentes, "2026-01-01")
    prop("un sensor amb 6 punts de soroll fa fallar el criteri de dispersió", codi_no > 0,
         f"{codi_no} problemes")
    prop("i llavors no escriu cap línia per enganxar",
         "set CALIBRATGE" not in sortida_no.getvalue())
    encallades = [(q, {**v, "sensor.baixa_humitat": 60.0}) for q, v in f_]
    with contextlib.redirect_stdout(io.StringIO()):
        codi_enc = informe(encallades, "2026-01-01")
    prop("un sensor encallat també", codi_enc > 0, f"{codi_enc} problemes")

    # ── LES DADES DE DEBÒ ─────────────────────────────────────────────────
    # ⚠️ Obligatòries: si falten, FALLA. Abans es saltaven en silenci, i amb el
    #    CSV esborrat la meitat dels errors possibles passaven sense avís.
    print("\nLES DADES DE DEBÒ (docs/domotica/dades/calibratge-2026-09.csv)")
    if not (CSV_REAL.exists() and JINJA_REAL.exists()):
        prop("hi ha el CSV i calibratge.jinja", False, "en falta algun")
    else:
        files_r = _files_reals()
        llista, final = ajust_final(files_r)
        refs = [b["ref"] for b in llista]
        prop(f"exactament {BLOCS_REALS} blocs, com a l'anàlisi del 23/09", len(llista) == BLOCS_REALS,
             f"{len(llista)} blocs")
        prop("i el recorregut permet ajustar pendent", max(refs) - min(refs) >= MIN_RECORREGUT_HR,
             f"{min(refs):.1f}–{max(refs):.1f} %")

        jinja = llegeix_jinja(JINJA_REAL.read_text(encoding="utf-8"))
        repo = calibratge_del_repo()
        for nom in SENSORS:
            iguals = (repo[nom]["c_rh_a"] == final[nom]["c_rh_a"]
                      and repo[nom]["c_rh_b"] == final[nom]["c_rh_b"]
                      and repo[nom]["c_t"] == final[nom]["c_t"])
            prop(f"{nom}: el fitxer és exactament el que surt de les dades", iguals,
                 f"jinja {repo[nom]['c_rh_a']:.4f}/{repo[nom]['c_rh_b']:+.2f}/{repo[nom]['c_t']} · "
                 f"dades {final[nom]['c_rh_a']:.4f}/{final[nom]['c_rh_b']:+.2f}/{final[nom]['c_t']}")
        t_ref = [b["t_ref"] for b in llista]
        prop("i el rang de validesa escrit és el de les dades",
             jinja["RANG_HR"] == [round(min(refs), 1), round(max(refs), 1)]
             and jinja["RANG_T"] == [round(min(t_ref), 1), round(max(t_ref), 1)],
             f"jinja {jinja['RANG_HR']} {jinja['RANG_T']}")

        with contextlib.redirect_stdout(io.StringIO()):
            codi_real = informe(files_r)
        prop("l'eina dona l'ajust per bo (codi 0), amb els criteris que decideixen", codi_real == 0,
             f"{codi_real} problemes")

        abans, despres = dispersio_td_blocs(llista), dispersio_td_blocs(llista, repo)
        prop("dispersió de Td per blocs, amb el que es desplega, dins de l'objectiu",
             despres <= MAX_DISPERSIO_TD and despres < abans / 2, f"{abans:.2f} → {despres:.2f} °C")

        # En HR: el llindar no és a ull, surt del criteri. 0,30 °C de Td són
        # tants punts d'HR com digui Magnus a les condicions de la prova.
        dtd_per_punt = punt_de_rosada(27.0, 61.0) - punt_de_rosada(27.0, 60.0)
        llindar_hr = MAX_DISPERSIO_TD / dtd_per_punt
        seps = [max(b["hr"][n] * repo[n]["c_rh_a"] + repo[n]["c_rh_b"] for n in SENSORS)
                - min(b["hr"][n] * repo[n]["c_rh_a"] + repo[n]["c_rh_b"] for n in SENSORS)
                for b in llista]
        prop(f"en HR s'ajunten dins de {llindar_hr:.2f} punts (= {MAX_DISPERSIO_TD} °C de Td)",
             est.median(seps) < llindar_hr, f"mediana {est.median(seps):.2f} punts")

        print("\nEXTRAPOLACIÓ: que la recta no es desbordi fora del rang mesurat")
        for nom in SENSORS:
            c = repo[nom]
            creix = correccio(c, 90.0) - correccio(c, 73.0)
            prop(f"{nom}: del 73 al 90 %, la correcció no creix més d'1,5 punts",
                 abs(creix) <= 1.5 and abs(c["c_rh_a"] - 1.0) <= 0.07,
                 f"{correccio(c, 73.0):+.2f} → {correccio(c, 90.0):+.2f} · a = {c['c_rh_a']:.4f}")
        a_100 = max(100.0 * repo[n]["c_rh_a"] + repo[n]["c_rh_b"] for n in SENSORS)
        prop("una lectura de 100 % no passa del 102 abans de retallar", a_100 <= 102.0, f"{a_100:.2f}")
        # Les mateixes dades, totes 15 punts amunt. Suposa que l'error NO canvia
        # amb l'HR (i el model diu que sí): per això només s'exigeix que no ho
        # empitjori. I s'informa en Td a la temperatura del soterrani a l'hivern.
        for desplacament in (+15.0, -15.0):
            crus = [[min(max(b["hr"][n] + desplacament, 1.0), 100.0) for n in SENSORS] for b in llista]
            cor = [[v * repo[n]["c_rh_a"] + repo[n]["c_rh_b"] for v, n in zip(fila, SENSORS)]
                   for fila in crus]
            m_cru = est.median(max(f) - min(f) for f in crus)
            m_cor = est.median(max(f) - min(f) for f in cor)
            td_hivern = est.median(max(punt_de_rosada(12.0, min(v, 100.0)) for v in f)
                                   - min(punt_de_rosada(12.0, min(v, 100.0)) for v in f) for f in cor)
            prop(f"{desplacament:+.0f} punts: no els separa més que sense corregir", m_cor < m_cru,
                 f"{m_cru:.2f} → {m_cor:.2f} punts · a 12 °C, {td_hivern:.2f} °C de Td")

    print("\nEls trams exclosos es llegeixen bé de la línia d'ordres")
    fr = _franges_excloses(["--exclou", "2026-09-21T14:54+02:00/2026-09-21T15:30+02:00"])
    prop("una franja, i el fus es respecta (12:54–13:30 UTC)",
         len(fr) == 1
         and fr[0][0] == datetime(2026, 9, 21, 12, 54, tzinfo=timezone.utc)
         and fr[0][1] == datetime(2026, 9, 21, 13, 30, tzinfo=timezone.utc),
         f"{fr[0][0].isoformat()} → {fr[0][1].isoformat()}" if fr else "cap")
    prop("i sense --exclou no n'hi ha cap", _franges_excloses(["--csv", "x.csv"]) == [])

    print("\nLes rampes es parteixen bé")
    parts = rampes(files)
    prop("hi ha baixada i pujada", len(parts["baixada"]) > 100 and len(parts["pujada"]) > 100,
         f"{len(parts['baixada'])} / {len(parts['pujada'])}")

    print("\nHistoric de minimal_response, interpretat sencer")
    cru = [[
        {"entity_id": "sensor.x", "state": "50.0",
         "last_changed": "2026-09-21T00:00:00+00:00",
         "last_updated": "2026-09-21T00:00:00+00:00", "attributes": {}},
        {"state": "51.0", "last_changed": "2026-09-21T00:15:00+00:00"},
        {"state": "52.0", "last_changed": "2026-09-21T00:30:00+00:00"},
    ], []]
    llegit = interpreta(cru)
    prop("no perd els punts que no porten entity_id",
         len(llegit.get("sensor.x", [])) == 3,
         f"{len(llegit.get('sensor.x', []))} de 3 llegits")
    prop("i una serie buida no peta", list(llegit) == ["sensor.x"])

    print("\nL'històric es demana sencer, amb el final explícit")
    ara = datetime(2026, 9, 22, 12, 0, tzinfo=timezone.utc)
    url = cami_historic(72, ["sensor.x", MARCADOR], "minimal_response", ara=ara)
    parts_url = urllib.parse.urlsplit(url)
    consulta = urllib.parse.parse_qs(parts_url.query, keep_blank_values=True)
    fins = consulta.get("end_time", [None])[0]
    inici = _quan(urllib.parse.unquote(parts_url.path.rsplit("/", 1)[1]))
    prop("porta end_time, i és ara (sense, HA en torna només 24 h)",
         fins is not None and _quan(fins) == ara, fins or "no hi és")
    prop("l'inici és 72 h abans, en UTC", inici == ara - timedelta(hours=72), inici.isoformat())
    prop("cap «+» cru, que arribaria com un espai", "+" not in url)
    prop("i minimal_response hi segueix", "minimal_response" in consulta)

    print("\nUn sensor que cau no queda congelat")
    t0 = datetime(2026, 9, 21, tzinfo=timezone.utc)
    caigut = {f"sensor.{n}_{m}": [(t0, "50.0")] for n in SENSORS for m in ("temperatura", "humitat")}
    caigut["sensor.soterrani_fons_humitat"] += [(t0 + timedelta(minutes=30), "unavailable"),
                                              (t0 + timedelta(minutes=60), "51.0")]
    files_c = graella(caigut, t0, t0 + timedelta(minutes=90))
    durant = [f for f in files_c if t0 + timedelta(minutes=30) <= f[0] < t0 + timedelta(minutes=60)]
    prop("els minuts sense dada queden fora", len(durant) == 0, f"{len(durant)} files mentre estava caigut")
    prop("i quan torna, torna a comptar", len(files_c) == 61, f"{len(files_c)} de 61")

    print()
    print("Tots els tests passen." if ok else "HI HA TESTS QUE FALLEN.")
    return 0 if ok else 1


# ───────────────────────────────────────────────────────────────── main ─────
def files_de(dades, trams, exclosos=()) -> list:
    """Les files de l'ajust: la graella de cada tram, sense els exclosos (extrems
    inclosos) i sense duplicats si dos trams es trepitgen. La fan servir main()
    i els tests, perquè no hi hagi dos camins."""
    per_hora = {}
    for inici, fi in trams:
        for fila in graella(dades, inici, fi):
            per_hora[fila[0]] = fila
    files = [per_hora[q] for q in sorted(per_hora)]
    for a, b in exclosos:
        files = [f for f in files if not (a <= f[0] <= b)]
    return files


def _franja(argv: list[str], opcio: str) -> list[tuple[datetime, datetime]]:
    """«opcio INICI/FI», repetible. Marques ISO amb fus.

    --exclou són els trams que NO entren a l'ajust: el sotrac de qui mou el
    recipient, el tram dins d'una nevera amb gradients... Queden a l'històric
    —són dades—, però no fan calibratge.

    --finestra substitueix el marcador, i només s'hauria de fer servir per als
    trams antics que es van mesurar sense encendre'l.
    """
    franges = []
    for i, arg in enumerate(argv):
        if arg != opcio:
            continue
        des, _, fins = argv[i + 1].partition("/")
        if not fins:
            raise SystemExit(f"{opcio} vol INICI/FI, per exemple "
                             "2026-09-21T14:54+02:00/2026-09-21T15:30+02:00")
        franges.append((_quan(des), _quan(fins)))
    return franges


def _franges_excloses(argv: list[str]) -> list[tuple[datetime, datetime]]:
    return _franja(argv, "--exclou")


def main(argv: list[str]) -> int:
    if "--prova" in argv or len(argv) == 0:
        return tests()

    if "--csv" in argv:
        dades = carrega_csv(Path(argv[argv.index("--csv") + 1]))
    elif "--descarrega" in argv:
        hores = 72.0
        if "--hores" in argv:
            hores = float(argv[argv.index("--hores") + 1])
        dades = descarrega(hores)
        desti = Path("calibratge-cru.csv")
        desa_csv(dades, desti)
        print(f"Històric desat a {desti} ({sum(len(v) for v in dades.values())} punts)")
    else:
        print(__doc__)
        return 1

    manual = _franja(argv, "--finestra")
    if manual:
        trams = manual
        print("⚠ Finestra donada a mà: el marcador no mana. Només per a trams antics\n"
              "  que es van fer sense encendre'l (la primera tanda, 21/09/2026).")
    else:
        trams = trams_del_marcador(dades)
        if not trams:
            print(f"No hi ha cap tram amb {MARCADOR} encès. L'experiment s'ha de marcar.")
            return 1
    for inici, fi in trams:
        print(f"Finestra de calibratge: {inici.isoformat()} → {fi.isoformat()}")
    exclosos = _franges_excloses(argv)
    tots = files_de(dades, trams)
    files = files_de(dades, trams, exclosos)
    print(f"{len(tots)} mostres d'un minut amb els deu sensors alhora; "
          f"{len(tots) - len(files)} dins de trams exclosos")

    versio = argv[argv.index("--versio") + 1] if "--versio" in argv else None
    return 1 if informe(files, versio) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
