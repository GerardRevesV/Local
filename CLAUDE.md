# Instruccions del repositori

## Què és això

Repositori d'un **local comercial en planta baixa amb soterrani**, a Barcelona:
documentació de la finca i, més endavant, el codi per controlar-ne els aparells domòtics.

⚠️ **El repositori és públic i està anonimitzat.** Llegeix la secció *Dades personals*
abans d'escriure res: hi ha una llista tancada del que no hi pot entrar.

## Idioma

Tota la documentació va en **català**. Les citacions literals de documents legals es
mantenen en l'idioma original (castellà), marcades com a citació.

## Regla principal: la documentació s'actualitza sobre la marxa

Cada cop que l'usuari aporti informació nova sobre el local o la domòtica —una foto, una
factura, un document, una dada d'una visita, una decisió tècnica—:

1. **Incorporar-la al document que toca** dins de `docs/`, no deixar-la només a la conversa.
2. **Actualitzar [`docs/pendents.md`](docs/pendents.md)**: marcar el que s'ha resolt, afegir
   el que s'hagi obert.
3. **Actualitzar l'estat al [`README.md`](README.md)** si canvia la fase del projecte.
4. Si és una fita del muntatge de Home Assistant, afegir una línia al registre
   d'instal·lació de [`docs/domotica/home-assistant.md`](docs/domotica/home-assistant.md).

No cal preguntar abans de documentar. Sí que cal preguntar abans de donar per bona una dada
que contradigui el que ja hi ha escrit.

**Jerarquia:** `decisio-stack.md` mana sobre les propostes de `docs/domotica/`. Les propostes
porten una capçalera que diu què en queda superat; es conserven pel raonament. Si una decisió
nova supera `decisio-stack.md`, s'edita allà i s'hi deixa constància.

## Flux de treball amb git

**Res va directament a `main`.** Tot canvi passa per una branca i un *pull request*, encara
que el repositori sigui d'una sola persona.

```bash
git switch -c nom-de-la-branca
# … canvis …
git add -A && git commit
git push -u origin nom-de-la-branca
gh pr create --base main
```

**Per què, en un repositori d'un sol autor:**

- El PR és **l'únic moment en què es veu tot el canvi junt** abans de publicar-lo. En un
  repositori públic amb dades d'una finca real, aquesta última mirada és la barana de
  privacitat: és quan es repassa que no hi hagi adreça, noms, cadastre ni imports.
- Deixa **constància escrita del perquè** de cada canvi, separada del *què* dels commits.
  D'aquí a un any, davant d'un pèrit o davant d'un mateix, això val molt.
- `main` queda sempre desplegable, que és el que el servidor del local fa `git pull`.

**Excepció única:** una correcció urgent amb el servidor caigut. Es fa, i es documenta després.

**Abans d'obrir el PR**, repassar el `git diff` sencer buscant adreça, noms propis, referència
cadastral, números de sèrie i imports. Vegeu *Dades personals*.

## Estructura

```
docs/
  pendents.md          Llista única de coses obertes
  fonts.md             D'on surt cada dada i què s'ha deixat fora
  local/
    fitxa-tecnica.md   Identificació genèrica, superfícies aproximades, règim
    compravenda.md     Parts (per rol), clàusules, despeses, cronologia
    humitats.md        El tema obert: retenció de 3.000 €, ITE, pla
    comunitat.md       Junta (per càrrec), derrames, acords
    installacions.md   Ventilació, splits, subministraments
    subministraments.md  Llum, aigua i la SIM de dades: contractes i estat
  domotica/
    decisio-stack.md   ⭐ LA DECISIÓ. Mana sobre qualsevol proposta anterior
    fases.md           ⭐ Fases, portes de test i repartiment de feina
    objectius.md       Per què es fa i amb quins principis
    arquitectura.md    Índex d'estat de les decisions
    acces-remot.md     Proposta d'accés des de fora del local
    monitoritzacio.md  Proposta de registre, retenció i visualització de dades
    control-punt-rosada.md  Proposta de lògica de control, helpers i maquinari
    desplegament.md    Flux casa → GitHub → local, i com es desplega
    publicacio-dades.md Com pugen les dades i on s'arxiven
    home-assistant.md  Muntatge del servidor i registre d'instal·lació
    runbook-servidor.md  Refer el servidor de zero: ordres, versions i paranys
    inventari.md       Aparells existents i candidats
    noms-entitats.md   Conveni de noms d'entitat — es fixa ABANS d'emparellar
  privat/              (IGNORAT per git — mai commitar)
    identificacio.md   Adreça, cadastre, registre, parts, preu, detall de l'ITE

config/                Configuració de Home Assistant (es desplega al local)
  configuration.yaml   `recorder`: purge_keep_days, commit_interval, exclusions
  packages/rosada.yaml La lògica del punt de rosada — UN sol punt d'avaluació
docker-compose.yml     Els DOS contenidors: HA (versió fixada) i matter-server
                       (digest fixat). Matter, perquè «tplink» rebutja el hub
scripts/               Guions per al host del local (bash)
  prepara-host.sh      Deixa el portàtil llest: SSH, NTP, cap suspensió, Docker
  comprova.sh          Verifica d'una passada que tot segueix com ha de ser
  inicia-serie.sh      Tanca l'experimentació i comença la sèrie probatòria
tools/                 Eines que corren a casa, no al local (Python stdlib)
  replica.py           Rèplica offline de la lògica + test de deriva
  valida_yaml.py       Valida el YAML abans de desplegar
```

## Dades personals — regla dura

Aquest repositori és **públic a GitHub**. **Mai** abocar-hi cap d'aquestes dades:

- **Adreça postal**, barri, districte, noms de carrer i llindes literals de l'escriptura.
- **Referència cadastral**, finca registral, CRU, registre de la propietat, localització
  cadastral.
- **Número de protocol notarial** i referències de còpia simple o de documents associats.
- **Noms propis**: de la propietat, de notaris, de societats venedores, d'agències. Si cal
  esmentar algú, fer-ho pel **càrrec** («el president», «l'agència»), mai pel nom ni pel pis.
- **DNI/NIF, números de compte bancari**, entitats bancàries, adreces particulars de tercers.
- **Preu exacte** de compra, imports de pagaments i dades bancàries de l'operació.
- **Superfícies, coeficient i valor cadastral exactes** — al repositori hi van arrodonits.
- **Deficiències de l'ITE atribuïdes a habitatges concrets** de la finca (afecten tercers).
- **Rutes de fitxers del disc personal** i noms de fitxers originals que continguin l'adreça.

### On van, doncs

Tot això viu a **`docs/privat/identificacio.md`**, que està al `.gitignore` i **no es commita
mai**. Quan arribi una dada d'aquestes:

1. Guardar-la al fitxer privat.
2. Al document públic de `docs/`, escriure'n només la part **anonimitzada o arrodonida** que
   calgui per raonar, i apuntar al fitxer privat per al valor exacte.

### Abans de commitar

Revisar el `git diff` buscant adreça, noms propis, referència cadastral i imports. Si
s'afegeixen **fotos**, comprovar que no portin **geolocalització a les metadades** ni rètols,
plaques o documents amb l'adreça visible.

## Precisió

La documentació legal es cita **amb fidelitat**. Si una clàusula té matisos, s'escriuen els
matisos. Si una dada no la tenim, es diu *pendent* — no s'omple amb una suposició.
