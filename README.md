# Local — documentació i domòtica

Repositori central d'un **local comercial en planta baixa amb soterrani**, a Barcelona: la
documentació de la finca i, més endavant, el codi per controlar-ne els aparells domòtics.

> 🔒 **Repositori públic i anonimitzat.** No hi consten l'adreça, les dades cadastrals i
> registrals, els noms de les parts ni els imports de l'operació. Vegeu
> [Privacitat](#privacitat).

## Què hi ha aquí

| Carpeta | Contingut |
|---|---|
| [`docs/local/`](docs/local/) | Fitxa tècnica, compravenda, humitats, comunitat, instal·lacions i subministraments |
| [`docs/domotica/`](docs/domotica/) | Objectius, arquitectura, accés remot, inventari, muntatge de Home Assistant, el [runbook del servidor](docs/domotica/runbook-servidor.md), el [conveni de noms d'entitat](docs/domotica/noms-entitats.md) i com [s'empara un aparell per Matter](docs/domotica/emparellar-matter.md) |
| [`docs/pendents.md`](docs/pendents.md) | Llista única de coses obertes |
| [`docs/fonts.md`](docs/fonts.md) | D'on surt cada dada i què s'ha deixat fora deliberadament |
| [`config/`](config/) | La configuració de Home Assistant que es desplega al local, amb la lògica del punt de rosada a [`packages/rosada.yaml`](config/packages/rosada.yaml) |
| [`scripts/`](scripts/) | Guions per al host del local: preparar-lo, comprovar-lo, [avisar si cau](scripts/bategada.sh) i [tancar l'experimentació](scripts/inicia-serie.sh) quan comença la sèrie que val com a prova |
| [`tools/`](tools/) | Eines que corren a casa: rèplica offline de la lògica i validació del YAML |

## Estat actual (21 de setembre de 2026)

- **Local:** comprat. Escriptura signada el 9 de setembre de 2026. Possessió lliurada.
- **Tema obert:** humitats al soterrani. Hi ha una **retenció de 3.000 € amb data límit
  ~9 de març de 2027** per determinar-ne l'origen. Vegeu [humitats.md](docs/local/humitats.md).
- **Domòtica:** **el servidor ja corre.** Home Assistant 2026.9.3 en un portàtil amb Linux
  Mint, amb la versió fixada, accés per **Tailscale** i `purge_keep_days: 730` des del primer
  dia. Ara mateix s'està fent l'**assaig general a casa** —amb el mateix router SIM que hi
  haurà al local— abans de portar-ho tot allà.
  → [home-assistant.md](docs/domotica/home-assistant.md) · [runbook-servidor.md](docs/domotica/runbook-servidor.md)
  L'objectiu és **governar els ventiladors cap a l'exterior pel punt de rosada per estalviar
  deshumidificador, i monitoritzar-ho tot**. ⚠️ **Des del 21/09/2026 és l'objectiu principal**:
  documentar les humitats per a la retenció queda **ajornat, amb la porta oberta**, i per això
  queden superats el repositori privat d'arxiu, el segell de temps i la congelació de
  versions. L'arquitectura és: Home Assistant sobre SQLite, lògica en YAML natiu, còpia
  nocturna en Python al disc USB del local, i Tailscale com a única via d'accés. De panell,
  primer els taulers natius d'HA. ⚠️ **Des del 21/09/2026
  l'stack són dos contenidors i no un:** el hub Tapo xifra amb TPAP i la integració `tplink`
  el rebutja, així que la via és **Matter**, que demana el seu propi servidor.
  → [decisio-stack.md](docs/domotica/decisio-stack.md) · [fases.md](docs/domotica/fases.md)

## Privacitat

Aquest repositori documenta una operació immobiliària real, i **és públic**. Per això la
documentació està escrita de manera **impersonal i no identificable**:

- Res d'**adreça**, barri, llindes literals, **referència cadastral**, finca registral, CRU
  ni **número de protocol** notarial.
- Res de **noms** — ni de la propietat, ni de notaris, ni de societats o agències. Les
  persones s'esmenten pel **càrrec**, mai pel nom.
- Res de **DNI/NIF, comptes bancaris** ni adreces particulars de tercers.
- Res del **preu exacte** ni del calendari de pagaments.
- Res de **deficiències de l'ITE atribuïdes a habitatges concrets** de la finca.

Totes aquestes dades viuen en un únic fitxer local, `docs/privat/identificacio.md`, que està
al [`.gitignore`](.gitignore) i **no s'ha de commitar mai**. Els documents originals (PDF,
DOCX) tampoc: el `.gitignore` els exclou per extensió.

**Abans d'afegir res de nou al repositori, rellegiu aquesta llista.**
