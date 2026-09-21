#!/usr/bin/env python3
"""Rèplica offline de la decisió del soterrani — lògica v2.

PER A QUÈ SERVEIX
─────────────────
1. **Provar la lògica abans de desplegar-la.** Els tests d'aquí fan passar
   cada estat, cada mode i els casos límit (HA que arrenca, urgència i la seva
   sortida, caps de setmana i festius, paràmetres incoherents).
2. **Comprovar que HA diu el mateix.** `--prova-ha` fa avaluar la macro de
   config/custom_templates/decisio.jinja AL HA DE DEBÒ —enviada dins de la
   plantilla, sense tocar cap fitxer del servidor— amb milers de casos, i la
   compara amb aquesta rèplica resultat a resultat, motiu inclòs.
3. **Test de deriva.** `--deriva H` baixa les últimes H hores de
   `sensor.decisio_del_soterrani`, que grava les seves entrades, i les torna a
   decidir aquí: si una fila no quadra, les dues implementacions han derivat.
4. **Fixar els llindars amb dades pròpies**: quantes hores hauria ventilat, o
   deshumidificat, amb uns altres paràmetres.

⚠️ Aquesta funció NO decideix res en producció. La decisió en viu la pren la
   macro, cridada per `config/packages/control.yaml`. Duplicar la lògica és un
   cost acceptat conscientment (decisio-stack.md); el que el fa acceptable són
   precisament --prova-ha i --deriva.

    python3 tools/replica.py              # els tests, sense xarxa
    python3 tools/replica.py --prova-ha   # la macro, avaluada per HA, contra la rèplica
    python3 tools/replica.py --deriva 24  # les últimes 24 h gravades, tornades a decidir

--prova-ha i --deriva fan servir HA_URL i HA_TOKEN (o HA_TOKEN_FILE), com
calibratge.py i tarifa.py. Només llegeixen: /api/template avalua una plantilla,
i /api/history torna l'històric.
"""

from __future__ import annotations

import json
import math
import os
import random
import re
import sys
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

# La consola de Windows és cp1252 per defecte i peta amb «°» o «≈». El
# repositori s'edita des de Windows i s'executa a Linux: ha de funcionar als dos.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ARREL = Path(__file__).resolve().parent.parent
MACRO = ARREL / "config" / "custom_templates" / "decisio.jinja"
CONTROL = ARREL / "config" / "packages" / "control.yaml"
ROSADA = ARREL / "config" / "packages" / "rosada.yaml"

# Coeficients de Magnus — Alduchov & Eskridge (1996).
# Error de la fórmula: ±0,1 °C entre −40 i +50 °C.
MAGNUS_A = 17.625
MAGNUS_B = 243.04


def punt_de_rosada(temperatura_c: float, humitat_relativa: float) -> float:
    """Punt de rosada en °C a partir de temperatura (°C) i HR (%).

    La HR es limita a [1, 100]: un 0 % faria log(0) i els sensors barats
    escupen zeros ocasionals, sobretot amb bateria baixa.
    """
    hr = min(max(humitat_relativa, 1.0), 100.0)
    gamma = math.log(hr / 100.0) + (MAGNUS_A * temperatura_c) / (MAGNUS_B + temperatura_c)
    return (MAGNUS_B * gamma) / (MAGNUS_A - gamma)


def humitat_relativa(temperatura_c: float, rosada_c: float) -> float:
    """La inversa: la HR que correspon a un punt de rosada a una temperatura.

    És com `sensor.soterrani_humitat_maxima` treu la HR calibrada de cada punt.
    """
    return 100.0 * math.exp(MAGNUS_A * rosada_c / (MAGNUS_B + rosada_c)
                            - MAGNUS_A * temperatura_c / (MAGNUS_B + temperatura_c))


# ═════════════════════════════════════════════════════════════════════════════
#  LA LÒGICA — rèplica exacta de decisio.jinja
# ═════════════════════════════════════════════════════════════════════════════

# Els valors de partida: els que posa l'inicialitzador de control.yaml la
# primera vegada. Un test comprova que diguin el mateix.
PARAMETRES_DE_PARTIDA: dict[str, float] = {
    "delta_td_on": 2.0,
    "delta_td_off": 0.8,
    "delta_td_higiene": 0.0,
    "t_int_minima": 13.0,
    "hr_ext_bloqueig": 95.0,
    "marge_superficie_min": 3.0,
    "hr_vall": 55.0,
    "hr_pla": 60.0,
    "hr_punta": 65.0,
    "hr_fix": 55.0,
    "hr_urgencia": 70.0,
    "hr_urgencia_objectiu": 50.0,
    "hr_mentre_ventila": 70.0,
    "renovacions_dia": 3.0,
    "renovacions_absencia": 1.0,
    "cabal_ventiladors": 150.0,
    "volum_soterrani": 115.0,
}
# Els dels executors (Fase 3): no entren a la decisió, però l'inicialitzador
# també els posa.
PARAMETRES_EXECUTORS: dict[str, float] = {
    "min_on_ventilador": 12.0,
    "min_off_ventilador": 10.0,
}

MODES = ("Òptim", "Ocupat", "Prioritzar ventilació", "Assecat intensiu", "Silenci",
         "Impressió", "Absència", "Llindar fix", "Tot aturat")
ESTATS = ("calibratge", "aturat", "sense_dades", "urgencia", "ocupat", "impressio", "fix",
          "bloquejat", "ventilar", "higiene", "deshumidificar", "repos")

HISTERESI_URGENCIA_HR = 5
HISTERESI_MARGE = 0.5
HISTERESI_HIGIENE = 0.5
VELOCITAT_ALTA = 100


def _f(x: float, decimals: int) -> str:
    """El filtre «format» de Jinja: '%.Nf' % x."""
    return f"%.{decimals}f" % x


def decideix(e: dict, p: dict, minuts_fins_mitjanit: int) -> dict:
    """Rèplica exacta de `decideix()` de config/custom_templates/decisio.jinja.

    Mateix ordre, mateixes operacions, mateixos textos. Qualsevol canvi aquí
    s'ha de fer també a la macro, i --prova-ha ho comprovarà.
    """
    o = {"estat": "repos", "motiu": "", "llindar": None, "ventiladors": None,
         "per_dtd": False, "urgencia": None, "dtd": None, "llindar_tram": None,
         "pendent": None}
    falta = next((k for k in PARAMETRES_DE_PARTIDA if p.get(k) is None), None)
    mode = e["mode"]
    nit = mode in ("Ocupat", "Silenci")

    # ── 1–3. NO ES DECIDEIX RES
    if e["calibratge"]:
        o.update(estat="calibratge", motiu="Mode calibratge: els sensors estan junts, no al seu lloc")
    elif mode == "Tot aturat":
        o.update(estat="aturat", ventiladors=False,
                 motiu="Tot aturat (a mà): cap ordre al deshumidificador, i els ventiladors aturats")
    elif falta is not None:
        o.update(estat="sense_dades", ventiladors=False, motiu=f"Paràmetre sense valor: {falta}")
    elif e["td_int"] is None:
        o.update(estat="sense_dades", ventiladors=False, motiu="Sense punt de rosada interior fiable")
    elif e["hr_max"] is None:
        o.update(estat="sense_dades", ventiladors=False, motiu="Sense humitat interior fiable")
    elif e["t_int"] is None:
        o.update(estat="sense_dades", ventiladors=False, motiu="Sense temperatura interior fiable")
    else:
        # ── ELS NÚMEROS
        trams = {"vall": p["hr_vall"], "pla": p["hr_pla"], "punta": p["hr_punta"]}
        llindar_tram = int(trams[e["tram"]] if e["tram"] in trams
                           else min([p["hr_vall"], p["hr_pla"], p["hr_punta"]]))
        tram_text = f"del tram de {e['tram']}" if e["tram"] in trams else "(tram desconegut)"

        ref_baixa = e["referencia"] != "Exterior"
        td_ref = e["td_baixa"] if ref_baixa else e["td_ext"]
        ref_nom = "la planta baixa" if ref_baixa else "fora"
        dtd = None if td_ref is None else round(e["td_int"] - td_ref, 2)

        fred = e["t_int"] < p["t_int_minima"]
        humit_fora = (not ref_baixa) and e["hr_ext"] is not None and e["hr_ext"] > p["hr_ext_bloqueig"]
        plou = (not ref_baixa) and e["plou"]
        bloqueig = fred or humit_fora or plou

        delta_ok = p["delta_td_off"] < p["delta_td_on"]
        llindar_dtd = p["delta_td_off"] if e["ventila_previ"] else p["delta_td_on"]
        vol_ventilar = delta_ok and dtd is not None and dtd >= llindar_dtd
        asseca = vol_ventilar and not bloqueig

        renovacions = p["renovacions_absencia"] if mode == "Absència" else p["renovacions_dia"]
        objectiu_min = renovacions * p["volum_soterrani"] / p["cabal_ventiladors"] * 60
        pendent = (None if e["minuts_ventilats"] is None
                   else max([objectiu_min - e["minuts_ventilats"], 0]))
        moment_bo = dtd is not None and dtd >= p["delta_td_higiene"] - (
            HISTERESI_HIGIENE if e["estat_previ"] == "higiene" else 0)
        fi_de_dia = pendent is not None and pendent >= minuts_fins_mitjanit
        vol_higiene = mode == "Prioritzar ventilació" or (
            pendent is not None and pendent > 0 and (moment_bo or fi_de_dia))

        hr_llindar = p["hr_urgencia"] - (HISTERESI_URGENCIA_HR if e["urgencia_previ"] else 0)
        marge_llindar = p["marge_superficie_min"] + (HISTERESI_MARGE if e["urgencia_previ"] else 0)
        per_hr = e["hr_max"] >= hr_llindar
        per_marge = e["marge"] is not None and e["marge"] < marge_llindar

        hr_text = _f(e["hr_max"], 1)
        o.update(dtd=dtd, llindar_tram=llindar_tram,
                 pendent=None if pendent is None else int(round(pendent, 0)))

        # ── 4–13. EL PRIMER QUE ES COMPLEIX, MANA
        if per_hr or per_marge or mode == "Assecat intensiu":
            o.update(estat="urgencia", urgencia="hr" if per_hr else ("marge" if per_marge else "mode"),
                     llindar=int(p["hr_urgencia_objectiu"]))
            if mode != "Llindar fix":
                o.update(ventiladors=asseca or mode in ("Ocupat", "Impressió"), per_dtd=asseca)
            if per_hr and e["hr_max"] >= p["hr_urgencia"]:
                m = f"Urgència: HR màxima al {hr_text} % (llindar: {_f(p['hr_urgencia'], 0)} %)"
            elif per_hr:
                m = f"Urgència: HR màxima al {hr_text} %, fins que baixi del {_f(hr_llindar, 0)} %"
            elif per_marge and e["marge"] < p["marge_superficie_min"]:
                m = (f"Urgència: marge de paret de {_f(e['marge'], 1)} °C "
                     f"(mínim: {_f(p['marge_superficie_min'], 1)} °C)")
            elif per_marge:
                m = (f"Urgència: marge de paret de {_f(e['marge'], 1)} °C, "
                     f"fins que passi de {_f(marge_llindar, 1)} °C")
            else:
                m = "Assecat intensiu (a mà)"
            if o["ventiladors"] and asseca:
                m += f" · ventiladors: l'aire de {ref_nom} asseca (ΔTd = {_f(dtd, 2)} °C)"
            elif o["ventiladors"]:
                m += " · ventiladors: " + ("hi ha algú" if mode == "Ocupat" else "impressió")
            o["motiu"] = m
        elif mode == "Ocupat":
            o.update(estat="ocupat", llindar=llindar_tram, ventiladors=True,
                     motiu=("Hi ha algú (a mà): ventilació contínua, i el deshumidificador "
                            f"en mode Nit al {llindar_tram} % {tram_text}"))
        elif mode == "Impressió":
            o.update(estat="impressio", llindar=llindar_tram, ventiladors=True,
                     motiu="Impressió (a mà): ventilació contínua pels vapors")
        elif mode == "Llindar fix":
            o.update(estat="fix", llindar=int(p["hr_fix"]),
                     motiu=f"Llindar fix al {int(p['hr_fix'])} % (a mà): els ventiladors no es toquen")
        elif not delta_ok:
            o.update(estat="bloquejat", llindar=llindar_tram, ventiladors=False,
                     motiu=(f"Paràmetres incoherents: el Δ d'aturada ({_f(p['delta_td_off'], 1)} °C) "
                            f"no és per sota del d'arrencada ({_f(p['delta_td_on'], 1)} °C)"))
        elif mode != "Silenci" and asseca:
            o.update(estat="ventilar", llindar=int(p["hr_mentre_ventila"]), ventiladors=True,
                     per_dtd=True, motiu=f"L'aire de {ref_nom} asseca: ΔTd = {_f(dtd, 2)} °C")
        elif mode != "Silenci" and vol_higiene and not bloqueig:
            if mode == "Prioritzar ventilació":
                m = "Prioritzar ventilació (a mà)"
            elif moment_bo:
                m = f"Renovar l'aire: falten {_f(pendent, 0)} min, i ara no mulla (ΔTd = {_f(dtd, 2)} °C)"
            else:
                m = f"Renovar l'aire: falten {_f(pendent, 0)} min, i s'acaba el dia"
            o.update(estat="higiene", llindar=int(p["hr_mentre_ventila"]), ventiladors=True, motiu=m)
        elif mode != "Silenci" and (vol_ventilar or vol_higiene):
            vol = "ventilar" if vol_ventilar else "renovar l'aire"
            if fred:
                m = f"Es voldria {vol}, però fa massa fred a dins ({_f(e['t_int'], 1)} °C)"
            elif humit_fora:
                m = f"Es voldria {vol}, però l'HR de fora és al {_f(e['hr_ext'], 0)} %: el sensor pot estar mullat"
            else:
                m = f"Es voldria {vol}, però plou segons l'estació oficial"
            o.update(estat="bloquejat", llindar=llindar_tram, ventiladors=False, motiu=m)
        elif e["hr_max"] > llindar_tram:
            o.update(estat="deshumidificar", llindar=llindar_tram, ventiladors=False,
                     motiu=(("Silenci: " if mode == "Silenci" else "")
                            + f"HR màxima al {hr_text} %, per sobre del {llindar_tram} % {tram_text}"))
        else:
            o.update(estat="repos", llindar=llindar_tram, ventiladors=False,
                     motiu=(("Silenci: " if mode == "Silenci" else "")
                            + f"HR màxima al {hr_text} %: dins del {llindar_tram} % {tram_text}"))

    tocar = o["llindar"] is not None
    return {
        "estat": o["estat"], "motiu": o["motiu"], "llindar": o["llindar"],
        "mode_aparell": ("sleep" if nit else "normal") if tocar else None,
        "velocitat": (None if nit else VELOCITAT_ALTA) if tocar else None,
        "ventiladors": o["ventiladors"], "ventila_per_dtd": o["per_dtd"],
        "urgencia": o["urgencia"], "dtd": o["dtd"], "llindar_tram": o["llindar_tram"],
        "higiene_pendent": o["pendent"],
    }


def entrades(**canvis) -> dict:
    """Unes entrades de partida —un dia normal, en pla, sense res a fer— per als tests."""
    e = {"calibratge": False, "mode": "Òptim", "referencia": "Planta baixa",
         "td_int": 12.0, "hr_max": 58.0, "t_int": 20.0, "marge": None,
         "td_baixa": 12.5, "td_ext": 13.0, "hr_ext": 60.0, "plou": False,
         "tram": "pla", "minuts_ventilats": 200.0, "estat_previ": "repos",
         "ventila_previ": False, "urgencia_previ": False}
    desconegudes = set(canvis) - set(e)
    if desconegudes:
        raise KeyError(f"entrades desconegudes: {desconegudes}")
    e.update(canvis)
    return e


def parametres(**canvis) -> dict:
    p = dict(PARAMETRES_DE_PARTIDA)
    p.update(canvis)
    return p


# ═════════════════════════════════════════════════════════════════════════════
#  TESTS
# ═════════════════════════════════════════════════════════════════════════════

def _prop(nom: str, condicio: bool, detall: str = "") -> bool:
    marca = "OK  " if condicio else "FALLA"
    print(f"  {marca} {nom}{('  — ' + str(detall)) if detall and not condicio else ''}")
    return condicio


def _d(**kw):
    """decideix() amb entrades de partida canviades; «p=», «m=» per als altres."""
    p = kw.pop("p", parametres())
    m = kw.pop("m", 600)
    return decideix(entrades(**kw), p, m)


def tests() -> int:
    ok = True
    print("Fórmula de Magnus")
    for t, hr, esperat in [
        (20.0, 75.0, 15.44),
        (30.0, 65.0, 22.71),
        (20.0, 100.0, 20.00),
        (22.4, 66.0, 15.74),   # lectura real de «Centre», 20/09/2026
        (23.9, 68.0, 17.64),   # lectura real de «Fora», 20/09/2026
    ]:
        obtingut = punt_de_rosada(t, hr)
        ok &= _prop(f"Td({t} °C, {hr} %) ≈ {esperat} °C", abs(obtingut - esperat) < 0.05,
                    f"obtingut {obtingut:.2f}")
    ok &= _prop("a HR 100 % el punt de rosada és la temperatura",
                abs(punt_de_rosada(17.3, 100.0) - 17.3) < 0.01)
    ok &= _prop("HR 0 % no peta (es limita a 1 %)", punt_de_rosada(20.0, 0.0) < -20)
    ok &= _prop("el punt de rosada creix amb la humitat",
                punt_de_rosada(20, 40) < punt_de_rosada(20, 60) < punt_de_rosada(20, 80))
    ok &= _prop("la inversa torna la HR (la de soterrani_humitat_maxima)",
                all(abs(humitat_relativa(t, punt_de_rosada(t, h)) - h) < 1e-9
                    for t in (8.0, 15.0, 28.0) for h in (35.0, 62.0, 97.0)))
    ok &= _prop("arrodonir el Td a 2 decimals mou la HR menys de 0,1 punts",
                all(abs(humitat_relativa(t, round(punt_de_rosada(t, h), 2)) - h) < 0.1
                    for t in (8.0, 15.0, 28.0) for h in (35.0, 62.0, 97.0)))

    print("\nEl cas que motiva el projecte")
    # 20/09/2026: fora SEMBLA més sec, però el Td de fora és més alt → ventilar mullaria.
    interior, exterior = punt_de_rosada(22.4, 66.0), punt_de_rosada(23.9, 68.0)
    ok &= _prop("amb les lectures reals del 20/09/2026, l'aire de fora porta més aigua",
                exterior > interior, f"int {interior:.2f} vs ext {exterior:.2f}")
    d = _d(referencia="Exterior", td_int=round(interior, 2), td_ext=round(exterior, 2),
           t_int=22.4, hr_ext=68.0, hr_max=66.0)
    ok &= _prop("i la lògica NO ventila", d["estat"] != "ventilar" and not d["ventiladors"], d)

    print("\nCalibratge: guanya a tot")
    ok &= _prop("amb el mode encès, «calibratge» i no es toca res",
                (lambda d: d["estat"] == "calibratge" and d["llindar"] is None
                 and d["ventiladors"] is None)(_d(calibratge=True)))
    ok &= _prop("fins i tot amb una urgència", _d(calibratge=True, hr_max=85.0)["estat"] == "calibratge")
    ok &= _prop("fins i tot sense dades", _d(calibratge=True, td_int=None, hr_max=None,
                                               t_int=None)["estat"] == "calibratge")
    ok &= _prop("fins i tot en «Tot aturat»", _d(calibratge=True, mode="Tot aturat")["estat"] == "calibratge")
    ok &= _prop("i amb un paràmetre sense valor", _d(calibratge=True, p=parametres(hr_vall=None))["estat"]
                == "calibratge")

    print("\nTot aturat i fallada segura")
    d = _d(mode="Tot aturat", hr_max=85.0)
    ok &= _prop("«Tot aturat»: no es toca el deshumidificador, ventiladors aturats, encara que sigui urgent",
                d["estat"] == "aturat" and d["llindar"] is None and d["ventiladors"] is False, d)
    for nom, kw, motiu in [
        ("sense Td interior", dict(td_int=None), "Sense punt de rosada interior fiable"),
        ("sense HR interior", dict(hr_max=None), "Sense humitat interior fiable"),
        ("sense T interior", dict(t_int=None), "Sense temperatura interior fiable"),
        ("un paràmetre sense valor", dict(p=parametres(cabal_ventiladors=None)),
         "Paràmetre sense valor: cabal_ventiladors"),
    ]:
        d = _d(**kw)
        ok &= _prop(f"{nom} → sense_dades, ventiladors aturats, deshumidificador sense tocar",
                    d["estat"] == "sense_dades" and d["ventiladors"] is False and d["llindar"] is None
                    and d["motiu"] == motiu, d)
    d = _d(td_baixa=None, hr_max=63.0)
    ok &= _prop("sense la referència NO és sense_dades: el deshumidificador segueix pel tram",
                d["estat"] == "deshumidificar" and d["llindar"] == 60 and d["dtd"] is None, d)
    d = _d(td_baixa=None, td_int=16.0)
    ok &= _prop("i sense referència no es ventila per ΔTd", d["ventiladors"] is False, d)

    print("\nHA que arrenca: no hi ha estat previ")
    d = _d(estat_previ="unknown", ventila_previ=False, urgencia_previ=False, td_int=13.5)
    ok &= _prop("sense estat previ, la histèresi fa servir el llindar d'arrencada (ΔTd 1,0 < 2,0: no ventila)",
                d["estat"] != "ventilar", d)
    d = _d(estat_previ="unavailable", hr_max=67.0)
    ok &= _prop("i sense urgència prèvia, la urgència entra al 70 %, no al 65 %", d["estat"] != "urgencia", d)
    d = _d(mode="unknown")
    ok &= _prop("un mode desconegut es comporta com «Òptim»", d["estat"] == "repos" and d["llindar"] == 60, d)
    d = _d(referencia="unknown", td_int=15.0, td_baixa=12.5, td_ext=20.0)
    ok &= _prop("una referència desconeguda es comporta com la planta baixa", d["estat"] == "ventilar", d)

    print("\nUrgència")
    d = _d(hr_max=70.0)
    ok &= _prop("HR màxima al 70 % → urgència, al 50 % en Manual i velocitat alta",
                d["estat"] == "urgencia" and d["urgencia"] == "hr" and d["llindar"] == 50
                and d["mode_aparell"] == "normal" and d["velocitat"] == 100, d)
    ok &= _prop("sigui quin sigui el tram (punta)", _d(hr_max=72.0, tram="punta")["llindar"] == 50)
    ok &= _prop("al 69,9 % encara no", _d(hr_max=69.9)["estat"] != "urgencia")
    d = _d(hr_max=66.0, urgencia_previ=True)
    ok &= _prop("i se'n surt 5 punts per sota: al 66 % hi segueix",
                d["estat"] == "urgencia" and "fins que baixi del 65 %" in d["motiu"], d)
    ok &= _prop("al 64,9 % ja en surt", _d(hr_max=64.9, urgencia_previ=True)["estat"] != "urgencia")
    d = _d(marge=2.9)
    ok &= _prop("marge de paret de 2,9 °C → urgència per marge", d["urgencia"] == "marge", d)
    ok &= _prop("marge de 3,2 °C amb urgència prèvia → hi segueix (surt a 3,5)",
                _d(marge=3.2, urgencia_previ=True)["estat"] == "urgencia")
    ok &= _prop("sense sensor de paret, el marge no dispara res", _d(marge=None)["estat"] == "repos")
    d = _d(mode="Assecat intensiu")
    ok &= _prop("«Assecat intensiu» → urgència a mà, encara que no calgui",
                d["estat"] == "urgencia" and d["urgencia"] == "mode" and d["llindar"] == 50, d)
    d = _d(hr_max=75.0, td_int=16.0, td_baixa=13.0)
    ok &= _prop("urgència amb aire que asseca → ventiladors engegats i tots dos junts",
                d["ventiladors"] is True and d["ventila_per_dtd"] is True and "asseca" in d["motiu"], d)
    d = _d(hr_max=75.0, td_int=16.0, td_baixa=13.0, t_int=11.0)
    ok &= _prop("però amb fred a dins, els ventiladors no", d["ventiladors"] is False, d)
    d = _d(hr_max=75.0, mode="Ocupat")
    ok &= _prop("urgència amb algú dins → ventiladors engegats igualment, i mode Nit",
                d["ventiladors"] is True and d["mode_aparell"] == "sleep" and d["velocitat"] is None
                and "hi ha algú" in d["motiu"], d)
    d = _d(hr_max=75.0, mode="Impressió", t_int=11.0)
    ok &= _prop("urgència imprimint, amb fred → ventiladors engegats (els vapors)",
                d["ventiladors"] is True and "impressió" in d["motiu"], d)
    d = _d(hr_max=75.0, mode="Llindar fix")
    ok &= _prop("urgència en «Llindar fix» → al 50 %, però els ventiladors no es toquen",
                d["llindar"] == 50 and d["ventiladors"] is None, d)
    d = _d(hr_max=75.0, mode="Silenci", td_int=16.0, td_baixa=13.0)
    ok &= _prop("urgència en «Silenci» amb aire que asseca → ventiladors sí, aparell en Nit",
                d["ventiladors"] is True and d["mode_aparell"] == "sleep", d)

    print("\nEl llindar per tram — cost per litre")
    for tram, esperat in (("vall", 55), ("pla", 60), ("punta", 65)):
        d = _d(tram=tram, hr_max=50.0)
        ok &= _prop(f"{tram} → {esperat} %", d["llindar"] == esperat and d["llindar_tram"] == esperat, d)
    d = _d(tram=None, hr_max=50.0)
    ok &= _prop("tram desconegut → el més baix (55 %)", d["llindar"] == 55 and "desconegut" in d["motiu"], d)
    ok &= _prop("HR màxima per sobre del tram → «deshumidificar»", _d(hr_max=61.0)["estat"] == "deshumidificar")
    ok &= _prop("i per sota → «repos», amb el mateix llindar", _d(hr_max=59.0)["llindar"] == 60)
    # Els caps de setmana i els festius, pel calendari de tarifa.py (el mateix
    # que tarifa.jinja, verificat hora per hora contra HA).
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from tarifa import tram as tram_de  # noqa: E402
    for nom, dia, hora, esperat in [
        ("dimarts 22/09/2026 a les 03", date(2026, 9, 22), 3, 55),
        ("dimarts 22/09/2026 a les 09", date(2026, 9, 22), 9, 60),
        ("dimarts 22/09/2026 a les 11", date(2026, 9, 22), 11, 65),
        ("dissabte 26/09/2026 a les 11", date(2026, 9, 26), 11, 55),
        ("diumenge 27/09/2026 a les 19", date(2026, 9, 27), 19, 55),
        ("dilluns 12/10/2026 (festiu) a les 11", date(2026, 10, 12), 11, 55),
        ("dimarts 8/12/2026 (festiu) a les 19", date(2026, 12, 8), 19, 55),
        ("Divendres Sant 2027 a les 11 (NO és vall)", date(2027, 3, 26), 11, 65),
        ("dilluns 7/12/2026 (trasllat, NO és vall) a les 19", date(2026, 12, 7), 19, 65),
    ]:
        d = _d(tram=tram_de(dia, hora), hr_max=50.0)
        ok &= _prop(f"{nom} → {esperat} %", d["llindar"] == esperat, d)
    d = _d(p=parametres(hr_vall=50.0), tram="vall", hr_max=52.0)
    ok &= _prop("l'experiment del 50 % en vall és només un paràmetre",
                d["estat"] == "deshumidificar" and d["llindar"] == 50, d)

    print("\nVentilar per assecar, amb histèresi")
    d = _d(td_int=14.5, td_baixa=12.5)
    ok &= _prop("ΔTd = 2,00 contra la planta baixa → ventilar, deshumidificador al 70 %",
                d["estat"] == "ventilar" and d["llindar"] == 70 and d["ventiladors"] is True
                and d["ventila_per_dtd"] is True and d["dtd"] == 2.0, d)
    ok &= _prop("ΔTd = 1,50 parat → no arrenca",
                _d(td_int=14.0, td_baixa=12.5)["estat"] != "ventilar")
    ok &= _prop("ΔTd = 1,50 ventilant → continua",
                _d(td_int=14.0, td_baixa=12.5, ventila_previ=True)["estat"] == "ventilar")
    ok &= _prop("ΔTd = 0,70 ventilant → s'atura",
                _d(td_int=13.2, td_baixa=12.5, ventila_previ=True)["estat"] != "ventilar")
    d = _d(referencia="Exterior", td_int=14.5, td_baixa=16.0, td_ext=12.0)
    ok &= _prop("la referència tria contra quin aire: amb «Exterior» mana el de fora",
                d["estat"] == "ventilar" and d["dtd"] == 2.5 and "fora" in d["motiu"], d)
    ok &= _prop("i amb «Planta baixa», el de dalt (que aquí mullaria)",
                _d(td_int=14.5, td_baixa=16.0, td_ext=12.0)["estat"] != "ventilar")
    d = _d(td_int=15.0, td_baixa=12.5, t_int=12.0)
    ok &= _prop("fred a dins → «bloquejat», i només perquè es volia ventilar",
                d["estat"] == "bloquejat" and d["ventiladors"] is False and "ventilar" in d["motiu"], d)
    d = _d(t_int=12.0)
    ok &= _prop("fred a dins sense res a ventilar → no és «bloquejat»", d["estat"] == "repos", d)
    d = _d(td_int=15.0, td_baixa=12.5, hr_ext=98.0, plou=True)
    ok &= _prop("amb la planta baixa, l'HR de fora i la pluja no bloquegen", d["estat"] == "ventilar", d)
    d = _d(referencia="Exterior", td_int=15.0, td_ext=12.5, hr_ext=98.0)
    ok &= _prop("amb «Exterior», l'HR de fora al 98 % bloqueja", d["estat"] == "bloquejat"
                and "mullat" in d["motiu"], d)
    d = _d(referencia="Exterior", td_int=15.0, td_ext=12.5, plou=True)
    ok &= _prop("amb «Exterior», la pluja bloqueja", d["estat"] == "bloquejat" and "plou" in d["motiu"], d)
    d = _d(td_int=15.0, td_baixa=12.5, p=parametres(delta_td_off=2.5))
    ok &= _prop("paràmetres incoherents (Δ d'aturada ≥ d'arrencada) → «bloquejat» i no es ventila",
                d["estat"] == "bloquejat" and d["ventiladors"] is False and "incoherents" in d["motiu"], d)
    ok &= _prop("però la urgència segueix manant",
                _d(hr_max=75.0, p=parametres(delta_td_off=2.5))["estat"] == "urgencia")

    print("\nRenovar l'aire (higiene)")
    objectiu = 3 * 115 / 150 * 60   # 138 min
    d = _d(minuts_ventilats=0.0, td_int=12.6, td_baixa=12.5)
    ok &= _prop("falten minuts i ara no mulla (ΔTd 0,1) → «higiene», al 70 %",
                d["estat"] == "higiene" and d["llindar"] == 70 and d["higiene_pendent"] == round(objectiu), d)
    ok &= _prop("falten minuts però ara mullaria, i queda dia → espera",
                _d(minuts_ventilats=0.0, td_int=12.0, td_baixa=13.0, m=600)["estat"] != "higiene")
    d = _d(minuts_ventilats=0.0, td_int=12.0, td_baixa=13.0, m=138)
    ok &= _prop("però si ja no queda dia (138 min per a 138 que falten) → es ventila igualment",
                d["estat"] == "higiene" and "acaba el dia" in d["motiu"], d)
    ok &= _prop("amb els minuts fets, res", _d(minuts_ventilats=140.0, td_int=12.6)["estat"] == "repos")
    ok &= _prop("amb la histèresi, a ΔTd −0,40 segueix renovant",
                _d(minuts_ventilats=50.0, td_int=12.1, td_baixa=12.5, estat_previ="higiene")["estat"]
                == "higiene")
    ok &= _prop("sense el comptador de minuts, no es decideix renovar",
                _d(minuts_ventilats=None, td_int=12.6)["estat"] == "repos")
    d = _d(mode="Absència", minuts_ventilats=50.0, td_int=12.6)
    ok &= _prop("en «Absència», una renovació al dia: amb 50 min (de 46) ja n'hi ha prou",
                d["estat"] == "repos" and d["higiene_pendent"] == 0, d)
    d = _d(mode="Prioritzar ventilació", td_int=11.0, td_baixa=13.0)
    ok &= _prop("«Prioritzar ventilació» → renova encara que mulli",
                d["estat"] == "higiene" and d["ventiladors"] is True and d["llindar"] == 70, d)
    d = _d(mode="Prioritzar ventilació", td_int=15.0, td_baixa=12.5)
    ok &= _prop("i si a més asseca, és «ventilar»", d["estat"] == "ventilar", d)
    d = _d(mode="Prioritzar ventilació", t_int=11.0)
    ok &= _prop("però el fred el bloqueja", d["estat"] == "bloquejat" and "renovar" in d["motiu"], d)

    print("\nModes")
    d = _d(mode="Ocupat", t_int=11.0, tram="punta")
    ok &= _prop("«Ocupat» → ventiladors engegats fins i tot amb fred; aparell en Nit al llindar del tram",
                d["estat"] == "ocupat" and d["ventiladors"] is True and d["mode_aparell"] == "sleep"
                and d["velocitat"] is None and d["llindar"] == 65, d)
    d = _d(mode="Impressió", t_int=11.0)
    ok &= _prop("«Impressió» → ventiladors engegats fins i tot amb fred; Manual al llindar del tram",
                d["estat"] == "impressio" and d["ventiladors"] is True and d["mode_aparell"] == "normal"
                and d["llindar"] == 60, d)
    d = _d(mode="Silenci", td_int=15.0, td_baixa=12.5, minuts_ventilats=0.0)
    ok &= _prop("«Silenci» → no ventila encara que assequi, i l'aparell en Nit",
                d["estat"] == "repos" and d["ventiladors"] is False and d["mode_aparell"] == "sleep"
                and d["motiu"].startswith("Silenci: "), d)
    d = _d(mode="Llindar fix", tram="punta", hr_max=62.0)
    ok &= _prop("«Llindar fix» → el 55 % sigui quin sigui el tram, i els ventiladors no es toquen",
                d["estat"] == "fix" and d["llindar"] == 55 and d["ventiladors"] is None
                and d["mode_aparell"] == "normal", d)
    ok &= _prop("«Absència» es comporta com «Òptim» quan no hi ha renovació pendent",
                _d(mode="Absència", hr_max=62.0) == {**_d(hr_max=62.0)})

    print("\nFallada segura: cap estat deixa res «per sempre»")
    for estat, kw in [("urgencia", dict(hr_max=80.0)), ("ventilar", dict(td_int=15.0)),
                      ("higiene", dict(minuts_ventilats=0.0, td_int=12.6)), ("repos", {}),
                      ("deshumidificar", dict(hr_max=63.0)), ("ocupat", dict(mode="Ocupat")),
                      ("fix", dict(mode="Llindar fix"))]:
        d = _d(**kw)
        ok &= _prop(f"«{estat}»: el llindar és un número (l'aparell s'atura sol en arribar-hi), mai «continu»",
                    d["estat"] == estat and isinstance(d["llindar"], int) and d["llindar"] >= 40, d)

    print("\nEls fitxers diuen el mateix que la rèplica")
    ok &= tests_fitxers()

    print()
    if ok:
        print("Tots els tests passen.")
        return 0
    print("Hi ha tests que fallen.")
    return 1


def tests_fitxers() -> bool:
    """Els filferros: el que la rèplica suposa dels fitxers de config/, comprovat."""
    ok = True
    macro = MACRO.read_text(encoding="utf-8")
    control = CONTROL.read_text(encoding="utf-8")
    rosada = ROSADA.read_text(encoding="utf-8")

    llista = re.search(r"set PARAMETRES = \[(.*?)\]", macro, re.S)
    a_la_macro = re.findall(r"'(\w+)'", llista.group(1)) if llista else []
    ok &= _prop("la macro espera els mateixos paràmetres que la rèplica, en el mateix ordre",
                a_la_macro == list(PARAMETRES_DE_PARTIDA), a_la_macro)

    passats = re.findall(r"'(\w+)': states\('input_number\.(\w+)'\)", control)
    ok &= _prop("control.yaml els passa tots, cadascun amb el seu input_number",
                sorted(k for k, _ in passats) == sorted(PARAMETRES_DE_PARTIDA)
                and all(k == ent for k, ent in passats), passats)

    partida = {k: float(v) for k, v in re.findall(
        r"input_number\.(\w+) \}\n\s+data: \{ value: ([-\d.]+) \}", control)}
    ok &= _prop("l'inicialitzador de control.yaml posa els mateixos valors de partida",
                partida == {**PARAMETRES_DE_PARTIDA, **PARAMETRES_EXECUTORS}, partida)

    linies = control.split("\n")
    opcions: tuple = ()
    i = next((n for n, l in enumerate(linies) if l.strip() == "mode_soterrani:"), None)
    if i is not None:
        i = next(n for n in range(i, len(linies)) if linies[n].strip() == "options:") + 1
        while i < len(linies) and linies[i].strip().startswith("- "):
            opcions += (linies[i].strip()[2:],)
            i += 1
    ok &= _prop("els modes de l'input_select són els de la rèplica, amb «Òptim» primer",
                opcions == MODES, opcions)
    caducitats = set(re.findall(r"'([^']+)': '\d\d:\d\d:\d\d'", control))
    ok &= _prop("cada caducitat és d'un mode que existeix", caducitats and caducitats <= set(MODES),
                caducitats)

    # sensor.soterrani_humitat_maxima desfà Magnus amb la T CRUA. És exacte
    # mentre el calibratge de T dels tres punts del soterrani sigui zero.
    cts = {}
    for punt in ("fons", "centre", "gran"):
        m = re.search(rf'name: "Soterrani {punt} — punt de rosada".*?set c_t = ([-\d.]+)', rosada, re.S)
        cts[punt] = float(m.group(1)) if m else None
    ok &= _prop("el calibratge de T del soterrani és zero (si no, la HR màxima s'ha de corregir)",
                all(v == 0.0 for v in cts.values()), cts)
    return ok


# ═════════════════════════════════════════════════════════════════════════════
#  CONTRA EL HA DE DEBÒ
# ═════════════════════════════════════════════════════════════════════════════

def _ha() -> tuple[str, str]:
    base = os.environ.get("HA_URL", "").rstrip("/")
    testimoni = os.environ.get("HA_TOKEN", "")
    if not testimoni and os.environ.get("HA_TOKEN_FILE"):
        testimoni = Path(os.environ["HA_TOKEN_FILE"]).expanduser().read_text(encoding="utf-8").strip()
    if not base or not testimoni:
        raise SystemExit("Falten HA_URL i HA_TOKEN (o HA_TOKEN_FILE).")
    return base, testimoni


def _crida(cami: str, cos: dict | None = None, temps: int = 120):
    base, testimoni = _ha()
    peticio = urllib.request.Request(
        f"{base}{cami}", data=json.dumps(cos).encode() if cos is not None else None,
        headers={"Authorization": f"Bearer {testimoni}", "Content-Type": "application/json"})
    with urllib.request.urlopen(peticio, timeout=temps) as resposta:
        return resposta.read().decode()


def casos_aleatoris(n: int, llavor: int = 22092026) -> list[dict]:
    """Casos per a --prova-ha: tots els modes i estats, i molts valors als llindars."""
    rnd = random.Random(llavor)

    def alguna(valor, prob_none=0.06):
        return None if rnd.random() < prob_none else valor

    casos = []
    for _ in range(n):
        td_int = round(rnd.uniform(4, 24), 2)
        e = {
            "calibratge": rnd.random() < 0.04,
            "mode": rnd.choice(MODES + ("unknown",)),
            "referencia": rnd.choice(("Planta baixa", "Exterior", "Planta baixa", "unknown")),
            "td_int": alguna(td_int, 0.03),
            # Molts valors enters: el llindar d'urgència (70) i els del tram cauen justos.
            "hr_max": alguna(rnd.choice([float(rnd.randint(45, 80)), round(rnd.uniform(40, 90), 1)]), 0.03),
            "t_int": alguna(round(rnd.uniform(8, 30), 1), 0.03),
            "marge": None if rnd.random() < 0.6 else round(rnd.uniform(0, 6), 2),
            "td_baixa": alguna(round(td_int + rnd.choice([-2.0, -0.8, 0.0, 0.5]) + rnd.uniform(-3, 3), 2), 0.1),
            "td_ext": alguna(round(td_int + rnd.uniform(-5, 5), 2), 0.1),
            "hr_ext": alguna(float(rnd.randint(40, 100)), 0.1),
            "plou": rnd.random() < 0.15,
            "tram": rnd.choice(("vall", "pla", "punta", None)),
            "minuts_ventilats": alguna(float(rnd.choice([0, 30, 46, 100, 137, 138, 200, rnd.randint(0, 300)])), 0.1),
            "estat_previ": rnd.choice(ESTATS + ("unknown",)),
            "ventila_previ": rnd.random() < 0.3,
            "urgencia_previ": rnd.random() < 0.3,
        }
        p = dict(PARAMETRES_DE_PARTIDA)
        for k in rnd.sample(list(p), rnd.randint(0, 3)):
            p[k] = {
                "delta_td_on": round(rnd.uniform(1, 5), 1), "delta_td_off": round(rnd.uniform(0, 3), 1),
                "delta_td_higiene": round(rnd.uniform(-3, 3), 1), "t_int_minima": rnd.randint(16, 36) / 2,
                "hr_ext_bloqueig": float(rnd.randint(88, 100)), "marge_superficie_min": round(rnd.uniform(1.5, 5), 1),
                "hr_urgencia": float(rnd.randint(60, 85)), "renovacions_dia": rnd.randint(0, 24) / 2,
                "renovacions_absencia": rnd.randint(0, 24) / 2, "cabal_ventiladors": float(rnd.randint(2, 100) * 10),
                "volum_soterrani": float(rnd.randint(10, 60) * 5),
            }.get(k, float(rnd.randint(8, 16) * 5)) if rnd.random() > 0.05 else None
        casos.append({"e": e, "p": p, "m": rnd.randint(1, 1440)})
    return casos


def casos_limit() -> list[dict]:
    """Els casos dels tests, també contra HA: són els que tenen els llindars justos."""
    casos = []
    base = entrades()
    for kw in [
        {}, dict(hr_max=70.0), dict(hr_max=69.9), dict(hr_max=65.0, urgencia_previ=True),
        dict(marge=3.0), dict(marge=2.99), dict(marge=3.49, urgencia_previ=True),
        dict(td_int=14.5), dict(td_int=13.3, ventila_previ=True), dict(td_int=13.29, ventila_previ=True),
        dict(minuts_ventilats=0.0, td_int=12.5), dict(minuts_ventilats=0.0, td_int=12.0, td_baixa=13.0),
        dict(t_int=12.99, td_int=15.0), dict(t_int=13.0, td_int=15.0),
        dict(referencia="Exterior", hr_ext=95.0, td_int=16.0), dict(referencia="Exterior", hr_ext=96.0, td_int=16.0),
        dict(mode="Silenci", hr_max=80.0, td_int=16.0), dict(mode="Llindar fix", hr_max=80.0),
        dict(mode="Ocupat", tram=None), dict(mode="Prioritzar ventilació", t_int=10.0),
        dict(mode="Assecat intensiu"),
        dict(td_int=None), dict(hr_max=None), dict(t_int=None), dict(calibratge=True, mode="Tot aturat"),
    ]:
        casos.append({"e": {**base, **kw}, "p": dict(PARAMETRES_DE_PARTIDA), "m": 138})
    casos.append({"e": entrades(minuts_ventilats=0.0, td_int=12.0, td_baixa=13.0), "p": dict(PARAMETRES_DE_PARTIDA),
                  "m": 138})
    casos.append({"e": entrades(minuts_ventilats=0.0, td_int=12.0, td_baixa=13.0), "p": dict(PARAMETRES_DE_PARTIDA),
                  "m": 139})
    casos.append({"e": entrades(), "p": parametres(delta_td_off=2.0), "m": 600})
    casos.append({"e": entrades(), "p": parametres(hr_fix=None), "m": 600})
    return casos


def prova_ha(n: int = 3000, per_peticio: int = 250) -> int:
    """La macro de debò, avaluada per HA, contra la rèplica: cas a cas, camp a camp."""
    font = MACRO.read_text(encoding="utf-8")
    casos = casos_limit() + casos_aleatoris(n)
    dolents = 0
    for i in range(0, len(casos), per_peticio):
        tanda = casos[i:i + per_peticio]
        dades = json.dumps(tanda, ensure_ascii=False)
        if "'" in dades or "\\" in dades:
            raise SystemExit("Els casos no poden portar cometes simples ni barres: trencarien la plantilla.")
        plantilla = (font + "{%- for c in ('" + dades + "' | from_json) -%}"
                     "{{ decideix(c.e, c.p, c.m) }}\n{% endfor -%}")
        linies = [l for l in _crida("/api/template", {"template": plantilla}).splitlines() if l.strip()]
        if len(linies) != len(tanda):
            print(f"  ❌ tanda {i // per_peticio}: {len(linies)} resultats per a {len(tanda)} casos")
            dolents += len(tanda)
            continue
        for cas, linia in zip(tanda, linies):
            ha = json.loads(linia)
            aqui = decideix(cas["e"], cas["p"], cas["m"])
            if ha != aqui:
                dolents += 1
                if dolents <= 5:
                    dif = {k: (ha.get(k), aqui.get(k)) for k in set(ha) | set(aqui) if ha.get(k) != aqui.get(k)}
                    print(f"  ❌ {json.dumps(cas, ensure_ascii=False)}\n     HA ≠ rèplica: {dif}")
    estats = {decideix(c["e"], c["p"], c["m"])["estat"] for c in casos}
    print(f"  {len(casos)} casos · estats coberts: {len(estats)} de {len(ESTATS)}"
          + (f" (falten {sorted(set(ESTATS) - estats)})" if estats != set(ESTATS) else ""))
    print("✅ HA i la rèplica diuen el mateix, motiu inclòs" if not dolents
          else f"❌ {dolents} casos diferents de {len(casos)}")
    return 1 if dolents or estats != set(ESTATS) else 0


# ─── Test de deriva: el que va gravar el sensor, tornat a decidir ────────────

def _local(instant: datetime) -> datetime:
    """Hora local de Madrid d'un instant UTC, sense zoneinfo (a Windows no hi és).
    La regla europea: estiu de l'últim diumenge de març a l'últim d'octubre, a la 01:00 UTC."""
    def ultim_diumenge(any_: int, mes: int) -> datetime:
        d = date(any_, mes, 31)
        d -= timedelta(days=(d.weekday() + 1) % 7)
        return datetime(d.year, d.month, d.day, 1, tzinfo=timezone.utc)
    u = instant.astimezone(timezone.utc)
    estiu = ultim_diumenge(u.year, 3) <= u < ultim_diumenge(u.year, 10)
    return (u + timedelta(hours=2 if estiu else 1)).replace(tzinfo=None)


def minuts_fins_mitjanit(instant: datetime) -> int:
    local = _local(instant)
    return 1440 - local.hour * 60 - local.minute


def _quan(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def reprodueix(files: list[dict], parametres_hist: dict[str, list[tuple[datetime, str]]]) -> tuple[int, int, list]:
    """Torna a decidir cada fila gravada de la v2. → (comprovades, diferents, exemples)."""
    def valor(nom: str, quan: datetime):
        v = None
        for t, estat in parametres_hist.get(f"input_number.{nom}", []):
            if t <= quan:
                v = estat
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    comprovades, diferents, exemples = 0, 0, []
    for fila in files:
        a = fila.get("attributes") or {}
        if a.get("versio") != "v2" or not isinstance(a.get("entrades"), dict):
            continue
        quan = _quan(fila.get("last_updated") or fila["last_changed"])
        p = {k: valor(k, quan) for k in PARAMETRES_DE_PARTIDA}
        m = minuts_fins_mitjanit(quan)
        gravat = {"estat": fila["state"], "motiu": a.get("motiu"), "llindar": a.get("llindar"),
                  "ventiladors": a.get("ventiladors")}
        # La plantilla s'avalua uns mil·lisegons abans d'escriure la fila: si
        # cau just al canvi de minut, el minut bo és l'anterior.
        encerta = False
        for mm in (m, m + 1):
            d = decideix(a["entrades"], p, mm)
            if {k: d[k] for k in gravat} == gravat:
                encerta = True
                break
        comprovades += 1
        if not encerta:
            diferents += 1
            if len(exemples) < 5:
                exemples.append((fila.get("last_updated"), gravat, {k: d[k] for k in gravat}))
    return comprovades, diferents, exemples


def deriva(hores: float) -> int:
    des = (datetime.now(timezone.utc) - timedelta(hours=hores)).strftime("%Y-%m-%dT%H:%M:%S")
    base = f"/api/history/period/{urllib.parse.quote(des)}"
    decisio = json.loads(_crida(f"{base}?filter_entity_id=sensor.decisio_del_soterrani"
                                "&significant_changes_only=0"))
    # Els paràmetres des d'una setmana abans: cal el valor vigent a l'inici.
    des_p = (datetime.now(timezone.utc) - timedelta(hours=hores + 24 * 7)).strftime("%Y-%m-%dT%H:%M:%S")
    ents = ",".join(f"input_number.{k}" for k in PARAMETRES_DE_PARTIDA)
    cru = json.loads(_crida(f"/api/history/period/{urllib.parse.quote(des_p)}"
                            f"?filter_entity_id={ents}&minimal_response"))
    params: dict[str, list[tuple[datetime, str]]] = {}
    for serie in cru:
        if serie and serie[0].get("entity_id"):
            nom = serie[0]["entity_id"]
            params[nom] = [(_quan(pt.get("last_changed") or pt["last_updated"]), pt["state"]) for pt in serie]
    files = decisio[0] if decisio else []
    comprovades, diferents, exemples = reprodueix(files, params)
    for quan, gravat, rep in exemples:
        print(f"  ❌ {quan}\n     gravat:  {gravat}\n     rèplica: {rep}")
    if not comprovades:
        print("No hi ha cap fila de la v2 en aquest període: no es pot dir res.")
        return 1
    print(f"{'✅' if not diferents else '❌'} {comprovades} files de la v2, {diferents} diferents")
    return 1 if diferents else 0


def tests_deriva() -> bool:
    """La reconstrucció de --deriva, amb una fila feta a mà (sense xarxa)."""
    ok = True
    ok &= _prop("hora local: 22/09/2026 21:30 UTC són les 23:30 (estiu)",
                _local(datetime(2026, 9, 22, 21, 30, tzinfo=timezone.utc)) == datetime(2026, 9, 22, 23, 30))
    ok &= _prop("hora local: 15/01/2027 22:59 UTC són les 23:59 (hivern)",
                minuts_fins_mitjanit(datetime(2027, 1, 15, 22, 59, tzinfo=timezone.utc)) == 1)
    quan = datetime(2026, 9, 22, 9, 0, 30, tzinfo=timezone.utc)
    e = entrades(minuts_ventilats=0.0, td_int=12.0, td_baixa=13.0)
    m = minuts_fins_mitjanit(quan)
    d = decideix(e, parametres(), m)
    fila = {"state": d["estat"], "last_updated": quan.isoformat(),
            "attributes": {"versio": "v2", "entrades": e, "motiu": d["motiu"], "llindar": d["llindar"],
                           "ventiladors": d["ventiladors"]}}
    hist = {f"input_number.{k}": [(quan - timedelta(days=1), str(v))] for k, v in PARAMETRES_DE_PARTIDA.items()}
    ok &= _prop("una fila gravada es torna a decidir igual", reprodueix([fila], hist) == (1, 0, []))
    hist["input_number.hr_pla"] = [(quan - timedelta(days=1), "60.0"), (quan + timedelta(seconds=5), "55.0")]
    ok &= _prop("i fa servir el paràmetre vigent en aquell moment, no el d'ara",
                reprodueix([fila], hist)[1] == 0)
    fila_dolenta = {**fila, "state": "ventilar"}
    ok &= _prop("i una fila que no quadra, la troba", reprodueix([fila_dolenta], hist)[1] == 1)
    ok &= _prop("les files de la v1 (sense «versio») no es comproven",
                reprodueix([{**fila, "attributes": {"motiu": "x"}}], hist)[0] == 0)
    return ok


def main(argv: list[str]) -> int:
    if "--prova-ha" in argv:
        return prova_ha()
    if "--deriva" in argv:
        i = argv.index("--deriva")
        return deriva(float(argv[i + 1]) if len(argv) > i + 1 else 24)
    resultat = tests()
    print("\nTest de deriva, sense xarxa")
    deriva_ok = tests_deriva()
    print("\nLa reconstrucció de --deriva funciona." if deriva_ok
          else "\nLa reconstrucció de --deriva falla.")
    return resultat or (0 if deriva_ok else 1)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
