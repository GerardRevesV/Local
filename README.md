# Local — documentació i domòtica

Repositori central d'un **local comercial en planta baixa amb soterrani**, a Barcelona: la
documentació de la finca i, més endavant, el codi per controlar-ne els aparells domòtics.

> 🔒 **Repositori públic i anonimitzat.** No hi consten l'adreça, les dades cadastrals i
> registrals, els noms de les parts ni els imports de l'operació. Vegeu
> [Privacitat](#privacitat).

## Què hi ha aquí

| Carpeta | Contingut |
|---|---|
| [`docs/local/`](docs/local/) | Fitxa tècnica, compravenda, humitats, comunitat i instal·lacions |
| [`docs/domotica/`](docs/domotica/) | Objectius, arquitectura, accés remot, muntatge de Home Assistant i inventari |
| [`docs/fonts.md`](docs/fonts.md) | D'on surt cada dada i què s'ha deixat fora deliberadament |

## Estat actual (20 de setembre de 2026)

- **Local:** comprat. Escriptura signada el 9 de setembre de 2026. Possessió lliurada.
- **Tema obert:** humitats al soterrani. Hi ha una **retenció de 3.000 € amb data límit
  ~9 de març de 2027** per determinar-ne l'origen. Vegeu [humitats.md](docs/local/humitats.md).
- **Domòtica:** fase zero. S'està instal·lant **Home Assistant en un portàtil secundari**
  (ara mateix, preparant un pen drive amb Linux Mint). El maquinari del servidor ja està
  identificat i **és suficient** per a l'stack decidit.
  → [home-assistant.md](docs/domotica/home-assistant.md#el-maquinari-del-servidor)
  L'objectiu és **governar els ventiladors cap a l'exterior pel punt de rosada per estalviar
  deshumidificador, i monitoritzar-ho tot**. L'arquitectura ja **està decidida**: un sol
  contenidor de Home Assistant sobre SQLite, lògica en YAML natiu, exportació nocturna en
  Python a un repositori privat, i Tailscale com a única via d'accés. Sense panell web propi.
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
