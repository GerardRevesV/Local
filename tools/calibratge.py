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

EL GRA DE LA MESURA MANA
────────────────────────
Els Tapo donen l'HR en percentatges SENCERS i la T en dècimes, i Home Assistant
només enregistra quan el valor canvia. Un 1 % d'HR són ~0,2 °C de punt de
rosada: amb l'aire quiet, els cinc sensors es queden clavats en un enter i no
se'n pot treure res més fi.

Per això l'experiment són RAMPES LENTES i no replans: en una rampa cada sensor
creua el 60→61 % en un instant una mica diferent, i aquest desfasament és
informació per sota del gra. Aquesta eina ho aprofita fent la mitjana sobre
molts creuaments.

⚠️ I per això ajusta CADA RAMPA PER SEPARAT. Si el hub triga sempre una mica
   més a enviar un sensor concret, aquest retard sistemàtic s'assembla exacta-
   ment a un desplaçament de calibratge — però en pujada desplaça cap a un
   costat i en baixada cap a l'altre. Si les dues rampes no s'assemblen, el que
   tens no és calibratge: és retard o histèresi, i el número no s'ha de fer
   servir.

Surt amb codi 1 si l'ajust no es pot donar per bo.
"""

from __future__ import annotations

import csv
import json
import os
import statistics as est
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from replica import punt_de_rosada  # noqa: E402  (Magnus, sense duplicar-lo)

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
#    l'ajust —dispersió 0,25 °C contra 0,24 sense pendent— però que extrapolat
#    al 85 % de l'hivern inventava fins a 1,5 punts d'HR de correcció (~0,3 °C
#    de Td). Amb l'HR en enters, un pendent ajustat en 10 punts és soroll; i
#    el que fa mal no és el soroll dins del rang, sinó el que fa fora d'ell.
MAX_DISPERSIO_TD = 0.30     # °C — criteri d'acceptació (vegeu calibratge.md)


# ─────────────────────────────────────────────────────────────── dades ──────
FORMAT_HA = "%Y-%m-%dT%H:%M:%S+00:00"


def url_historic(base: str, hores: float, entitats, ara: datetime | None = None) -> str:
    """/api/history de les últimes «hores», amb el final EXPLÍCIT.

    ⚠️ Sense «end_time», Home Assistant en torna només 24 h des de l'inici,
       demanis les hores que demanis. Comprovat el 22/09/2026 amb HA 2026.9.3:
       30 h demanades sense final s'aturaven just 24 h després de l'inici; amb
       end_time=<ara> arribaven senceres. Amb les 72 h per defecte, l'ajust es
       quedava les 24 h MÉS VELLES de la finestra i perdia les 48 més recents
       —les rampes de la caixa de sal i de la nevera— sense cap avís.

    Les dues marques van en UTC amb el fus escrit, i codificades: un «+» cru a
    la URL arriba com un espai.
    """
    ara = ara or datetime.now(timezone.utc)
    des = urllib.parse.quote((ara - timedelta(hours=hores)).strftime(FORMAT_HA))
    fins = urllib.parse.quote(ara.strftime(FORMAT_HA))
    return (f"{base}/api/history/period/{des}?end_time={fins}"
            f"&filter_entity_id={','.join(entitats)}&minimal_response")


def descarrega(hores: float) -> dict[str, list[tuple[datetime, str]]]:
    """Baixa l'històric de Home Assistant. URL i testimoni per variable d'entorn.

    No es posa cap adreça al repositori: és públic.

    ⚠️ Fins al 22/09/2026 la petició no portava «end_time» (vegeu url_historic):
       qualsevol calibratge tret amb --descarrega abans d'aquesta correcció va
       fer servir només les PRIMERES 24 h de la finestra, i s'ha de tornar a
       calcular.
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

    url = url_historic(base, hores, entitats)
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
def finestra_de_calibratge(dades) -> tuple[datetime, datetime] | None:
    """Del marcador: quan va estar encès. És el que delimita l'experiment."""
    punts = sorted(dades.get(MARCADOR, []))
    inici = fi = None
    for quan, estat in punts:
        if estat == "on" and inici is None:
            inici = quan
        elif estat == "off" and inici is not None:
            fi = quan
    if inici is None:
        return None
    return inici, (fi or max(q for p in dades.values() for q, _ in p))


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


# ───────────────────────────────────────────────────────────── informe ──────
def informe(files_per_rampa) -> int:
    problemes = 0
    ajustos = {}
    for nom_rampa, files in files_per_rampa.items():
        print(f"\n── Rampa de {nom_rampa}: {len(files)} mostres d'un minut")
        if len(files) < MIN_MOSTRES:
            print(f"   ⚠ massa curta (calen {MIN_MOSTRES}); no s'hi ajusta res")
            problemes += 1
            continue
        hr = [est.median([f[1][f"sensor.{n}_humitat"] for n in SENSORS]) for f in files]
        t = [est.median([f[1][f"sensor.{n}_temperatura"] for n in SENSORS]) for f in files]
        print(f"   rang assolit: HR {min(hr):.0f}–{max(hr):.0f} %  ·  T {min(t):.1f}–{max(t):.1f} °C")
        ajustos[nom_rampa] = ajusta(files)

    if len(ajustos) < 2:
        print("\n⚠ Només hi ha una rampa utilitzable. Amb una sola no es pot separar\n"
              "  el calibratge del retard del hub: cal la baixada I la pujada.")
        problemes += 1

    if ajustos:
        print("\n── Comparació entre rampes (la prova de si el número és de fiar)")
        print("   sensor              c_t baixada / pujada     c_rh_b baixada / pujada")
        for nom in SENSORS:
            vals = [ajustos[r][nom] for r in ajustos if nom in ajustos[r]]
            if len(vals) == 2:
                dt = abs(vals[0]["c_t"] - vals[1]["c_t"])
                dh = abs(vals[0]["c_rh_b"] - vals[1]["c_rh_b"])
                marca = "  ⚠" if (dt > 0.2 or dh > 1.5) else ""
                print(f"   {nom:18} {vals[0]['c_t']:+6.2f} / {vals[1]['c_t']:+6.2f}"
                      f"      {vals[0]['c_rh_b']:+6.2f} / {vals[1]['c_rh_b']:+6.2f}{marca}")
                if marca:
                    problemes += 1

    totes = [f for files in files_per_rampa.values() for f in files]
    if len(totes) >= MIN_MOSTRES:
        final = ajusta(totes)
        abans = dispersio_td(totes)
        despres = dispersio_td(totes, final)
        print(f"\n── Dispersió de Td entre els cinc (mediana)")
        print(f"   abans:   {abans:.2f} °C")
        print(f"   després: {despres:.2f} °C   (objectiu ≤ {MAX_DISPERSIO_TD:.2f})")
        if despres > MAX_DISPERSIO_TD:
            print("   ⚠ per sobre de l'objectiu: el llindar ΔTd s'ha de quedar alt")
            problemes += 1

        print("\n── Per enganxar a config/packages/rosada.yaml")
        # El rang va AL COSTAT dels números: fora d'ell, la correcció s'extrapola.
        hr_t = [est.median([f[1][f"sensor.{n}_humitat"] for n in SENSORS]) for f in totes]
        t_t = [est.median([f[1][f"sensor.{n}_temperatura"] for n in SENSORS]) for f in totes]
        print(f"   {{#- Calibratge vàlid entre {min(hr_t):.0f} i {max(hr_t):.0f} % d'HR "
              f"i {min(t_t):.1f}–{max(t_t):.1f} °C. Fora d'aquest rang, s'extrapola. -#}}")
        for nom in SENSORS:
            c = final[nom]
            nota = "" if c["pendent_ajustat"] else "   # sense recorregut: només desplaçament"
            print(f"   {nom}:{nota}")
            print(f"     {{% set c_t = {c['c_t']:.2f} %}}"
                  f"{{% set c_rh_a = {c['c_rh_a']:.4f} %}}"
                  f"{{% set c_rh_b = {c['c_rh_b']:.2f} %}}")
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


def tests() -> int:
    ok = True

    def prop(nom, condicio, detall=""):
        nonlocal ok
        ok &= bool(condicio)
        print(f"  {'OK  ' if condicio else 'FALLA'} {nom}" + (f"   ({detall})" if detall else ""))

    print("Mínims quadrats")
    a, b = _minims_quadrats([1, 2, 3, 4], [3, 5, 7, 9])
    prop("recupera y = 2x + 1", abs(a - 2) < 1e-9 and abs(b - 1) < 1e-9, f"a={a:.3f} b={b:.3f}")

    print("\nRecuperació d'un error conegut (amb quantització d'1 % com la real)")
    reals = {"soterrani_fons": (0.0, 0.0), "soterrani_centre": (0.3, -2.0),
             "soterrani_gran": (-0.2, 1.5), "baixa": (0.0, 0.0), "exterior": (0.1, -1.0)}
    files = _sintetic(reals)
    res = ajusta(files)
    for nom, (dt, dh) in reals.items():
        prop(f"{nom}: desplaçament d'HR ≈ {-dh:+.1f}",
             abs(res[nom]["c_rh_b"] - (-dh)) < 0.6, f"obtingut {res[nom]['c_rh_b']:+.2f}")
        prop(f"{nom}: desplaçament de T ≈ {-dt:+.1f}",
             abs(res[nom]["c_t"] - (-dt)) < 0.15, f"obtingut {res[nom]['c_t']:+.2f}")

    print("\nLa correcció redueix la dispersió de Td")
    abans, despres = dispersio_td(files), dispersio_td(files, res)
    prop("la dispersió baixa", despres < abans, f"{abans:.2f} → {despres:.2f} °C")
    prop("i queda dins de l'objectiu", despres <= MAX_DISPERSIO_TD, f"{despres:.2f} °C")

    print("\nSense recorregut no s'inventa cap pendent")
    plans = _sintetic(reals, pas_hr=0.0)
    res_plans = ajusta(plans)
    prop("cap pendent ajustat", not any(r["pendent_ajustat"] for r in res_plans.values()))
    prop("i el pendent es queda a 1", all(r["c_rh_a"] == 1.0 for r in res_plans.values()))

    print("\nAmb 10 punts de recorregut, cap pendent (dades reals del 21/09)")
    curt = ajusta(_sintetic(reals, pas_hr=10 / 300))
    prop("no s'ajusta pendent amb 10 punts d'HR", not any(r["pendent_ajustat"] for r in curt.values()))

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
    url = url_historic("http://ha:8123", 72, ["sensor.x", MARCADOR], ara)
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

    print("\nLa finestra surt del marcador")
    t0 = datetime(2026, 9, 21, tzinfo=timezone.utc)
    dades = {MARCADOR: [(t0, "off"), (t0 + timedelta(hours=1), "on"),
                        (t0 + timedelta(hours=37), "off")]}
    finestra = finestra_de_calibratge(dades)
    prop("detecta inici i final", finestra is not None
         and finestra[0] == t0 + timedelta(hours=1)
         and finestra[1] == t0 + timedelta(hours=37))
    prop("i sense marcador retorna None", finestra_de_calibratge({}) is None)

    print()
    print("Tots els tests passen." if ok else "HI HA TESTS QUE FALLEN.")
    return 0 if ok else 1


# ───────────────────────────────────────────────────────────────── main ─────
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

    finestra = finestra_de_calibratge(dades)
    if finestra is None:
        print(f"No hi ha cap tram amb {MARCADOR} encès. L'experiment s'ha de marcar.")
        return 1
    inici, fi = finestra
    print(f"Finestra de calibratge: {inici.isoformat()} → {fi.isoformat()}")

    files = graella(dades, inici, fi)
    print(f"{len(files)} mostres d'un minut amb els deu sensors alhora")
    return 1 if informe(rampes(files)) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
