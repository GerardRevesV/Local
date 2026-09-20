#!/usr/bin/env python3
"""Validació de sintaxi YAML entenent els tags propis de Home Assistant.

PyYAML no coneix `!include`, `!secret` i companyia, i peta en trobar-los. Això
els registra com a no-operacions per poder validar la sintaxi sense HA.

    python3 tools/valida_yaml.py

⚠️ Això NO substitueix `check_config` de Home Assistant: comprova la sintaxi,
no que les claus existeixin ni que les plantilles Jinja tinguin sentit. És la
primera barrera, barata i instantània; la segona la posa `desplega.sh`.

Surt amb codi 1 si algun fitxer no és vàlid.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

# La consola de Windows és cp1252 per defecte i peta amb «°» o «≈». El
# repositori s'edita des de Windows i s'executa a Linux: ha de funcionar als dos.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Tags que Home Assistant afegeix al carregador de YAML.
HA_TAGS = (
    "!include",
    "!include_dir_list",
    "!include_dir_named",
    "!include_dir_merge_list",
    "!include_dir_merge_named",
    "!secret",
    "!env_var",
    "!input",
)

FITXERS = ("config/**/*.yaml", "*.yml", "esphome/**/*.yaml")


class CarregadorHA(yaml.SafeLoader):
    """SafeLoader que tolera els tags de Home Assistant."""


def _ignora(loader: CarregadorHA, node: yaml.Node):  # noqa: ARG001
    """Resol qualsevol tag d'HA a un marcador, sense interpretar-lo."""
    if isinstance(node, yaml.ScalarNode):
        return f"<{node.tag}>"
    if isinstance(node, yaml.SequenceNode):
        return []
    return {}


for tag in HA_TAGS:
    CarregadorHA.add_constructor(tag, _ignora)


def valida(cami: Path) -> str | None:
    """Retorna None si el fitxer és vàlid, o el missatge d'error."""
    try:
        yaml.load(cami.read_text(encoding="utf-8"), Loader=CarregadorHA)
    except yaml.YAMLError as err:
        return str(err).replace("\n", "\n    ")
    except OSError as err:
        return f"no es pot llegir: {err}"
    return None


def main() -> int:
    arrel = Path(__file__).resolve().parent.parent
    camins: list[Path] = []
    for patro in FITXERS:
        camins.extend(sorted(arrel.glob(patro)))

    if not camins:
        print("No s'ha trobat cap fitxer YAML a validar.")
        return 1

    errors = 0
    for cami in camins:
        relatiu = cami.relative_to(arrel).as_posix()
        problema = valida(cami)
        if problema is None:
            print(f"  OK     {relatiu}")
        else:
            errors += 1
            print(f"  FALLA  {relatiu}\n    {problema}")

    print()
    if errors:
        print(f"{errors} fitxer(s) amb errors de sintaxi.")
        return 1
    print(f"{len(camins)} fitxers YAML, sintaxi correcta.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
