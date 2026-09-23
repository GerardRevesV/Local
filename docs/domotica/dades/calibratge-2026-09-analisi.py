#!/usr/bin/env python3
"""Les xifres de l'ajust del calibratge del 21–23/09/2026 que cita el doc.

    python3 docs/domotica/dades/calibratge-2026-09-analisi.py

Fa servir tools/calibratge.py (el mateix camí que l'ordre de línia d'ordres) i
el CSV d'aquesta carpeta. No escriu res: només imprimeix. Primer, l'informe de
l'eina tal com surt; després, el que l'eina no calcula (trams, fora de mostra,
biaix del màxim, temperatura, histèresi, terra de quantització, salt en
desplegar).

Cobreix les seccions «Com s'ajusta la correcció» i «Els números» de
docs/domotica/calibratge.md. Les xifres de les INCIDÈNCIES (hores, salts d'un
moment concret) surten del CSV directament, no d'aquí.

Per què existeix: a la revisió del 23/09/2026 el document duia números de tres
versions diferents de l'eina, i alguns no es podien reproduir de cap manera.
"""
from __future__ import annotations

import random
import statistics as est
import sys
from datetime import timedelta
from pathlib import Path

ARREL = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ARREL / "tools"))
import calibratge as C  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

Q = C._quan
SEGMENTS = {   # els trams de l'experiment, en hora local
    "la nit (21/09 00:43–11:26)": ("2026-09-21T00:43+02:00", "2026-09-21T11:26+02:00"),
    "la pujada del tàper (21/09 12:39 – 22/09 05:00)": ("2026-09-21T12:39+02:00", "2026-09-22T05:00+02:00"),
    "el replà del tàper (22/09 05:00–12:45)": ("2026-09-22T05:00+02:00", "2026-09-22T12:45+02:00"),
    "després de la nevera (23/09 13:00–13:33)": ("2026-09-23T13:00+02:00", "2026-09-23T13:33+02:00"),
}


def dins(bloc, tram):
    return Q(tram[0]) <= bloc["quan"] < Q(tram[1])


def td_corregit(bloc, nom, c):
    return C.punt_de_rosada(bloc["t"][nom] + c["c_t"],
                            min(max(bloc["hr"][nom] * c["c_rh_a"] + c["c_rh_b"], 1.0), 100.0))


def main() -> None:
    files = C._files_reals()
    print("════ L'INFORME DE L'EINA ════")
    C.informe(files, "2026-09-23")
    llista, final = C.ajust_final(files)
    repo = C.calibratge_del_repo()
    assert all(final[n]["c_rh_a"] == repo[n]["c_rh_a"] and final[n]["c_rh_b"] == repo[n]["c_rh_b"]
               for n in C.SENSORS), "calibratge.jinja no és el que surt de les dades"
    refs = [b["ref"] for b in llista]

    print("\n════ EL QUE L'EINA NO CALCULA ════")
    print(f"\n── L'ajust: {len(llista)} blocs · referència {min(refs):.1f}–{max(refs):.1f} %")
    print("   sensor              a        b      corr. 55 %   73 %    85 %    90 %")
    for n in C.SENSORS:
        c = final[n]
        print(f"   {n:18} {c['c_rh_a']:.4f} {c['c_rh_b']:+6.2f}  "
              + "  ".join(f"{C.correccio(c, x):+6.2f}" for x in (55, 73, 85, 90)))

    print("\n── Blocs per tram, i què cobreixen")
    for nom, tram in SEGMENTS.items():
        tros = [b for b in llista if dins(b, tram)]
        if tros:
            print(f"   {nom}: {len(tros)} blocs · referència {min(b['ref'] for b in tros):.1f}–"
                  f"{max(b['ref'] for b in tros):.1f} % · T {min(b['t_ref'] for b in tros):.1f}–"
                  f"{max(b['t_ref'] for b in tros):.1f} °C")
        else:
            print(f"   {nom}: 0 blocs")

    print("\n── Fora de mostra: s'ajusta sense un tram i es prova sobre aquell tram")
    for nom, tram in SEGMENTS.items():
        prova = [b for b in llista if dins(b, tram)]
        resta = [b for b in llista if not dins(b, tram)]
        aj = C.ajusta_blocs(resta)
        if len(prova) < 2 or not aj:
            continue
        aj = C.desplegable(aj)
        print(f"   {nom}: dins de mostra {C.dispersio_td_blocs(prova, final):.2f} °C · "
              f"fora de mostra {C.dispersio_td_blocs(prova, aj):.2f} °C · "
              f"pendent {'sí' if aj[C.SENSORS[0]]['pendent_ajustat'] else 'NO'} · correcció al 85 %: "
              + " ".join(f"{n.split('_')[-1]} {C.correccio(aj[n], 85):+.2f}" for n in C.SENSORS))

    print("\n── La referència interior és un MÀXIM, i el màxim de tres sorolls puja")
    biaix, dtd, dtd_cru, fons = [], [], [], []
    identitat = {n: {"c_rh_a": 1.0, "c_rh_b": 0.0, "c_t": 0.0} for n in C.SENSORS}
    for b in llista:
        tds = {n: td_corregit(b, n, final[n]) for n in C.SENSORS}
        crus = {n: td_corregit(b, n, identitat[n]) for n in C.SENSORS}
        tres = [tds[n] for n in ("soterrani_fons", "soterrani_centre", "soterrani_gran")]
        tres_c = [crus[n] for n in ("soterrani_fons", "soterrani_centre", "soterrani_gran")]
        biaix.append(max(tres) - est.mean(tres))
        dtd.append(max(tres) - tds["baixa"])
        dtd_cru.append(max(tres_c) - crus["baixa"])
        fons.append(tds["soterrani_fons"] - crus["soterrani_fons"])
    print(f"   màxim dels tres − mitjana dels tres (mateix aire): mediana {est.median(biaix):+.2f} °C")
    print(f"   ΔTd interior − planta baixa (mateix aire, hauria de ser 0): "
          f"mitjana {est.mean(dtd):+.2f} °C, p95 {sorted(dtd)[int(0.95 * len(dtd))]:+.2f}")

    print("\n── El salt en desplegar, amb els sensors junts (el que es veurà a l'històric)")
    tres_noms = ("soterrani_fons", "soterrani_centre", "soterrani_gran")
    hrmax = [max(C.correccio(final[n], b["hr"][n]) + b["hr"][n] for n in tres_noms)
             - max(b["hr"][n] for n in tres_noms) for b in llista]
    print(f"   Td de fons: {min(fons):+.2f} … {max(fons):+.2f} °C · "
          f"ΔTd interior − planta baixa: {est.mean(dtd) - est.mean(dtd_cru):+.2f} °C de mitjana · "
          f"HR màxima: {est.mean(hrmax):+.2f} punts de mitjana")

    print("\n── Quant és 1 punt d'HR en Td")
    for t, h in ((26.5, 55.0), (27.0, 60.0), (12.0, 85.0)):
        print(f"   a {t:.1f} °C i {h:.0f} %: {C.punt_de_rosada(t, h + 1) - C.punt_de_rosada(t, h):.3f} °C")

    print("\n── El terra de la quantització (Monte Carlo: model perfecte i lectures en enters)")
    # Cada sensor és PERFECTE llevat d'un desplaçament per sota del gra (fix per
    # a tot l'experiment) i de l'arrodoniment a enters que fan els Tapo, sobre
    # la trajectòria real de cada bloc. ⚠️ En un replà, un sensor clavat en un
    # enter arrossega el mateix error tot el bloc: això és el que promitjar no
    # treu, i el que un soroll «independent per minut» amagaria (la primera
    # versió d'aquest càlcul, així, donava 0,04 °C per blocs).
    rnd = random.Random(1)
    minuts_bloc = {}
    for q_, v in files:
        minuts_bloc.setdefault(int(q_.timestamp()) // (C.MINUTS_BLOC * 60), []).append(v)
    per_bloc, per_minut = [], []
    for _ in range(20):
        sota_gra = {n: rnd.uniform(-0.5, 0.5) for n in C.SENSORS}
        for b in llista:
            fs = minuts_bloc[int(b["quan"].timestamp()) // (C.MINUTS_BLOC * 60)]
            refs_min = [est.median(v[f"sensor.{n}_humitat"] for n in C.SENSORS) for v in fs]
            ts_min = [est.median(v[f"sensor.{n}_temperatura"] for n in C.SENSORS) for v in fs]
            mitj, un = [], []
            for n in C.SENSORS:
                hs = [round(r + sota_gra[n]) - sota_gra[n] for r in refs_min]
                mitj.append(C.punt_de_rosada(est.mean(ts_min), est.mean(hs)))
                un.append(C.punt_de_rosada(ts_min[0], hs[0]))
            per_bloc.append(max(mitj) - min(mitj))
            per_minut.append(max(un) - min(un))
    print(f"   per blocs: {est.median(per_bloc):.2f} °C · minut a minut: {est.median(per_minut):.2f} °C")
    print("   (el que es mesura per sobre d'això és error que la recta no recull)")

    print("\n── La temperatura, dins de les dades: es pot separar de l'HR?")
    for des, fins in ((45, 50), (50, 55), (55, 60), (60, 65), (65, 70), (70, 75)):
        tros = [b["t_ref"] for b in llista if des <= b["ref"] < fins]
        if tros:
            print(f"   HR {des}–{fins} %: {len(tros):3} blocs · T {min(tros):.1f}–{max(tros):.1f} °C "
                  f"({max(tros) - min(tros):.1f})")
    p, q = C._minims_quadrats(refs, [b["t_ref"] for b in llista])
    print(f"   T = {p:.3f}·HR {q:+.1f} → del {min(refs):.0f} al {max(refs):.0f} % la T puja "
          f"{p * (max(refs) - min(refs)):.1f} °C")
    t_mitja = est.mean(b["t_ref"] for b in llista)
    for n in C.SENSORS:
        res = [C.correccio(final[n], b["hr"][n]) + b["hr"][n] - b["ref"] for b in llista]
        ts = [b["t_ref"] for b in llista]
        pt, qt = C._minims_quadrats(ts, res)
        var = est.pvariance(res)
        r2 = 1 - est.pvariance([res[i] - (pt * ts[i] + qt) for i in range(len(res))]) / var if var else 0
        print(f"   residu de {n:18} contra la T: {pt:+.2f} punts/°C (R² {r2:.2f}) · "
              f"extrapolat a 12 °C: {pt * (12 - t_mitja):+.1f} punts")

    print("\n── Histèresi: la desviació de cada sensor respecte de la mediana, abans i després")
    dades = C.carrega_csv(C.CSV_REAL)

    def desviacions(a, b):
        fs = C.graella(dades, Q(a), Q(b))
        med = est.mean(est.median(f[1][f"sensor.{n}_humitat"] for n in C.SENSORS) for f in fs)
        tmed = est.mean(est.median(f[1][f"sensor.{n}_temperatura"] for n in C.SENSORS) for f in fs)
        dh = {n: est.mean(f[1][f"sensor.{n}_humitat"] for f in fs) - med for n in C.SENSORS}
        dt = {n: est.mean(f[1][f"sensor.{n}_temperatura"] for f in fs) - tmed for n in C.SENSORS}
        return len(fs), med, tmed, dh, dt
    _, m1, t1, d1, _ = desviacions("2026-09-21T00:43+02:00", "2026-09-21T11:26+02:00")
    print(f"   21/09 nit: HR mediana {m1:.1f} % · T {t1:.1f} °C · "
          + " ".join(f"{n.split('_')[-1]} {d1[n]:+.2f}" for n in C.SENSORS))
    for inici in ("13:00", "13:10", "13:20"):
        n2, m2, t2, d2, dt2 = desviacions(f"2026-09-23T{inici}+02:00", "2026-09-23T13:33+02:00")
        canvi = {n: d2[n] - d1[n] for n in C.SENSORS}
        print(f"   23/09 {inici}–13:33 ({n2} min, {m2:.1f} %, {t2:.1f} °C): canvi "
              + " ".join(f"{n.split('_')[-1]} {canvi[n]:+.2f}" for n in C.SENSORS)
              + f" · el més gran, {max(abs(v) for v in canvi.values()):.2f} · T d'exterior "
              f"{dt2['exterior']:+.2f} °C sobre la mediana")


if __name__ == "__main__":
    main()
