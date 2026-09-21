#!/usr/bin/env python3
"""El calendari de trams de la 2.0TD, escrit per segona vegada per vigilar el primer.

QUÈ RESOL
─────────
El cost de l'endoll depèn de saber, per a cada hora, si és punta, pla o vall.
Això ho decideix config/custom_templates/tarifa.jinja dins de Home Assistant.
Aquí hi ha el mateix calendari escrit en Python, de manera independent, per
poder-los comparar i per treure la taula de festius que va als documents.

    python3 tools/tarifa.py --prova                # tests, sense xarxa
    python3 tools/tarifa.py --festius 2026 2036    # taula de festius en vall
    python3 tools/tarifa.py --prova-ha             # contra el HA de debò

LA REGLA (Circular CNMC 3/2020, art. 7.3, península)
────────────────────────────────────────────────────
Punta 10–14 i 18–22 · pla 8–10, 14–18 i 22–24 · vall 0–8, de dilluns a
divendres feiners. Vall tot el dia: dissabtes, diumenges, el 6 de gener i els
festius nacionals «con exclusión tanto de los festivos sustituibles como de los
que no tienen fecha fija». Els festius, doncs, són una REGLA de data fixa i no
una llista per any: serveix per a qualsevol any mentre no canviï la llei.

⚠️ Divendres Sant NO és vall (no té data fixa), ni el dilluns que trasllada un
   festiu caigut en diumenge, ni cap festiu català o de Barcelona.

--prova-ha demana al HA que avaluï tarifa.jinja a cada frontera de tram (el
minut d'abans i el de després) de cada dia de 2026 a 2036, i ho compara. Un any
per petició perquè el HA avalua plantilles al fil principal i no s'ha de
bloquejar. Fa servir HA_URL i HA_TOKEN (o HA_TOKEN_FILE), com calibratge.py.

Només biblioteca estàndard. Surt amb codi 1 si hi ha cap discrepància.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# RD 2001/1983, art. 45.1, apartats a), b) i c) —els de data fixa— més el
# 6 de gener, que la circular hi afegeix expressament perquè és substituïble.
FESTIUS = {
    (1, 1): "Any Nou",
    (1, 6): "Reis",
    (5, 1): "Festa del Treball",
    (8, 15): "l'Assumpció",
    (10, 12): "Festa Nacional d'Espanya",
    (11, 1): "Tots Sants",
    (12, 6): "la Constitució",
    (12, 8): "la Immaculada",
    (12, 25): "Nadal",
}
PUNTA = (10, 11, 12, 13, 18, 19, 20, 21)
FRONTERES = (0, 8, 10, 14, 18, 22)   # hores en què pot canviar el tram
DIES = ("dl", "dt", "dc", "dj", "dv", "ds", "dg")


def tram(dia: date, hora: int) -> str:
    """El tram d'una hora local sencera."""
    if dia.weekday() >= 5 or (dia.month, dia.day) in FESTIUS or hora < 8:
        return "vall"
    return "punta" if hora in PUNTA else "pla"


# ─── Hora local de Madrid sense zoneinfo ─────────────────────────────────────
# A Windows, zoneinfo no porta la base de dades de zones i aquesta eina ha de
# córrer a casa. La regla europea és prou simple per escriure-la: horari
# d'estiu de l'últim diumenge de març a l'últim d'octubre, a la 01:00 UTC.

def _ultim_diumenge(any_: int, mes: int) -> date:
    d = date(any_, mes, 31)
    return d - timedelta(days=(d.weekday() + 1) % 7)


def a_utc(local: datetime) -> float:
    """Segons UNIX d'una hora local de Madrid (sense tz)."""
    y = local.year
    inici = datetime.combine(_ultim_diumenge(y, 3), datetime.min.time()) + timedelta(hours=2)
    fi = datetime.combine(_ultim_diumenge(y, 10), datetime.min.time()) + timedelta(hours=3)
    desfas = 2 if inici <= local < fi else 1
    return (local - timedelta(hours=desfas)).replace(tzinfo=timezone.utc).timestamp()


def pasqua(any_: int) -> date:
    """Diumenge de Pasqua (algorisme gregorià anònim)."""
    a, b, c = any_ % 19, any_ // 100, any_ % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mes = (h + l - 7 * m + 114) // 31
    return date(any_, mes, (h + l - 7 * m + 114) % 31 + 1)


def taula_festius(inici: int, fi: int) -> str:
    """Markdown: per any, els festius que cauen entre setmana (els que compten)."""
    files = ["| Any | Festius en vall que cauen entre setmana | Divendres Sant (**no** és vall) |",
             "|---|---|---|"]
    for y in range(inici, fi + 1):
        dies = [date(y, m, d) for (m, d) in FESTIUS if date(y, m, d).weekday() < 5]
        text = " · ".join(f"{DIES[d.weekday()]} {d.day}/{d.month}" for d in sorted(dies))
        vs = pasqua(y) - timedelta(days=2)
        files.append(f"| {y} | {len(dies)}: {text} | {vs.day}/{vs.month} |")
    return "\n".join(files)


# ─── Tests sense xarxa ───────────────────────────────────────────────────────

def tests() -> int:
    fallades = 0

    def prop(nom, condicio):
        nonlocal fallades
        print(f"  {'✅' if condicio else '❌'} {nom}")
        fallades += not condicio

    print("Calendari")
    prop("dilluns 21/09/2026 a les 7 → vall", tram(date(2026, 9, 21), 7) == "vall")
    prop("dilluns 21/09/2026 a les 8 → pla", tram(date(2026, 9, 21), 8) == "pla")
    prop("dilluns 21/09/2026 a les 10 → punta", tram(date(2026, 9, 21), 10) == "punta")
    prop("dilluns 21/09/2026 a les 22 → pla", tram(date(2026, 9, 21), 22) == "pla")
    prop("dissabte a les 12 → vall", tram(date(2026, 9, 26), 12) == "vall")
    prop("dimecres 6/1/2027 a les 12 → vall", tram(date(2027, 1, 6), 12) == "vall")
    prop("Divendres Sant 2027 (26/3) a les 12 → punta", tram(date(2027, 3, 26), 12) == "punta")
    prop("Sant Esteve 2029 (dc 26/12) a les 12 → punta", tram(date(2029, 12, 26), 12) == "punta")
    prop("dilluns 7/12/2026, trasllat de la Constitució → punta", tram(date(2026, 12, 7), 12) == "punta")
    hores = [tram(date(2026, 9, 21), h) for h in range(24)]
    prop("un dia feiner: 8 h de vall, 8 de pla i 8 de punta",
         (hores.count("vall"), hores.count("pla"), hores.count("punta")) == (8, 8, 8))

    print("Hora local")
    prop("25/10/2026 01:30 és estiu (+2)", a_utc(datetime(2026, 10, 25, 1, 30))
         == datetime(2026, 10, 24, 23, 30, tzinfo=timezone.utc).timestamp())
    prop("25/10/2026 04:00 és hivern (+1)", a_utc(datetime(2026, 10, 25, 4))
         == datetime(2026, 10, 25, 3, tzinfo=timezone.utc).timestamp())
    prop("28/03/2027 03:00 és estiu (+2)", a_utc(datetime(2027, 3, 28, 3))
         == datetime(2027, 3, 28, 1, tzinfo=timezone.utc).timestamp())
    prop("Pasqua 2027 = 28/3, 2030 = 21/4", pasqua(2027) == date(2027, 3, 28)
         and pasqua(2030) == date(2030, 4, 21))

    print("✅ Tot bé" if not fallades else f"❌ {fallades} fallades")
    return 1 if fallades else 0


# ─── Contra el HA de debò ────────────────────────────────────────────────────

def _post_plantilla(plantilla: str) -> str:
    base = os.environ.get("HA_URL", "").rstrip("/")
    testimoni = os.environ.get("HA_TOKEN", "")
    if not testimoni and os.environ.get("HA_TOKEN_FILE"):
        testimoni = Path(os.environ["HA_TOKEN_FILE"]).expanduser().read_text(encoding="utf-8").strip()
    if not base or not testimoni:
        raise SystemExit("Falten HA_URL i HA_TOKEN (o HA_TOKEN_FILE).")
    peticio = urllib.request.Request(
        f"{base}/api/template", data=json.dumps({"template": plantilla}).encode(),
        headers={"Authorization": f"Bearer {testimoni}", "Content-Type": "application/json"})
    with urllib.request.urlopen(peticio, timeout=60) as resposta:
        return resposta.read().decode()


def prova_ha(inici: int = 2026, fi: int = 2036) -> int:
    total = dolents = 0
    for y in range(inici, fi + 1):
        instants: list[tuple[datetime, str]] = []
        dia = date(y, 1, 1)
        while dia.year == y:
            for h in FRONTERES:
                for local in (datetime.combine(dia, datetime.min.time()) + timedelta(hours=h, minutes=-1),
                              datetime.combine(dia, datetime.min.time()) + timedelta(hours=h)):
                    instants.append((local, tram(local.date(), local.hour)))
            dia += timedelta(days=1)
        # Cap frontera cau entre les 2 i les 3, que és on hi ha el canvi d'hora:
        # totes les hores provades existeixen i són úniques.
        tss = [int(a_utc(local)) for local, _ in instants]
        plantilla = ("{% from 'tarifa.jinja' import tram %}"
                     "{% for ts in " + json.dumps(tss) + " %}{{ tram(ts) | trim }},{% endfor %}")
        resposta = _post_plantilla(plantilla).strip().rstrip(",").split(",")
        errors = [(local, esperat, r) for (local, esperat), r in zip(instants, resposta) if r != esperat]
        total += len(instants)
        dolents += len(errors) + abs(len(resposta) - len(instants))
        print(f"  {y}: {len(instants)} instants, {len(errors)} discrepàncies", *errors[:3])
    print("✅ HA i la referència diuen el mateix" if not dolents
          else f"❌ {dolents} discrepàncies de {total}")
    return 1 if dolents else 0


def main(argv: list[str]) -> int:
    if "--festius" in argv:
        i = argv.index("--festius")
        inici, fi = (int(argv[i + 1]), int(argv[i + 2])) if len(argv) > i + 2 else (2026, 2036)
        print(taula_festius(inici, fi))
        return 0
    if "--prova-ha" in argv:
        return prova_ha()
    if "--prova" in argv or not argv:
        return tests()
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
