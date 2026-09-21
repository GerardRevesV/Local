#!/usr/bin/env python3
"""Anàlisi de l'històric del soterrani: el que no cap en una targeta del tauler.

PER A QUÈ SERVEIX
─────────────────
La lògica v2 deixa cada dia les dades que han de corregir els seus propis
paràmetres (logica-v2.md, «Què aprèn cada dia»). Algunes es veuen al tauler
—vista «Aprendre»—; les que demanen episodis, comparacions o comptes llargs,
les fa aquesta eina, a casa, contra l'històric:

    diposits    Cada dipòsit ple (codi 32): hores, kWh, €, i amb --litres, els
                litres per kWh i el cost per litre. La dada que confirma la
                taula del cost per litre, i amb ella els tres llindars del tram.
    ventilacio  Cada episodi de ventilació: quant baixa el Td del soterrani per
                hora, i QUIN DELS DOS ΔTd (planta baixa o fora) ho prediu millor.
                → input_select.referencia_ventilacio, delta_td_on / delta_td_off
    rebot       La HR del pitjor racó després de cada aturada del compressor:
                quant aguanta la sequedat. → si el pre-assecat en vall paga
    dispersio   Per dia: quant difereixen els tres punts, i quin és el pitjor
                quanta estona. → humitat general o d'un racó
    cost        Per dia: kWh i € per tram, i hores de compressor
    marge       Per dia: hores amb el marge de paret per sota de 3 °C
    decisio     Per dia: hores de cada estat de la decisió, i les que HAURIA
                ventilat. → la pregunta de la Porta B
    resum       Tot això seguit (per defecte)

    python3 tools/analisi.py --prova                          # tests, sense xarxa
    python3 tools/analisi.py descarrega --hores 168 --csv h.csv
    python3 tools/analisi.py resum --csv h.csv
    python3 tools/analisi.py diposits --hores 48 --litres 3.1 2.9

Sense --csv, baixa les últimes --hores (per defecte 168) de HA amb HA_URL i
HA_TOKEN (o HA_TOKEN_FILE), com calibratge.py. Només llegeix. Només biblioteca
estàndard. Les hores i els dies són els locals de Barcelona.
"""

from __future__ import annotations

import csv
import json
import math
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from replica import _local, _quan, historic  # noqa: E402  (mateix accés a HA i mateixa hora local)
from tarifa import a_utc  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Les que només necessiten l'estat, i les que necessiten els atributs.
NUMERIQUES = (
    "sensor.soterrani_fons_punt_de_rosada", "sensor.soterrani_centre_punt_de_rosada",
    "sensor.soterrani_gran_punt_de_rosada", "sensor.soterrani_punt_de_rosada_de_referencia",
    "sensor.dtd_interior_planta_baixa", "sensor.dtd_interior_exterior",
    "sensor.soterrani_humitat_maxima", "sensor.soterrani_dispersio_rosada",
    "sensor.marge_de_condensacio", "sensor.deshumidificador_potencia",
    "sensor.deshumidificador_energia", "sensor.deshumidificador_cost",
    "sensor.deshumidificador_energia_punta", "sensor.deshumidificador_energia_pla",
    "sensor.deshumidificador_energia_vall", "sensor.deshumidificador_cost_punta",
    "sensor.deshumidificador_cost_pla", "sensor.deshumidificador_cost_vall",
    "sensor.deshumidificador_humitat", "sensor.decisio_del_soterrani",
    "sensor.decisio_llindar_deshumidificador", "binary_sensor.decisio_ventiladors",
    "binary_sensor.ventiladors_en_marxa",
)
AMB_ATRIBUTS = ("binary_sensor.deshumidificador_avaria",)
PUNTS = ("fons", "centre", "gran")
W_COMPRESSOR = 150

Serie = list  # [(datetime UTC, estat, atributs | None)], en ordre


# ─── Dades ───────────────────────────────────────────────────────────────────

def descarrega(hores: float) -> dict[str, Serie]:
    dades: dict[str, Serie] = {}
    for entitats, minimal in ((NUMERIQUES, True), (AMB_ATRIBUTS, False)):
        opcions = ["significant_changes_only=0"] + (["minimal_response"] if minimal else [])
        for serie in historic(hores, entitats, *opcions):
            # ⚠️ Amb minimal_response l'entity_id només és al primer punt
            #    (calibratge.py ho va aprendre el 21/09/2026).
            if not serie or not serie[0].get("entity_id"):
                continue
            ent = serie[0]["entity_id"]
            dades[ent] = [(_quan(p.get("last_changed") or p["last_updated"]), p["state"],
                           p.get("attributes")) for p in serie if "state" in p]
    return dades


def desa_csv(dades: dict[str, Serie], cami: Path) -> None:
    with cami.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["marca_temps", "entity_id", "estat", "atributs"])
        for ent, serie in sorted(dades.items()):
            for t, estat, atr in serie:
                w.writerow([t.isoformat(), ent, estat, json.dumps(atr, ensure_ascii=False) if atr else ""])


def carrega_csv(cami: Path) -> dict[str, Serie]:
    dades: dict[str, Serie] = {}
    with cami.open(encoding="utf-8", newline="") as f:
        for fila in csv.DictReader(f):
            dades.setdefault(fila["entity_id"], []).append(
                (_quan(fila["marca_temps"]), fila["estat"],
                 json.loads(fila["atributs"]) if fila.get("atributs") else None))
    for serie in dades.values():
        serie.sort(key=lambda x: x[0])
    return dades


def num(estat) -> float | None:
    try:
        v = float(estat)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


# ─── Sèries escalonades: cada valor val fins al canvi següent ────────────────

def a(serie: Serie, t: datetime):
    """L'estat vigent a l'instant t (el de l'últim canvi ≤ t), o None."""
    vigent = None
    for ts, estat, _ in serie:
        if ts > t:
            break
        vigent = estat
    return vigent


def trossos(serie: Serie, t0: datetime, t1: datetime):
    """[(inici, fi, estat)] que cobreixen [t0, t1], amb l'estat vigent a cada tros."""
    punts = [(t0, a(serie, t0))] + [(ts, e) for ts, e, _ in serie if t0 < ts < t1]
    return [(ini, punts[i + 1][0] if i + 1 < len(punts) else t1, e) for i, (ini, e) in enumerate(punts)]


def segons_que(serie: Serie, t0: datetime, t1: datetime, cond) -> float:
    return sum((fi - ini).total_seconds() for ini, fi, e in trossos(serie, t0, t1) if cond(e))


def mitjana(serie: Serie, t0: datetime, t1: datetime) -> float | None:
    """Mitjana ponderada pel temps; els trossos sense número no compten."""
    suma = durada = 0.0
    for ini, fi, e in trossos(serie, t0, t1):
        v = num(e)
        if v is not None:
            s = (fi - ini).total_seconds()
            suma += v * s
            durada += s
    return suma / durada if durada else None


def minim(serie: Serie, t0: datetime, t1: datetime) -> float | None:
    vals = [num(e) for _, _, e in trossos(serie, t0, t1) if num(e) is not None]
    return min(vals) if vals else None


def intervals(serie: Serie, cond, t_fi: datetime | None = None) -> list[tuple[datetime, datetime]]:
    """Els intervals en què cond(estat) és cert. L'últim, obert, es tanca a t_fi."""
    fora, dins = [], None
    for ts, estat, _ in serie:
        if cond(estat) and dins is None:
            dins = ts
        elif not cond(estat) and dins is not None:
            fora.append((dins, ts))
            dins = None
    if dins is not None and t_fi is not None:
        fora.append((dins, t_fi))
    return fora


def increment(serie: Serie, t0: datetime, t1: datetime) -> float | None:
    """Quant ha pujat un comptador entre t0 i t1. Si baixa de cop (s'ha
    reiniciat), el que marca després és tot el que ha comptat des del reinici.
    El valor a t1 hi entra (un canvi just a t1 és d'aquest interval); el de t0
    és el punt de partida, o sigui que dos intervals seguits no el compten dues vegades.

    ⚠️ Baixar MENYS d'un 10 % no és un reinici, és un rebot: la mateixa regla
    que consum.yaml (i que HA per als «total_increasing»). Passa de debò: el
    22/09/2026 a les 01:06, després d'estar no disponible, l'endoll va tornar
    22 Wh més avall. Comptat com a reinici, sumava 1,56 kWh que no existien."""
    vals = [v for v in [num(a(serie, t0))] + [num(e) for ts, e, _ in serie if t0 < ts <= t1]
            if v is not None]
    if not vals:
        return None
    total, ref = 0.0, vals[0]
    for v in vals[1:]:
        if v >= ref:
            total += v - ref
            ref = v
        elif v < 0.9 * ref:     # reinici: tot el que marca és nou
            total += v
            ref = v
        # si no, rebot: no es compta, i la referència es queda on era
    return total


def dies_locals(t0: datetime, t1: datetime) -> list[tuple[date, datetime, datetime]]:
    """Els dies locals sencers o parcials entre t0 i t1, amb els seus límits en UTC."""
    dia, fi_local = _local(t0).date(), _local(t1).date()
    sortida = []
    while dia <= fi_local:
        ini = datetime.fromtimestamp(a_utc(datetime.combine(dia, datetime.min.time())), timezone.utc)
        fi = datetime.fromtimestamp(a_utc(datetime.combine(dia + timedelta(days=1), datetime.min.time())),
                                    timezone.utc)
        sortida.append((dia, max(ini, t0), min(fi, t1)))
        dia += timedelta(days=1)
    return sortida


def limits(dades: dict[str, Serie]) -> tuple[datetime, datetime]:
    tots = [ts for serie in dades.values() for ts, _, _ in serie]
    return min(tots), max(tots)


def _h(segons: float) -> str:
    return f"{segons / 3600:5.1f} h"


def _v(x, fmt=".2f", buit="—") -> str:
    return buit if x is None else format(x, fmt)


# ─── Les anàlisis ────────────────────────────────────────────────────────────

def diposits(dades: dict[str, Serie], litres: list[float] | None = None) -> list[dict]:
    """Cada dipòsit, de quan es torna a posar buit (32 → 0) a quan s'atura ple (→ 32).
    ⚠️ Tret i ple donen el mateix codi 32 (experiment 8): un «dipòsit» de pocs
       kWh és segurament algú que l'ha tret abans d'hora. I el primer després
       d'estona parat també omple la safata interior: surt car."""
    avaria = dades.get("binary_sensor.deshumidificador_avaria", [])
    codis = [(ts, (atr or {}).get("fault_code")) for ts, _, atr in avaria]
    energia = dades.get("sensor.deshumidificador_energia", [])
    cost = dades.get("sensor.deshumidificador_cost", [])
    potencia = dades.get("sensor.deshumidificador_potencia", [])
    hr = dades.get("sensor.deshumidificador_humitat", [])
    cicles, buidat, anterior = [], None, None
    for ts, codi in codis:
        if anterior == 32 and codi != 32:
            buidat = ts
        elif codi == 32 and anterior != 32 and buidat is not None:
            kwh = increment(energia, buidat, ts)
            cicles.append({"inici": buidat, "fi": ts, "hores": (ts - buidat).total_seconds() / 3600,
                           "kwh": kwh, "eur": increment(cost, buidat, ts),
                           "compressor_h": segons_que(potencia, buidat, ts,
                                                      lambda e: (num(e) or 0) > W_COMPRESSOR) / 3600,
                           "hr": mitjana(hr, buidat, ts), "curt": kwh is not None and kwh < 0.2})
            buidat = None
        anterior = codi
    for cicle, l in zip(cicles, litres or []):
        cicle["litres"] = l
        cicle["l_kwh"] = l / cicle["kwh"] if cicle["kwh"] else None
        cicle["eur_l"] = cicle["eur"] / l if cicle["eur"] is not None and l else None
    return cicles


def ventilacio(dades: dict[str, Serie], minim_min: float = 15) -> dict:
    """Episodis de ventilació, i quin ΔTd prediu millor com baixa el Td del soterrani."""
    reals = dades.get("binary_sensor.ventiladors_en_marxa", [])
    font = "relés" if any(e == "on" for _, e, _ in reals) else "decisió (en ombra)"
    serie = reals if font == "relés" else dades.get("binary_sensor.decisio_ventiladors", [])
    _, t_fi = limits(dades) if dades else (None, None)
    td = dades.get("sensor.soterrani_punt_de_rosada_de_referencia", [])
    episodis = []
    for ini, fi in intervals(serie, lambda e: e == "on", t_fi):
        hores = (fi - ini).total_seconds() / 3600
        td0, td1 = num(a(td, ini)), num(a(td, fi))
        if hores * 60 < minim_min or td0 is None or td1 is None:
            continue
        episodis.append({"inici": ini, "hores": hores, "baixada_h": (td0 - td1) / hores,
                         "dtd_baixa": mitjana(dades.get("sensor.dtd_interior_planta_baixa", []), ini, fi),
                         "dtd_ext": mitjana(dades.get("sensor.dtd_interior_exterior", []), ini, fi)})
    r = {}
    for clau in ("dtd_baixa", "dtd_ext"):
        parells = [(e[clau], e["baixada_h"]) for e in episodis if e[clau] is not None]
        r[clau] = pearson(parells)
    return {"font": font, "episodis": episodis, "r": r}


def pearson(parells: list[tuple[float, float]]) -> float | None:
    if len(parells) < 3:
        return None
    xs, ys = zip(*parells)
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    sxy = sum((x - mx) * (y - my) for x, y in parells)
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    return sxy / math.sqrt(sxx * syy) if sxx and syy else None


def rebot(dades: dict[str, Serie], despres=(30, 60, 120, 180), repos_min: float = 90) -> dict:
    """Després de cada aturada del compressor (i almenys «repos_min» sense tornar a
    engegar), com puja la HR del pitjor racó: quant aguanta la sequedat."""
    potencia = dades.get("sensor.deshumidificador_potencia", [])
    hr = dades.get("sensor.soterrani_humitat_maxima", [])
    _, t_fi = limits(dades)
    engegades = intervals(potencia, lambda e: (num(e) or 0) > W_COMPRESSOR, t_fi)
    events = []
    for i, (_, aturada) in enumerate(engegades):
        seguent = engegades[i + 1][0] if i + 1 < len(engegades) else t_fi
        if aturada >= t_fi or (seguent - aturada).total_seconds() < repos_min * 60:
            continue
        hr0 = num(a(hr, aturada))
        if hr0 is None:
            continue
        punts = {}
        for m in despres:
            t = aturada + timedelta(minutes=m)
            if t <= seguent and t <= t_fi and num(a(hr, t)) is not None:
                punts[m] = num(a(hr, t)) - hr0
        events.append({"aturada": aturada, "hr": hr0, "puja": punts})
    corba = {}
    for m in despres:
        vals = [e["puja"][m] for e in events if m in e["puja"]]
        corba[m] = (sum(vals) / len(vals), len(vals)) if vals else (None, 0)
    return {"events": events, "corba": corba}


def dispersio(dades: dict[str, Serie]) -> list[dict]:
    t0, t1 = limits(dades)
    disp = dades.get("sensor.soterrani_dispersio_rosada", [])
    tds = {p: dades.get(f"sensor.soterrani_{p}_punt_de_rosada", []) for p in PUNTS}
    sortida = []
    for dia, ini, fi in dies_locals(t0, t1):
        # Quin punt és el més humit, tros a tros, on canvia qualsevol dels tres.
        canvis = sorted({ini, fi} | {ts for s in tds.values() for ts, _, _ in s if ini < ts < fi})
        pitjor = {p: 0.0 for p in PUNTS}
        for a_, b_ in zip(canvis, canvis[1:]):
            vals = {p: num(a(s, a_)) for p, s in tds.items()}
            vals = {p: v for p, v in vals.items() if v is not None}
            if vals:
                pitjor[max(vals, key=vals.get)] += (b_ - a_).total_seconds()
        total = sum(pitjor.values())
        maxim = max((num(e) for _, _, e in trossos(disp, ini, fi) if num(e) is not None), default=None)
        sortida.append({"dia": dia, "mitjana": mitjana(disp, ini, fi), "maxim": maxim,
                        "pitjor": {p: s / total for p, s in pitjor.items()} if total else {}})
    return sortida


def cost(dades: dict[str, Serie]) -> list[dict]:
    t0, t1 = limits(dades)
    potencia = dades.get("sensor.deshumidificador_potencia", [])
    sortida = []
    for dia, ini, fi in dies_locals(t0, t1):
        fila = {"dia": dia, "kwh": increment(dades.get("sensor.deshumidificador_energia", []), ini, fi),
                "eur": increment(dades.get("sensor.deshumidificador_cost", []), ini, fi),
                "compressor_h": segons_que(potencia, ini, fi, lambda e: (num(e) or 0) > W_COMPRESSOR) / 3600}
        for tram in ("punta", "pla", "vall"):
            fila[f"kwh_{tram}"] = increment(dades.get(f"sensor.deshumidificador_energia_{tram}", []), ini, fi)
            fila[f"eur_{tram}"] = increment(dades.get(f"sensor.deshumidificador_cost_{tram}", []), ini, fi)
        sortida.append(fila)
    return sortida


def marge(dades: dict[str, Serie], llindar: float = 3.0) -> list[dict]:
    t0, t1 = limits(dades)
    serie = dades.get("sensor.marge_de_condensacio", [])
    return [{"dia": dia, "hores_sota": segons_que(serie, ini, fi,
                                                 lambda e: num(e) is not None and num(e) < llindar) / 3600,
             "minim": minim(serie, ini, fi)} for dia, ini, fi in dies_locals(t0, t1)]


def decisio(dades: dict[str, Serie]) -> list[dict]:
    t0, t1 = limits(dades)
    estats = dades.get("sensor.decisio_del_soterrani", [])
    vent = dades.get("binary_sensor.decisio_ventiladors", [])
    llindar = dades.get("sensor.decisio_llindar_deshumidificador", [])
    sortida = []
    for dia, ini, fi in dies_locals(t0, t1):
        hores: dict[str, float] = {}
        for a_, b_, e in trossos(estats, ini, fi):
            if e is not None:
                hores[e] = hores.get(e, 0) + (b_ - a_).total_seconds() / 3600
        sortida.append({"dia": dia, "hores": hores,
                        "ventilaria_h": segons_que(vent, ini, fi, lambda e: e == "on") / 3600,
                        "llindar": mitjana(llindar, ini, fi)})
    return sortida


# ─── Informes ────────────────────────────────────────────────────────────────

def informe(nom: str, dades: dict[str, Serie], litres: list[float] | None = None) -> None:
    if not dades:
        print("Sense dades.")
        return
    t0, t1 = limits(dades)
    if nom in ("resum",):
        print(f"De {_local(t0):%d/%m %H:%M} a {_local(t1):%d/%m %H:%M} (hora local)\n")
    if nom in ("diposits", "resum"):
        print("═══ Dipòsits (de buit a codi 32) ═══")
        cicles = diposits(dades, litres)
        if not cicles:
            print("  cap dipòsit complet en aquest període (amb la bomba no n'hi ha)")
        for c in cicles:
            print(f"  {_local(c['inici']):%d/%m %H:%M} → {_local(c['fi']):%d/%m %H:%M}  {c['hores']:5.1f} h · "
                  f"{_v(c['kwh'], '.3f')} kWh · {_v(c['eur'], '.3f')} € · compressor {c['compressor_h']:.1f} h · "
                  f"HR aparell {_v(c['hr'], '.0f')} %"
                  + (f" · {c['litres']:.2f} L → {_v(c['l_kwh'])} L/kWh · {_v(c['eur_l'], '.3f')} €/L"
                     if "litres" in c else "")
                  + ("  ⚠️ pocs kWh: tret abans d'hora?" if c["curt"] else ""))
        if cicles and not litres:
            print("  (amb --litres L1 L2 … —els mesurats, en ordre— surten els L/kWh i el €/L)")
    if nom in ("ventilacio", "resum"):
        v = ventilacio(dades)
        print(f"\n═══ Ventilació — episodis de la {v['font']} ═══")
        for e in v["episodis"]:
            print(f"  {_local(e['inici']):%d/%m %H:%M}  {e['hores']:4.1f} h · el Td baixa "
                  f"{e['baixada_h']:+.2f} °C/h · ΔTd planta baixa {_v(e['dtd_baixa'])} · fora {_v(e['dtd_ext'])}")
        if not v["episodis"]:
            print("  cap episodi de més de 15 min")
        rb, re_ = v["r"]["dtd_baixa"], v["r"]["dtd_ext"]
        print(f"  correlació de la baixada amb el ΔTd: planta baixa r = {_v(rb)} · fora r = {_v(re_)}")
        if rb is not None and re_ is not None:
            print(f"  → prediu millor: {'la planta baixa' if rb > re_ else 'fora'} "
                  "(referencia_ventilacio)")
        if v["font"] != "relés":
            print("  ⚠️ en ombra els ventiladors no s'han mogut: els episodis diuen què hauria fet, "
                  "no què ha passat")
    if nom in ("rebot", "resum"):
        r = rebot(dades)
        print(f"\n═══ Rebot — la HR del pitjor racó després d'aturar el compressor ({len(r['events'])} aturades) ═══")
        for m, (puja, n) in r["corba"].items():
            print(f"  +{m:3d} min: {'—' if puja is None else f'{puja:+.1f} punts'}  ({n} aturades)")
    if nom in ("dispersio", "resum"):
        print("\n═══ Dispersió dels tres punts (Td) ═══")
        for d in dispersio(dades):
            pitjor = " · ".join(f"{p} {f:.0%}" for p, f in d["pitjor"].items())
            print(f"  {d['dia']:%d/%m}  mitjana {_v(d['mitjana'])} °C · màxim {_v(d['maxim'])} °C · "
                  f"el més humit: {pitjor or '—'}")
    if nom in ("cost", "resum"):
        print("\n═══ Consum per dia ═══")
        for d in cost(dades):
            print(f"  {d['dia']:%d/%m}  {_v(d['kwh'], '.3f')} kWh · {_v(d['eur'], '.3f')} € · "
                  f"compressor {d['compressor_h']:.1f} h · punta {_v(d['kwh_punta'], '.3f')} kWh "
                  f"({_v(d['eur_punta'], '.3f')} €) · pla {_v(d['kwh_pla'], '.3f')} · vall {_v(d['kwh_vall'], '.3f')}")
    if nom in ("marge", "resum"):
        print("\n═══ Marge de la paret ═══")
        files = marge(dades)
        if all(f["minim"] is None for f in files):
            print("  sense dades (els DS18B20 encara no hi són)")
        else:
            for f in files:
                print(f"  {f['dia']:%d/%m}  per sota de 3 °C: {f['hores_sota']:.1f} h · mínim {_v(f['minim'], '.1f')} °C")
    if nom in ("decisio", "resum"):
        print("\n═══ La decisió, per dia ═══")
        for d in decisio(dades):
            estats = " · ".join(f"{e} {h:.1f} h" for e, h in sorted(d["hores"].items(), key=lambda x: -x[1]))
            print(f"  {d['dia']:%d/%m}  hauria ventilat {d['ventilaria_h']:.1f} h · llindar mitjà "
                  f"{_v(d['llindar'], '.0f')} % · {estats}")


# ─── Tests ───────────────────────────────────────────────────────────────────

def _dades_de_prova() -> dict[str, Serie]:
    """Un dia inventat, amb respostes conegudes. Dijous 24/09/2026, des de les 00:00 locals (22:00 UTC)."""
    t = datetime(2026, 9, 23, 22, 0, tzinfo=timezone.utc)

    def s(*punts):  # (minuts, estat[, atributs])
        return [(t + timedelta(minutes=m), str(e), atr[0] if atr else None) for m, e, *atr in punts]

    return {
        # Compressor de 0 a 60 i de 120 a 180; aturat fins a les 24 h.
        "sensor.deshumidificador_potencia": s((0, 360), (60, 1.1), (120, 360), (180, 1.1), (1439, 1.1)),
        "sensor.deshumidificador_energia": s((0, 10.0), (60, 10.36), (180, 10.72), (1439, 10.73)),
        "sensor.deshumidificador_cost": s((0, 1.0), (60, 1.034), (180, 1.068), (1439, 1.069)),
        # Dipòsit: ple a les 100, buidat a les 110, ple a les 300.
        "binary_sensor.deshumidificador_avaria": s((0, "off", {"fault_code": 0}), (100, "on", {"fault_code": 32}),
                                                   (110, "off", {"fault_code": 0}), (300, "on", {"fault_code": 32})),
        # La HR del pitjor racó: 60 % en aturar-se a les 180, +2 a les 240, +5 a les 360.
        "sensor.soterrani_humitat_maxima": s((0, 62.0), (180, 60.0), (240, 62.0), (360, 65.0)),
        # Dues ventilacions: la primera amb ΔTd alts i el Td baixant de pressa.
        "binary_sensor.decisio_ventiladors": s((0, "off"), (400, "on"), (460, "off"), (600, "on"), (660, "off"),
                                               (800, "on"), (860, "off")),
        "sensor.soterrani_punt_de_rosada_de_referencia": s((0, 15.0), (400, 15.0), (460, 14.0), (600, 14.0),
                                                           (660, 13.5), (800, 13.5), (860, 13.3)),
        "sensor.dtd_interior_planta_baixa": s((0, 1.0), (400, 3.0), (600, 1.5), (800, 0.5)),
        "sensor.dtd_interior_exterior": s((0, 1.0), (400, 0.5), (600, 2.5), (800, 1.0)),
        "sensor.soterrani_fons_punt_de_rosada": s((0, 13.0), (720, 15.5)),
        "sensor.soterrani_centre_punt_de_rosada": s((0, 14.0)),
        "sensor.soterrani_gran_punt_de_rosada": s((0, 15.0)),
        "sensor.soterrani_dispersio_rosada": s((0, 2.0), (720, 1.5)),
        "sensor.marge_de_condensacio": s((0, 4.0), (600, 2.5), (720, 3.5)),
        "sensor.decisio_del_soterrani": s((0, "repos"), (360, "higiene"), (480, "repos"), (1439, "repos")),
    }


def tests() -> int:
    fallades = 0

    def prop(nom, cond, detall=""):
        nonlocal fallades
        print(f"  {'OK  ' if cond else 'FALLA'} {nom}{('  — ' + str(detall)) if detall and not cond else ''}")
        fallades += not cond

    d = _dades_de_prova()
    print("Sèries escalonades")
    t = datetime(2026, 9, 23, 22, 0, tzinfo=timezone.utc)
    pot = d["sensor.deshumidificador_potencia"]
    prop("hores de compressor: 2,0", abs(segons_que(pot, t, t + timedelta(hours=24),
                                                    lambda e: (num(e) or 0) > 150) / 3600 - 2.0) < 1e-9)
    prop("un comptador que es reinicia no resta",
         increment([(t, "5", None), (t + timedelta(hours=1), "6", None), (t + timedelta(hours=2), "0.5", None)],
                   t, t + timedelta(hours=3)) == 1.5)
    # El cas real del 22/09/2026: 1,586 → no disponible → 1,564 → 1,600.
    rebot_real = [(t, "1.5", None), (t + timedelta(minutes=10), "1.586", None),
                  (t + timedelta(minutes=20), "unavailable", None), (t + timedelta(minutes=30), "1.564", None),
                  (t + timedelta(minutes=40), "1.600", None)]
    prop("un rebot cap avall (< 10 %) no es pren per un reinici",
         abs(increment(rebot_real, t, t + timedelta(hours=1)) - 0.100) < 1e-9,
         increment(rebot_real, t, t + timedelta(hours=1)))
    prop("el dia local 24/09 comença a les 22:00 UTC del 23",
         dies_locals(t, t + timedelta(hours=5))[0][:2] == (date(2026, 9, 24), t))

    print("Dipòsits")
    c = diposits(d, litres=[1.2])
    prop("un dipòsit complet, de les 110 a les 300 min", len(c) == 1 and c[0]["hores"] == 190 / 60, c)
    prop("amb els kWh d'aquell interval (0,36)", abs(c[0]["kwh"] - 0.36) < 1e-9, c[0]["kwh"])
    prop("i els litres per kWh (1,2 / 0,36 = 3,33)", abs(c[0]["l_kwh"] - 1.2 / 0.36) < 1e-9)

    print("Ventilació")
    v = ventilacio(d)
    prop("tres episodis d'una hora, de la decisió (en ombra)",
         len(v["episodis"]) == 3 and v["font"] == "decisió (en ombra)", v["episodis"])
    prop("baixades 1,0 · 0,5 · 0,2 °C/h",
         [round(e["baixada_h"], 3) for e in v["episodis"]] == [1.0, 0.5, 0.2])
    prop("el ΔTd de la planta baixa hi correlaciona millor que el de fora",
         v["r"]["dtd_baixa"] is not None and v["r"]["dtd_baixa"] > (v["r"]["dtd_ext"] or -1), v["r"])

    print("Rebot")
    r = rebot(d)
    prop("una aturada útil (la de les 180 min; la de les 60 torna a engegar abans d'hora i mitja)",
         len(r["events"]) == 1, r["events"])
    prop("+60 min: +2 punts · +180 min: +5 punts", r["corba"][60][0] == 2.0 and r["corba"][180][0] == 5.0,
         r["corba"])

    print("Dispersió, marge i decisió")
    di = dispersio(d)[0]
    prop("el gran és el més humit fins a les 12:00 i el fons, després",
         abs(di["pitjor"]["gran"] - 720 / 1439) < 1e-3 and abs(di["pitjor"]["fons"] - 719 / 1439) < 1e-3, di)
    m = marge(d)[0]
    prop("2 h per sota de 3 °C, mínim 2,5", abs(m["hores_sota"] - 2.0) < 1e-9 and m["minim"] == 2.5, m)
    de = decisio(d)[0]
    prop("hauria ventilat 3 h, i 2 h en «higiene»",
         abs(de["ventilaria_h"] - 3.0) < 1e-9 and abs(de["hores"]["higiene"] - 2.0) < 1e-9, de)
    co = cost(d)[0]
    prop("el consum del dia: 0,73 kWh i 0,069 €",
         abs(co["kwh"] - 0.73) < 1e-9 and abs(co["eur"] - 0.069) < 1e-9, co)

    print("CSV d'anada i tornada")
    cami = Path(__file__).resolve().parent / "_prova_analisi.csv"
    try:
        desa_csv(d, cami)
        prop("el CSV es torna a llegir igual", carrega_csv(cami) == d)
    finally:
        cami.unlink(missing_ok=True)

    print("✅ Tot bé" if not fallades else f"❌ {fallades} fallades")
    return 1 if fallades else 0


def main(argv: list[str]) -> int:
    if "--prova" in argv:
        return tests()
    ordres = ("descarrega", "resum", "diposits", "ventilacio", "rebot", "dispersio", "cost", "marge", "decisio")
    nom = next((a_ for a_ in argv if a_ in ordres), "resum")

    def opcio(clau, defecte=None):
        return argv[argv.index(clau) + 1] if clau in argv and argv.index(clau) + 1 < len(argv) else defecte

    litres = [float(x) for x in argv[argv.index("--litres") + 1:] if num(x) is not None] if "--litres" in argv else None
    if nom == "descarrega":
        dades = descarrega(float(opcio("--hores", 168)))
        cami = Path(opcio("--csv", f"historic-{datetime.now():%Y%m%d-%H%M}.csv"))
        desa_csv(dades, cami)
        print(f"{sum(len(s) for s in dades.values())} punts de {len(dades)} entitats a {cami}")
        return 0
    dades = carrega_csv(Path(opcio("--csv"))) if "--csv" in argv else descarrega(float(opcio("--hores", 168)))
    informe(nom, dades, litres)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
