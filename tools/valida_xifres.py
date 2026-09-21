#!/usr/bin/env python3
"""Comprova que les xifres de línies citades als documents quadrin amb els fitxers.

Els documents diuen quantes línies fa cada fitxer de codi —«`docker-compose.yml`
(**149**)», «`scripts/comprova.sh` (288 línies)»— i, cada cop que es toca un
d'aquests fitxers, la xifra queda vella sense que ningú se n'adoni. Va passar
quatre vegades en una sola sessió (PR #16, #17 i #19). Això ho troba abans.

    python3 tools/valida_xifres.py

Es corre ABANS D'OBRIR CADA PR, igual que el repàs de dades personals.

Què reconeix, a tots els `.md` versionats (mai `docs/privat/`):

  · «`fitxer` (N)», «`fitxer` (**N**)», «`fitxer` (N línies)»  → exacte
  · «YAML de compose (N línies)»                               → exacte, és el compose
  · «`fitxer` (~N)»                                            → aproximat
  · «~N línies» en una línia que cita dos fitxers o més amb    → aproximat, contra la
    la seva xifra                                                suma d'aquells fitxers

El nom es resol al fitxer real: valen `docker-compose.yml`, `packages/rosada.yaml`
o `rosada.yaml`, mentre només n'hi hagi un que hi encaixi. Si n'hi ha dos, és
una falla: el document ha de dir el camí sencer.

Les aproximades toleren un 2 % o 10 línies, el que sigui més gran: prou per a un
arrodoniment, i prou poc perquè un fitxer nou no hi passi desapercebut.

Què NO fa, a posta:

  · No mira xifres en prosa o en diagrames sense backticks («rosada.yaml, ~566
    línies»). Endevinar a quin fitxer es refereix una xifra solta donaria falses
    alarmes, i una eina que avisa en fals acaba ignorada.
  · No mira totals que en sumen d'altres escrits en una altra línia (el «~N
    línies en total» que ve després de «Ja escrits» i «Per escriure»).
  · Salta el que està ratllat amb ~~ ~~, que és com el repositori marca el que
    ha quedat superat. Per citar una xifra vella a posta, ratlla-la.
  · Un fitxer citat amb «~N» que encara no existeix és un pla («Per escriure»)
    i se salta. El dia que existeixi, es començarà a comprovar sol —i fallarà si
    ningú no l'ha passat a «Ja escrits» amb la xifra de debò, que és el que toca.

Surt amb codi 1 si alguna xifra no quadra, o si no en troba cap: una eina que no
troba res segurament s'ha trencat, i callar seria un fals verd.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

# La consola de Windows és cp1252 per defecte i peta amb «í» o «⚠». El
# repositori s'edita des de Windows i s'executa a Linux: ha de funcionar als dos.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TOLERANCIA_REL = 0.02
TOLERANCIA_MIN = 10

# Un nom entre backticks només és un fitxer si acaba en una d'aquestes
# extensions. Sense això, `sensor.decisio_del_soterrani` seria un «fitxer».
EXTENSIONS = {
    "py", "sh", "yaml", "yml", "md", "json", "js", "ts", "css", "html",
    "toml", "conf", "ini", "sql", "txt", "jinja",
}

# Noms que els documents fan servir en comptes del camí del fitxer.
ALIES = {"YAML de compose": "docker-compose.yml"}

NUM = r"\d{1,3}(?:\.\d{3})+|\d+"  # «1.900» o «149»: el punt és de milers

RE_FITXER = re.compile(
    r"`(?P<nom>[\w./-]+)`\s*\(\s*(?:\*\*)?\s*(?P<aprox>~)?\s*(?P<n>" + NUM + r")"
    r"\s*(?:\*\*)?\s*(?:línies)?\s*(?:\*\*)?\s*\)"
)
RE_ALIES = re.compile(
    r"(?P<nom>" + "|".join(map(re.escape, ALIES)) + r")\s*\(\s*(?P<aprox>~)?\s*"
    r"(?P<n>" + NUM + r")\s*línies\s*\)"
)
RE_TOTAL = re.compile(r"~\s*(?P<n>" + NUM + r")\s*(?:\*\*)?\s*línies")
RE_RATLLAT = re.compile(r"~~.+?~~")


def num(text: str) -> int:
    return int(text.replace(".", ""))


def fmt(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def sembla_fitxer(nom: str) -> bool:
    return "." in nom and nom.rsplit(".", 1)[1].lower() in EXTENSIONS


def fitxers_versionats(arrel: Path) -> list[str]:
    """Els versionats i els nous que encara no ho són, però mai els ignorats.

    Els nous hi han de ser: l'eina es corre ABANS del commit, i un fitxer que
    s'acaba d'escriure i de citar als documents encara no és a l'índex. Els
    ignorats no: així `docs/privat/` i `config/.storage/` queden fora sols.
    """
    try:
        sortida = subprocess.run(
            ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            cwd=arrel, capture_output=True, check=True,
        ).stdout
        # «--cached» inclou els esborrats que encara són a l'índex.
        return [
            p for p in dict.fromkeys(sortida.decode("utf-8").split("\0"))
            if p and (arrel / p).is_file()
        ]
    except (OSError, subprocess.CalledProcessError):
        # Sense git: tot el que hi ha, fora de .git i de docs/privat.
        tots = []
        for p in arrel.rglob("*"):
            rel = p.relative_to(arrel).as_posix()
            if p.is_file() and ".git" not in p.parts and not rel.startswith("docs/privat/"):
                tots.append(rel)
        return tots


def resol(nom: str, fitxers: list[str]) -> list[str]:
    if nom in fitxers:
        return [nom]
    return [f for f in fitxers if f.endswith("/" + nom)]


def dins_tolerancia(diu: int, real: int) -> bool:
    return abs(diu - real) <= max(TOLERANCIA_MIN, TOLERANCIA_REL * real)


def main(arrel: Path | None = None) -> int:
    arrel = arrel or Path(__file__).resolve().parent.parent
    fitxers = fitxers_versionats(arrel)
    docs = sorted(
        f for f in fitxers if f.endswith(".md") and not f.startswith("docs/privat/")
    )

    mides: dict[str, int] = {}

    def linies(rel: str) -> int:
        if rel not in mides:
            text = (arrel / rel).read_text(encoding="utf-8", errors="replace")
            mides[rel] = len(text.splitlines())
        return mides[rel]

    comprovades = falles = avisos = 0

    def ok(missatge: str) -> None:
        nonlocal comprovades
        comprovades += 1
        print(f"  OK     {missatge}")

    def falla(missatge: str) -> None:
        nonlocal comprovades, falles
        comprovades += 1
        falles += 1
        print(f"  FALLA  {missatge}")

    def avis(missatge: str) -> None:
        nonlocal avisos
        avisos += 1
        print(f"  AVÍS   {missatge}")

    for doc in docs:
        cami = arrel / doc
        if not cami.is_file():
            continue
        for n_linia, text in enumerate(
            cami.read_text(encoding="utf-8", errors="replace").splitlines(), 1
        ):
            lloc = f"{doc}:{n_linia}"
            ratllats = [m.span() for m in RE_RATLLAT.finditer(text)]

            def ratllat(pos: int) -> bool:
                return any(a <= pos < b for a, b in ratllats)

            reals_citats: list[int] = []
            mascara = list(text)
            coincidencies = sorted(
                [*RE_FITXER.finditer(text), *RE_ALIES.finditer(text)],
                key=lambda m: m.start(),
            )
            for m in coincidencies:
                # Tapar-la perquè el «~N línies» de dins no compti com a total.
                for i in range(*m.span()):
                    mascara[i] = " "
                if ratllat(m.start()):
                    continue
                es_alies = m.re is RE_ALIES
                nom = ALIES[m["nom"]] if es_alies else m["nom"]
                if not es_alies and not sembla_fitxer(nom):
                    continue
                aprox = bool(m["aprox"])
                diu = num(m["n"])

                trobats = resol(nom, fitxers)
                if not trobats:
                    if not aprox:
                        avis(f"{lloc}  «{nom}» no existeix: si s'ha reanomenat o "
                             f"esborrat, aquesta xifra ja no es comprova")
                    continue
                if len(trobats) > 1:
                    falla(f"{lloc}  «{nom}» és ambigu ({', '.join(trobats)}): "
                          f"posa-hi el camí sencer")
                    continue

                rel = trobats[0]
                real = linies(rel)
                reals_citats.append(real)
                if aprox:
                    if dins_tolerancia(diu, real):
                        ok(f"{lloc}  {rel} ≈ {fmt(diu)} (en fa {fmt(real)})")
                    else:
                        falla(f"{lloc}  {rel}: diu ~{fmt(diu)}, en fa {fmt(real)}")
                elif diu == real:
                    ok(f"{lloc}  {rel} = {fmt(real)}")
                else:
                    falla(f"{lloc}  {rel}: diu {fmt(diu)}, en fa {fmt(real)}")

            # El total d'una llista de fitxers, com el de «Ja escrits».
            if len(reals_citats) >= 2:
                suma = sum(reals_citats)
                for m in RE_TOTAL.finditer("".join(mascara)):
                    if ratllat(m.start()):
                        continue
                    diu = num(m["n"])
                    if dins_tolerancia(diu, suma):
                        ok(f"{lloc}  total ~{fmt(diu)} (la suma real és {fmt(suma)})")
                    else:
                        falla(f"{lloc}  total: diu ~{fmt(diu)}, i els fitxers "
                              f"d'aquesta línia en sumen {fmt(suma)}")

    print()
    if comprovades == 0:
        print("No he trobat cap xifra de línies als documents. Segurament s'ha trencat "
              "l'eina o ha canviat el format: no ho dono per bo.")
        return 1
    cua = f" · {avisos} avís(os)" if avisos else ""
    if falles:
        print(f"{falles} xifra(es) desquadrada(es) de {comprovades}{cua}.")
        return 1
    print(f"{comprovades} xifres comprovades, totes quadren{cua}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
