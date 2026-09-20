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
  domotica/
    objectius.md       Per què es fa i amb quins principis
    arquitectura.md    Decisions obertes: eines, llenguatges, accés remot
    acces-remot.md     Proposta d'accés des de fora del local
    monitoritzacio.md  Proposta de registre, retenció i visualització de dades
    home-assistant.md  Muntatge del servidor i registre d'instal·lació
    inventari.md       Aparells existents i candidats
  privat/              (IGNORAT per git — mai commitar)
    identificacio.md   Adreça, cadastre, registre, parts, preu, detall de l'ITE
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
