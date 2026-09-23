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
#    l'ajust —dispersió 0,25 °C contra 0,24 sense pendent— però que extrapolat
#    al 85 % de l'hivern inventava fins a 1,5 punts d'HR de correcció (~0,3 °C
#    de Td). Amb l'HR en enters, un pendent ajustat en 10 punts és soroll; i
#    el que fa mal no és el soroll dins del rang, sinó el que fa fora d'ell.
MAX_DISPERSIO_TD = 0.30     # °C — criteri d'acceptació (vegeu calibratge.md)
MINUTS_BLOC = 20            # el bloc que es promitja per fer un punt d'ajust
RITME_MAX_BLOC = 4.0        # punts d'HR/hora: per sobre, el bloc és transitori
MIN_BLOCS = 10              # menys blocs que això no és una recta, és un dibuix


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

    ⚠️ Es descarten els blocs on l'HR es mou més de «ritme_max» punts/hora: són
       els transitoris —obrir, tancar, els graons— on el retard sí que domina.
    """
    per_bloc: dict[int, list] = {}
    for quan, valors in files:
        clau = int(quan.timestamp()) // (minuts * 60)
        per_bloc.setdefault(clau, []).append((quan, valors))
    sortida = []
    for clau in sorted(per_bloc):
        tall = per_bloc[clau]
        if len(tall) < minuts * 0.75:        # bloc incomplet: forats de dades
            continue
        med = [est.median([v[f"sensor.{n}_humitat"] for n in SENSORS]) for _, v in tall]
        durada_h = (tall[-1][0] - tall[0][0]).total_seconds() / 3600
        if durada_h <= 0 or abs(med[-1] - med[0]) / durada_h > ritme_max:
            continue
        sortida.append({
            "quan": tall[0][0],
            "n": len(tall),
            "hr": {n: est.mean([v[f"sensor.{n}_humitat"] for _, v in tall]) for n in SENSORS},
            "t": {n: est.mean([v[f"sensor.{n}_temperatura"] for _, v in tall]) for n in SENSORS},
            "ref": est.mean(med),
            "t_ref": est.mean([est.median([v[f"sensor.{n}_temperatura"] for n in SENSORS])
                               for _, v in tall]),
        })
    return sortida


def ajusta_blocs(llista: list[dict]) -> dict[str, dict[str, float]]:
    """Per sensor, la recta HR_corregida = c_rh_a·HR + c_rh_b, ajustada pels blocs.

    ⚠️ L'AJUST ES FA AL REVÉS i després s'inverteix: es busca «sensor en funció
       de la referència» i no «referència en funció del sensor». El motiu és que
       els mínims quadrats suposen que la variable independent no té error, i
       aquí el sensor en té —l'HR ve en enters—. Posant-lo com a dependent, el
       pendent deixa d'aplanar-se cap a zero (dilució de la regressió), que és
       part del que feia sortir números absurds ajustant minut a minut.
    """
    if len(llista) < MIN_BLOCS:
        return {}
    refs = [b["ref"] for b in llista]
    recorregut = max(refs) - min(refs)
    resultat = {}
    for nom in SENSORS:
        ys = [b["hr"][nom] for b in llista]
        if recorregut >= MIN_RECORREGUT_HR:
            p, q = _minims_quadrats(refs, ys)      # sensor ≈ p·ref + q
            a, b = (1.0, est.mean([refs[i] - ys[i] for i in range(len(ys))])) if p == 0 \
                else (1 / p, -q / p)               # ref ≈ a·sensor + b
        else:
            # Sense recorregut, un pendent seria soroll disfressat de ciència.
            a, b = 1.0, est.mean([refs[i] - ys[i] for i in range(len(ys))])
        residus = [(a * ys[i] + b) - refs[i] for i in range(len(ys))]
        resultat[nom] = {
            "c_t": est.mean([b_["t_ref"] - b_["t"][nom] for b_ in llista]),
            "c_rh_a": a,
            "c_rh_b": b,
            "recorregut_hr": recorregut,
            "pendent_ajustat": recorregut >= MIN_RECORREGUT_HR,
            "residu_max": max(abs(r) for r in residus),
            "blocs": len(llista),
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
    if len(totes) < MIN_MOSTRES:
        return problemes

    per_rampes = ajusta(totes)
    llista = blocs(totes)
    final = ajusta_blocs(llista)
    print(f"\n── Blocs de {MINUTS_BLOC} min: {len(llista)} utilitzables "
          f"(descartats els de més de {RITME_MAX_BLOC:.0f} punts d'HR/hora)")
    if not final:
        print(f"   ⚠ calen {MIN_BLOCS} blocs i no hi són: l'ajust es fa minut a minut,\n"
              "     que és pitjor. Vegeu docs/domotica/calibratge.md.")
        problemes += 1
        final = per_rampes
    else:
        refs = [b["ref"] for b in llista]
        print(f"   referència de {min(refs):.1f} a {max(refs):.1f} % "
              f"({max(refs) - min(refs):.0f} punts de recorregut)")
        # Els dos mètodes són independents: si no diuen el mateix, no te'n fiïs.
        print("\n── Blocs contra minut a minut (la prova de si el número és de fiar)")
        print("   sensor              correcció per blocs / minut a minut, a l'extrem alt")
        alt = max(refs)
        for nom in SENSORS:
            cb, cm = final[nom], per_rampes[nom]
            vb = cb["c_rh_a"] * alt + cb["c_rh_b"] - alt
            vm = cm["c_rh_a"] * alt + cm["c_rh_b"] - alt
            marca = "  ⚠" if abs(vb - vm) > 1.0 else ""
            print(f"   {nom:18} {vb:+6.2f} / {vm:+6.2f}{marca}")

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


def _sintetic_recta(veritat, hores=12.0):
    """Sensors amb error de PENDENT i desplaçament, sobre una pujada lenta.

    Cada sensor llegeix r tal que a·r + b = x, amb x l'HR de l'aire: és a dir,
    la lectura crua que caldria corregir amb (a, b). Quantitzada a enters, com
    els Tapo, i amb una deriva petita de T perquè hi hagi «dither».
    """
    files = []
    t0 = datetime(2026, 9, 21, tzinfo=timezone.utc)
    n = int(hores * 60)
    for i in range(n):
        x = 48.0 + 27.0 * i / n                    # 48 → 75 % en «hores»
        valors = {}
        for nom, (a, b) in veritat.items():
            valors[f"sensor.{nom}_humitat"] = float(round((x - b) / a))
            valors[f"sensor.{nom}_temperatura"] = round(26.0 + 0.5 * i / n, 1)
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

    print("\nBlocs: es descarten els transitoris i es conserven els replans")
    lents = _sintetic(reals, pas_hr=0.02)          # ~1,2 punts/h
    rapids = _sintetic(reals, pas_hr=0.30)         # ~18 punts/h: transitori
    prop("els blocs lents es conserven", len(blocs(lents)) >= 25, f"{len(blocs(lents))} blocs")
    prop("els transitoris es descarten", len(blocs(rapids)) == 0, f"{len(blocs(rapids))} blocs")

    print("\nL'ajust per blocs recupera un error de pendent + desplaçament")
    veritat = {"soterrani_fons": (0.95, 5.0), "soterrani_centre": (0.96, 0.9),
               "soterrani_gran": (1.03, -1.4), "baixa": (1.00, -1.2), "exterior": (1.0, 0.0)}
    files_b = _sintetic_recta(veritat)
    res_b = ajusta_blocs(blocs(files_b))
    prop("hi ha prou blocs per ajustar", bool(res_b), f"{len(blocs(files_b))} blocs")
    if res_b:
        for nom, (a_real, _) in veritat.items():
            prop(f"{nom}: pendent ≈ {a_real:.2f}", abs(res_b[nom]["c_rh_a"] - a_real) < 0.05,
                 f"obtingut {res_b[nom]['c_rh_a']:.4f}")
        # El que de debò importa: que després de corregir tots diguin el mateix.
        def _dispersio(correccions):
            pitjor = 0.0
            for b in blocs(files_b):
                vals = [b["hr"][n] * correccions[n]["c_rh_a"] + correccions[n]["c_rh_b"]
                        if correccions else b["hr"][n] for n in SENSORS]
                pitjor = max(pitjor, max(vals) - min(vals))
            return pitjor
        prop("la dispersió d'HR entre els cinc baixa de punts a dècimes",
             _dispersio(res_b) < 0.5 < _dispersio(None),
             f"{_dispersio(None):.2f} → {_dispersio(res_b):.2f} punts")

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
def _franges_excloses(argv: list[str]) -> list[tuple[datetime, datetime]]:
    """--exclou INICI/FI, repetible. Trams que NO han d'entrar a l'ajust.

    N'hi ha sempre: el sotrac de qui mou el recipient, el tram dins d'una nevera
    amb gradients... Queden a l'històric —són dades—, però no fan calibratge.
    Les marques van en ISO, amb fus: 2026-09-21T14:54+02:00/2026-09-21T15:30+02:00
    """
    franges = []
    for i, arg in enumerate(argv):
        if arg != "--exclou":
            continue
        des, _, fins = argv[i + 1].partition("/")
        if not fins:
            raise SystemExit("--exclou vol INICI/FI, per exemple "
                             "2026-09-21T14:54+02:00/2026-09-21T15:30+02:00")
        franges.append((_quan(des), _quan(fins)))
    return franges


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

    for franja in _franges_excloses(argv):
        abans = len(files)
        files = [f for f in files if not (franja[0] <= f[0] <= franja[1])]
        print(f"Exclosa {franja[0].isoformat()} → {franja[1].isoformat()}: "
              f"{abans - len(files)} mostres fora")

    return 1 if informe(rampes(files)) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
