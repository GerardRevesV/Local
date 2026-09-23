#!/usr/bin/env python3
"""Comprova que els enllaços amb àncora dels documents portin a un títol que existeixi.

Els documents s'enllacen entre ells per títol —«[inventari.md](inventari.md#deshumidificador)»—,
i l'àncora és el títol convertit en *slug*. Quan un títol es reanomena, o es
ratlla i s'hi afegeix «→ ✅ resolta», l'enllaç continua semblant bo i porta a dalt
de tot de la pàgina. Va passar amb la contradicció del manual (PR #60), i no ho
va veure ningú perquè cap eina no mirava les àncores. Això ho troba abans.

    python3 tools/valida_ancores.py        # només les falles i el resum
    python3 tools/valida_ancores.py -v     # també cada enllaç que resol

Es corre ABANS D'OBRIR CADA PR, al costat de `valida_xifres.py`.

Què mira: `README.md`, `CLAUDE.md` i `docs/**/*.md`, mai `docs/privat/`. Hi busca
«[text](fitxer.md#àncora)» i «[text](#àncora)», i falla si el fitxer no existeix o
si no hi ha cap títol ni cap `<a id="…">` / `<a name="…">` amb aquella àncora.

L'àncora es calcula com GitHub, que és on es llegeixen:

  · el text del títol tal com es veu: sense ~~ ** * _ ni backticks, dels enllaços
    només el text, sense etiquetes HTML (el que hi ha dins dels backticks es queda
    tal qual, `input_select` inclòs);
  · en minúscules;
  · fora tot el que no sigui lletra, marca, dígit, puntuació de connexió (`_`),
    «-» o espai —els emojis, «→», «—», «:», «/» se'n van—, SENSE ajuntar els espais;
  · cada espai, un «-». Per això «provar~~ → ✅ resolta» dona «provar---resolta».
  · Si dos títols donen el mateix, el segon porta «-1», el tercer «-2»…

Els títols de dins d'una cita («> ### …») també tenen àncora, i compten. El que
hi ha dins dels blocs de codi (``` o ~~~, també dins d'una cita) i dels backticks
no és ni títol ni enllaç: `# … canvis …` en un bloc de bash no és un títol.
L'àncora de l'enllaç es descodifica (%C3%B3 → ó) abans de comparar-la.

Què NO fa, a posta:

  · No mira els enllaços sense àncora, ni els externs (http…), ni els de
    referència («[x]: fitxer.md#…») o d'HTML (`<a href>`), ni l'àncora dels
    fitxers que no són `.md` (de `control.yaml#L12` només mira que el fitxer hi
    sigui).
  · No coneix els títols subratllats (`===` / `---` a sota) ni els d'HTML
    (`<h2>`), ni els emojis escrits com a `:nom:`. El repositori no en fa servir;
    el dia que n'hi hagi, cal ensenyar-l'hi.
  · No perdona majúscules: GitHub genera l'àncora en minúscules i un enllaç que
    només hi encaixa canviant-les és un enllaç que cal corregir.

Un fitxer que no és versionat —ignorat, com `docs/privat/`— compta com a
inexistent: a GitHub no hi és, i l'enllaç hi quedaria trencat.

Surt amb codi 1 si algun enllaç no resol, o si no en troba cap: una eina que no
troba res segurament s'ha trencat, i callar seria un fals verd.
"""

from __future__ import annotations

import difflib
import html
import posixpath
import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import unquote

sys.path.insert(0, str(Path(__file__).resolve().parent))
from valida_xifres import fitxers_versionats  # noqa: E402  (el mateix «què hi haurà a GitHub»)

# La consola de Windows és cp1252 per defecte i peta amb «ó» o «→». El
# repositori s'edita des de Windows i s'executa a Linux: ha de funcionar als dos.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RE_CITA = re.compile(r"^(?:[ ]{0,3}>[ ]?)+")
RE_TANCA = re.compile(r"^\s*(`{3,}|~{3,})")
RE_TITOL = re.compile(r"^[ ]{0,3}(#{1,6})(?:[ \t]+(.*?))?(?:[ \t]+#+)?[ \t]*$")
RE_CODI = re.compile(r"(?<!`)(`+)(?!`)(.+?)(?<!`)\1(?!`)")
RE_IMATGE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
RE_ENLLAC_TEXT = re.compile(r"\[([^\]]*)\](?:\([^)]*\)|\[[^\]]*\])")
RE_AUTOENLLAC = re.compile(r"<((?:https?|mailto):[^>\s]+)>")
RE_ETIQUETA = re.compile(r"</?[A-Za-z][^>]*>")
RE_ESCAPADA = re.compile(r"\\([!-/:-@\[-`{-~])")
RE_ANCORA_HTML = re.compile(
    r"<a\s[^>]*?(?<![\w-])(?:id|name)\s*=\s*(?:\"([^\"]*)\"|'([^']*)')", re.IGNORECASE
)
RE_ENLLAC = re.compile(
    r"\]\(\s*(?:<([^>]*)>|([^)\s]*))(?:\s+(?:\"[^\"]*\"|'[^']*'|\([^)]*\)))?\s*\)"
)
RE_ESQUEMA = re.compile(r"^(?:[A-Za-z][A-Za-z0-9+.-]*:|//)")

# Una «_» literal que no s'ha de confondre amb la d'una cursiva.
GUIO_BAIX = "\0"


def sense_codi(text: str) -> str:
    """El text sense els trossos entre backticks (per buscar-hi enllaços)."""
    return RE_CODI.sub(" ", text)


def _cursiva(m: re.Match) -> str:
    """Una tira de «_» fora: la de cursiva, sí; la de dins d'una paraula, no.

    La de cursiva toca una paraula només per un costat («_així_»); la de
    `snake_case` escrit sense backticks, pels dos, i GitHub la deixa com és.
    """
    text, a, b = m.string, m.start(), m.end()
    dins = a > 0 and text[a - 1].isalnum() and b < len(text) and text[b].isalnum()
    return m[0] if dins else ""


def text_renderitzat(titol: str) -> str:
    """El text d'un títol tal com el mostra GitHub, que és d'on surt l'àncora."""
    # El codi es guarda a part i torna al final tal qual: dins dels backticks,
    # «_», «*», «&amp;» o «<a>» són text, no format.
    codis: list[str] = []

    def guarda(m: re.Match) -> str:
        codi = m[2]
        if len(codi) > 2 and codi[0] == codi[-1] == " " and codi.strip():
            codi = codi[1:-1]
        codis.append(codi)
        return f"\x01{len(codis) - 1}\x02"

    text = RE_CODI.sub(guarda, titol)
    text = RE_ESCAPADA.sub(lambda m: GUIO_BAIX if m[1] == "_" else m[1], text)
    text = RE_IMATGE.sub("", text)
    text = RE_ENLLAC_TEXT.sub(r"\1", text)
    text = RE_AUTOENLLAC.sub(r"\1", text)
    text = RE_ETIQUETA.sub("", text)
    text = text.replace("*", "").replace("~", "")
    text = re.sub(r"_+", _cursiva, text)
    text = html.unescape(text)
    text = re.sub(r"\x01(\d+)\x02", lambda m: codis[int(m[1])], text)
    return text.replace(GUIO_BAIX, "_").strip()


def slug(text: str) -> str:
    """El *slug* de GitHub: minúscules, fora el que no és \\p{Word}, «-» o espai."""
    net = "".join(
        c for c in text.lower()
        if c in "- " or unicodedata.category(c)[0] in "LM"
        or unicodedata.category(c) in ("Nd", "Pc")
    )
    return net.replace(" ", "-")


def linies_de_text(contingut: str):
    """Les línies que no són codi, sense el «>» de les cites: (número, text)."""
    tanca = None  # (caràcter, llargada, profunditat de cita)
    for n_linia, linia in enumerate(contingut.splitlines(), 1):
        cita = RE_CITA.match(linia)
        profunditat = cita.group(0).count(">") if cita else 0
        text = linia[cita.end():] if cita else linia
        if tanca and profunditat < tanca[2]:
            tanca = None  # la cita s'ha acabat, i el bloc de dins amb ella
        m = RE_TANCA.match(text)
        if tanca:
            if m and m[1][0] == tanca[0] and len(m[1]) >= tanca[1] \
                    and not text[m.end():].strip():
                tanca = None
            continue
        if m:
            tanca = (m[1][0], len(m[1]), profunditat)
            continue
        yield n_linia, text


def ancores(contingut: str) -> set[str]:
    """Totes les àncores d'un document: les dels títols i les `<a id/name>`."""
    trobades: set[str] = set()
    vegades: dict[str, int] = {}
    for _, text in linies_de_text(contingut):
        m = RE_TITOL.match(text)
        if m:
            base = slug(text_renderitzat(m[2] or ""))
            candidata = base
            while candidata in vegades:  # com github-slugger
                vegades[base] += 1
                candidata = f"{base}-{vegades[base]}"
            vegades[candidata] = 0
            trobades.add(candidata)
        for a in RE_ANCORA_HTML.finditer(sense_codi(text)):
            trobades.add(a[1] if a[1] is not None else a[2])
    return trobades


def enllacos(contingut: str):
    """Els enllaços relatius amb àncora: (número de línia, fitxer, àncora)."""
    for n_linia, text in linies_de_text(contingut):
        for m in RE_ENLLAC.finditer(sense_codi(text)):
            desti = m[1] if m[1] is not None else m[2]
            if "#" not in desti or RE_ESQUEMA.match(desti):
                continue
            cami, ancora = desti.split("#", 1)
            yield n_linia, unquote(cami), unquote(ancora)


def main(arrel: Path | None = None, verbos: bool = False) -> int:
    arrel = arrel or Path(__file__).resolve().parent.parent
    fitxers = set(fitxers_versionats(arrel))
    docs = sorted(
        f for f in fitxers
        if f.endswith(".md") and not f.startswith("docs/privat/")
        and (f in ("README.md", "CLAUDE.md") or f.startswith("docs/"))
    )

    cache: dict[str, set[str]] = {}

    def ancores_de(rel: str) -> set[str]:
        if rel not in cache:
            cache[rel] = ancores((arrel / rel).read_text(encoding="utf-8", errors="replace"))
        return cache[rel]

    comprovats = falles = 0
    for doc in docs:
        contingut = (arrel / doc).read_text(encoding="utf-8", errors="replace")
        for n_linia, cami, ancora in enllacos(contingut):
            comprovats += 1
            lloc = f"{doc}:{n_linia}"
            if not cami:
                desti = doc
            elif cami.startswith("/"):
                desti = posixpath.normpath(cami.lstrip("/"))
            else:
                desti = posixpath.normpath(posixpath.join(posixpath.dirname(doc), cami))

            if desti not in fitxers:
                falles += 1
                print(f"  FALLA  {lloc}  «{cami}» no existeix (o no és versionat)")
                continue
            if not ancora or not desti.endswith(".md"):
                if verbos:
                    print(f"  OK     {lloc}  {desti} (l'àncora no es comprova)")
                continue
            if ancora in ancores_de(desti):
                if verbos:
                    print(f"  OK     {lloc}  {desti}#{ancora}")
                continue
            falles += 1
            print(f"  FALLA  {lloc}  {desti} no té cap àncora «#{ancora}»")
            proposta = difflib.get_close_matches(ancora, ancores_de(desti), n=1, cutoff=0.6)
            if proposta:
                print(f"         potser volia dir «#{proposta[0]}»")

    print()
    if comprovats == 0:
        print("No he trobat cap enllaç amb àncora als documents. Segurament s'ha trencat "
              "l'eina o ha canviat el format: no ho dono per bo.")
        return 1
    if falles:
        print(f"{falles} enllaç(os) trencat(s) de {comprovats}, a {len(docs)} documents.")
        return 1
    print(f"{comprovats} enllaços amb àncora a {len(docs)} documents, tots resolen.")
    return 0


if __name__ == "__main__":
    sys.exit(main(verbos="-v" in sys.argv[1:]))
