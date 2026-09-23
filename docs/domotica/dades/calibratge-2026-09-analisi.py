#!/usr/bin/env python3
"""Totes les xifres de la tanda de calibratge del 21–23/09/2026 que cita el doc.

    python3 docs/domotica/dades/calibratge-2026-09-analisi.py

Fa servir tools/calibratge.py (el mateix camí que l'ordre de línia d'ordres) i
el CSV d'aquesta carpeta. No escriu res: només imprimeix. Si una xifra de
docs/domotica/calibratge.md no surt d'aquí, és vella.

Per què existeix: a la revisió del 23/09/2026 el document duia números de tres
versions diferents de l'eina, i alguns no es podien reproduir de cap manera.
"""
from __future__ import annotations

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


def main() -> None:
    files = C._files_reals()
    llista, final = C.ajust_final(files)
    repo = C.calibratge_del_repo()
    assert all(final[n]["c_rh_a"] == repo[n]["c_rh_a"] and final[n]["c_rh_b"] == repo[n]["c_rh_b"]
               for n in C.SENSORS), "calibratge.jinja no és el que surt de les dades"
    refs = [b["ref"] for b in llista]

    print(f"── L'ajust: {len(llista)} blocs · referència {min(refs):.1f}–{max(refs):.1f} %")
    print("   sensor              a        b      corr. 55 %   73 %    85 %    90 %")
    for n in C.SENSORS:
        c = final[n]
        print(f"   {n:18} {c['c_rh_a']:.4f} {c['c_rh_b']:+6.2f}  "
              + "  ".join(f"{C.correccio(c, x):+6.2f}" for x in (55, 73, 85, 90)))

    print("\n── Blocs per tram (quants n'entren a l'ajust)")
    for nom, tram in SEGMENTS.items():
        print(f"   {nom}: {sum(1 for b in llista if dins(b, tram))}")

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
              f"correcció al 85 %: " + " ".join(f"{n.split('_')[-1]} {C.correccio(aj[n], 85):+.2f}"
                                                for n in C.SENSORS))

    print("\n── La referència interior és un MÀXIM, i el màxim de tres sorolls puja")
    biaix, dtd = [], []
    for b in llista:
        tds = {n: C.punt_de_rosada(b["t"][n], min(max(C.correccio(final[n], b["hr"][n]) + b["hr"][n], 1), 100))
               for n in C.SENSORS}
        tres = [tds["soterrani_fons"], tds["soterrani_centre"], tds["soterrani_gran"]]
        biaix.append(max(tres) - est.mean(tres))
        dtd.append(max(tres) - tds["baixa"])
    print(f"   màxim dels tres − mitjana dels tres (mateix aire): mediana {est.median(biaix):+.2f} °C")
    print(f"   ΔTd interior − planta baixa (mateix aire, hauria de ser 0): "
          f"mitjana {est.mean(dtd):+.2f} °C, p95 {sorted(dtd)[int(0.95 * len(dtd))]:+.2f}")

    print("\n── La temperatura, dins de les dades: es pot separar de l'HR?")
    for des, fins in ((45, 50), (50, 55), (55, 60), (60, 65), (65, 70), (70, 75)):
        tros = [b["t_ref"] for b in llista if des <= b["ref"] < fins]
        if tros:
            print(f"   HR {des}–{fins} %: {len(tros):3} blocs · T {min(tros):.1f}–{max(tros):.1f} °C "
                  f"({max(tros) - min(tros):.1f})")
    p, q = C._minims_quadrats(refs, [b["t_ref"] for b in llista])
    print(f"   T = {p:.3f}·HR {q:+.1f} → del {min(refs):.0f} al {max(refs):.0f} % la T puja "
          f"{p * (max(refs) - min(refs)):.1f} °C")
    for n in C.SENSORS:
        res = [C.correccio(final[n], b["hr"][n]) + b["hr"][n] - b["ref"] for b in llista]
        ts = [b["t_ref"] for b in llista]
        pt, qt = C._minims_quadrats(ts, res)
        var = est.pvariance(res)
        r2 = 1 - est.pvariance([res[i] - (pt * ts[i] + qt) for i in range(len(res))]) / var if var else 0
        print(f"   residu de {n:18} contra la T: {pt:+.2f} punts/°C (R² {r2:.2f})")

    print("\n── Histèresi: la desviació de cada sensor respecte de la mediana, abans i després")
    finestres = {"21/09 nit": ("2026-09-21T00:43+02:00", "2026-09-21T11:26+02:00"),
                 "23/09 13:00–13:33": ("2026-09-23T13:00+02:00", "2026-09-23T13:33+02:00")}
    desv = {}
    dades = C.carrega_csv(C.CSV_REAL)
    for nom, (a, b) in finestres.items():
        fs = C.graella(dades, Q(a), Q(b))
        med = est.mean(est.median(f[1][f"sensor.{n}_humitat"] for n in C.SENSORS) for f in fs)
        ts = est.mean(est.median(f[1][f"sensor.{n}_temperatura"] for n in C.SENSORS) for f in fs)
        desv[nom] = {n: est.mean(f[1][f"sensor.{n}_humitat"] for f in fs) - med for n in C.SENSORS}
        print(f"   {nom}: {len(fs)} min · HR mediana {med:.1f} % · T {ts:.1f} °C · "
              + " ".join(f"{n.split('_')[-1]} {desv[nom][n]:+.2f}" for n in C.SENSORS))
    canvi = {n: desv["23/09 13:00–13:33"][n] - desv["21/09 nit"][n] for n in C.SENSORS}
    print("   canvi: " + " ".join(f"{n.split('_')[-1]} {canvi[n]:+.2f}" for n in C.SENSORS)
          + f" · el més gran, {max(abs(v) for v in canvi.values()):.2f} punts")


if __name__ == "__main__":
    main()
