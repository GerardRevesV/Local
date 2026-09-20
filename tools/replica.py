#!/usr/bin/env python3
"""Rèplica offline de la lògica del punt de rosada.

PER A QUÈ SERVEIX
─────────────────
1. **Fixar els llindars amb dades pròpies.** Es passa sobre les quatre setmanes
   gravades a la Fase B i respon la pregunta que decideix si la Fase C val la
   pena: *quantes hores hauria ventilat amb cada joc de llindars?*
2. **Test de deriva.** Es compara amb el que va registrar de debò
   `sensor.decisio_soterrani`. Si divergeixen, les dues implementacions
   —aquesta i el YAML— han derivat, i cal saber-ho.

⚠️ Aquesta funció NO decideix res en producció. La decisió en viu la pren
   `config/packages/rosada.yaml`, i punt. Duplicar la lògica és un cost
   acceptat conscientment (vegeu decisio-stack.md); el que el fa acceptable és
   precisament el test de deriva.

    python3 tools/replica.py            # executa els tests
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass

# Coeficients de Magnus — Alduchov & Eskridge (1996).
# Error de la fórmula: ±0,1 °C entre −40 i +50 °C.
# La consola de Windows és cp1252 per defecte i peta amb «°» o «≈». El
# repositori s'edita des de Windows i s'executa a Linux: ha de funcionar als dos.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

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


@dataclass(frozen=True)
class Llindars:
    """Els mateixos paràmetres que els `input_number` de rosada.yaml."""

    delta_on: float = 2.0
    delta_off: float = 0.8
    hr_objectiu: float = 55.0
    marge_minim: float = 3.0
    t_interior_minima: float = 13.0
    hr_exterior_bloqueig: float = 95.0

    def __post_init__(self) -> None:
        if self.delta_off >= self.delta_on:
            raise ValueError(
                f"delta_off ({self.delta_off}) ha de ser menor que "
                f"delta_on ({self.delta_on}): sense banda morta el relé repica"
            )


@dataclass(frozen=True)
class Lectura:
    """Una mostra del conjunt de sensors en un instant."""

    td_interior: float | None
    td_exterior: float | None
    t_interior: float | None
    hr_exterior: float | None = None
    marge_condensacio: float | None = None
    plou: bool = False


@dataclass(frozen=True)
class Decisio:
    estat: str
    motiu: str


def decideix(lectura: Lectura, llindars: Llindars, estat_previ: str = "repos") -> Decisio:
    """Rèplica exacta de `sensor.decisio_soterrani`.

    Qualsevol canvi aquí s'ha de fer també a `config/packages/rosada.yaml`,
    i el test de deriva ho comprovarà sobre dades reals.
    """
    # 1. Fallada segura: sense dada fiable no es decideix res.
    if lectura.td_interior is None:
        return Decisio("sense_dades", "Sense punt de rosada interior fiable")
    if lectura.td_exterior is None:
        return Decisio("sense_dades", "Sense punt de rosada exterior fiable")
    if lectura.t_interior is None:
        return Decisio("sense_dades", "Sense temperatura interior fiable")

    delta = lectura.td_interior - lectura.td_exterior

    # 2. Bloquejos. Qualsevol d'ells veta la ventilació.
    if lectura.t_interior < llindars.t_interior_minima:
        return Decisio(
            "bloquejat",
            f"Massa fred a dins ({lectura.t_interior:.1f} °C): "
            "ventilar refredaria les parets",
        )
    if (
        lectura.hr_exterior is not None
        and lectura.hr_exterior > llindars.hr_exterior_bloqueig
    ):
        return Decisio(
            "bloquejat",
            f"HR exterior al {lectura.hr_exterior:.0f} %: el sensor pot estar mullat",
        )
    if lectura.plou:
        return Decisio("bloquejat", "Plou segons l'estació oficial")

    # 3. Objectiu assolit: si ja hi som, no cal fer res.
    td_objectiu = punt_de_rosada(lectura.t_interior, llindars.hr_objectiu)
    marge_ok = (
        lectura.marge_condensacio is None
        or lectura.marge_condensacio >= llindars.marge_minim
    )
    if lectura.td_interior <= td_objectiu and marge_ok:
        return Decisio("repos", "Objectiu assolit")

    # 4. Histèresi: el llindar depèn de si ja ventilàvem.
    llindar = llindars.delta_off if estat_previ == "ventilar" else llindars.delta_on

    if delta >= llindar:
        return Decisio("ventilar", f"Fora asseca: ΔTd = {delta:.2f} °C")
    if delta <= llindars.delta_off:
        return Decisio("deshumidificar", f"Fora no asseca prou: ΔTd = {delta:.2f} °C")
    return Decisio("deshumidificar", f"ΔTd = {delta:.2f} °C, dins de la banda morta")


# ═════════════════════════════════════════════════════════════════════════════
#  TESTS
# ═════════════════════════════════════════════════════════════════════════════

def _prop(nom: str, condicio: bool, detall: str = "") -> bool:
    marca = "OK  " if condicio else "FALLA"
    print(f"  {marca} {nom}{('  — ' + detall) if detall and not condicio else ''}")
    return condicio


def tests() -> int:
    ok = True
    print("Fórmula de Magnus")

    # Valors de referència calculats amb els coeficients d'Alduchov & Eskridge.
    for t, hr, esperat in [
        (20.0, 75.0, 15.44),
        (30.0, 65.0, 22.71),
        (20.0, 100.0, 20.00),
        (22.4, 66.0, 15.74),   # lectura real de «Centre», 20/09/2026
        (23.9, 68.0, 17.64),   # lectura real de «Fora», 20/09/2026
    ]:
        obtingut = punt_de_rosada(t, hr)
        ok &= _prop(
            f"Td({t} °C, {hr} %) ≈ {esperat} °C",
            abs(obtingut - esperat) < 0.05,
            f"obtingut {obtingut:.2f}",
        )

    ok &= _prop(
        "a HR 100 % el punt de rosada és la temperatura",
        abs(punt_de_rosada(17.3, 100.0) - 17.3) < 0.01,
    )
    ok &= _prop(
        "HR 0 % no peta (es limita a 1 %)",
        punt_de_rosada(20.0, 0.0) < -20,
    )
    ok &= _prop(
        "el punt de rosada creix amb la humitat",
        punt_de_rosada(20, 40) < punt_de_rosada(20, 60) < punt_de_rosada(20, 80),
    )

    print("\nEl cas que motiva el projecte")
    # 20/09/2026: fora SEMBLA més sec (68 % < 66 %? no: 68 > 66) però el que
    # compta és el punt de rosada, i el de fora és més alt → ventilar mullaria.
    interior = punt_de_rosada(22.4, 66.0)
    exterior = punt_de_rosada(23.9, 68.0)
    ok &= _prop(
        "amb les lectures reals del 20/09/2026, ventilar afegiria aigua",
        exterior > interior,
        f"int {interior:.2f} vs ext {exterior:.2f}",
    )
    d = decideix(
        Lectura(td_interior=interior, td_exterior=exterior, t_interior=22.4, hr_exterior=68.0),
        Llindars(),
    )
    ok &= _prop("i la lògica NO diu «ventilar»", d.estat != "ventilar", d.estat)

    # El cas clàssic d'error: l'estiu de Barcelona.
    ok &= _prop(
        "estiu: fora al 65 % d'HR i 30 °C porta MÉS aigua que dins al 75 % i 20 °C",
        punt_de_rosada(30, 65) > punt_de_rosada(20, 75),
    )

    print("\nHistèresi")
    llindars = Llindars()
    base = dict(t_interior=20.0, hr_exterior=60.0)
    # ΔTd = 1,5: entre delta_off (0,8) i delta_on (2,0) → banda morta.
    parat = decideix(Lectura(td_interior=16.0, td_exterior=14.5, **base), llindars, "repos")
    ventilant = decideix(Lectura(td_interior=16.0, td_exterior=14.5, **base), llindars, "ventilar")
    ok &= _prop("a la banda morta, si estava parat no arrenca", parat.estat != "ventilar", parat.estat)
    ok &= _prop("a la banda morta, si ventilava continua", ventilant.estat == "ventilar", ventilant.estat)

    ok &= _prop(
        "ΔTd per sobre de delta_on arrenca des de parat",
        decideix(Lectura(td_interior=16.0, td_exterior=13.5, **base), llindars, "repos").estat
        == "ventilar",
    )
    ok &= _prop(
        "ΔTd per sota de delta_off atura encara que ventilés",
        decideix(Lectura(td_interior=16.0, td_exterior=15.5, **base), llindars, "ventilar").estat
        != "ventilar",
    )

    print("\nBloquejos i fallada segura")
    for nom, lectura, esperat in [
        ("sense Td interior", Lectura(None, 10.0, 20.0), "sense_dades"),
        ("sense Td exterior", Lectura(16.0, None, 20.0), "sense_dades"),
        ("sense T interior", Lectura(16.0, 10.0, None), "sense_dades"),
        ("massa fred a dins", Lectura(16.0, 10.0, 11.0), "bloquejat"),
        ("HR exterior al 98 %", Lectura(16.0, 10.0, 20.0, hr_exterior=98.0), "bloquejat"),
        ("plou", Lectura(16.0, 10.0, 20.0, plou=True), "bloquejat"),
    ]:
        obtingut = decideix(lectura, llindars)
        ok &= _prop(f"{nom} → {esperat}", obtingut.estat == esperat, obtingut.estat)

    ok &= _prop(
        "el bloqueig per fred guanya encara que fora asseques molt",
        decideix(Lectura(20.0, 2.0, 9.0), llindars).estat == "bloquejat",
    )

    print("\nObjectiu i marge de condensació")
    # A 20 °C, l'objectiu del 55 % d'HR són ~10,7 °C de punt de rosada.
    objectiu = punt_de_rosada(20.0, 55.0)
    ok &= _prop(
        "per sota de l'objectiu i amb marge, repòs",
        decideix(Lectura(objectiu - 1, 5.0, 20.0, marge_condensacio=4.0), llindars).estat
        == "repos",
    )
    ok &= _prop(
        "per sota de l'objectiu però amb marge insuficient, NO es queda en repòs",
        decideix(Lectura(objectiu - 1, 5.0, 20.0, marge_condensacio=1.0), llindars).estat
        != "repos",
        "un marge petit vol dir que la paret condensa encara que l'aire sembli sec",
    )
    ok &= _prop(
        "sense sensor de paret, el marge no bloqueja (es tracta com a «sense dada»)",
        decideix(Lectura(objectiu - 1, 5.0, 20.0, marge_condensacio=None), llindars).estat
        == "repos",
    )

    print("\nValidació dels paràmetres")
    try:
        Llindars(delta_on=1.0, delta_off=1.5)
        ok &= _prop("delta_off >= delta_on ha de petar", False)
    except ValueError:
        ok &= _prop("delta_off >= delta_on peta amb un error clar", True)

    print()
    if ok:
        print("Tots els tests passen.")
        return 0
    print("Hi ha tests que fallen.")
    return 1


if __name__ == "__main__":
    sys.exit(tests())
