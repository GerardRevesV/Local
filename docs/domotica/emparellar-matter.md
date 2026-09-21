# Emparellar un aparell per Matter — procediment

> **Per a què serveix:** afegir un aparell a Home Assistant per **Matter** sense trencar res
> del que no té arreglada a posteriori. Escrit el **21/09/2026** arran de la pregunta *«com
> s'afegeix l'endoll P110M?»*, però el procediment és **el mateix** per al hub **H110** i per
> als dos **S110E** de la Fase C.
>
> El *per què* de Matter és a [decisio-stack.md](decisio-stack.md) i al
> [`docker-compose.yml`](../../docker-compose.yml). Això és el *com*.

## ⚠️ Abans de res: quin model és exactament

**Mira l'etiqueta de l'aparell, la de sota o la de la caixa.** La lletra final ho canvia tot:

| Model | Matter? | Com entra a HA | On som |
|---|---|---|---|
| **P110M** | ✅ **Sí, de fàbrica.** Porta el **codi Matter imprès** (QR + 11 xifres) | Directament al `matter-server`, **sense hub i sense núvol** | El que caldria |
| **P110** (sense `M`) | ❌ **No.** És un Tapo clàssic | Només per la integració `tplink`, **amb correu i contrasenya del compte Tapo** | El que diu avui [inventari.md](inventari.md) |

> 🔴 **[inventari.md](inventari.md) i [noms-entitats.md](noms-entitats.md) diuen «P110» i
> alhora donen la font com a **Matter**. Les dues coses no poden ser certes.** Si l'aparell
> és un **P110M**, el que està malament és el nom del model als documents i la resta del
> disseny s'aguanta. Si és un **P110** pelat, el que cau és la via: tornaria el compte de
> Tapo que Matter havia tret del mig.
>
> **Si hi ha codi Matter imprès a l'aparell, és un P110M.** Aquesta és la comprovació de
> cinc segons que decideix.

## Les dues regles que no tenen arreglada a posteriori

### 1. S'empara **al Wi-Fi definitiu**, no a un de provisional

L'emparellament Matter **grava les credencials de la xarxa dins de l'aparell**. Canviar de
SSID no és reconfigurar: és **tornar a emparellar**, i un aparell reemparellat entra a HA com
a **node nou**, amb identificadors nous i **entitats noves**. L'històric anterior queda orfe.

És la mateixa regla que ja hi ha escrita per al hub al
[runbook](runbook-servidor.md#6-home-assistant), i val igual per a l'endoll.

### 2. El **microprogramari va abans** de l'emparellament

L'endoll només publica el consum per Matter a partir de la **versió 1.3.0** del seu
microprogramari, que és la que hi va portar **Matter 1.3**
([nota de TP-Link](https://community.tp-link.com/us/smart-home/threads/topic/835084)).
Abans d'això, per Matter només hi ha l'interruptor: encén i apaga, i prou.

I actualitzar **després** d'emparellar surt car: hi ha usuaris que han hagut de
**treure'l d'HA, actualitzar-lo des de l'app i tornar-lo a emparellar**
([fil de la comunitat d'HA](https://community.home-assistant.io/t/tapo-p110m-energy-monitoring/736975)).
En aquest projecte, això és partir la sèrie per una actualització.

> 🎯 **Conseqüència pràctica:** l'aparell passa per l'**app de Tapo primer** —per posar-lo a
> la xarxa i deixar-hi el microprogramari final— i **només després** entra a Home Assistant.

## El que ha d'estar llest abans de començar

- [ ] **`matter-server` viu.** `bash scripts/comprova.sh` al servidor, tot verd.
- [ ] **L'app Companion d'HA al mòbil**, connectada a aquesta instància, amb **Bluetooth** i
      permís d'ubicació (a Android, el BLE el demana).
- [ ] **L'aparell, el mòbil i el servidor, a la mateixa xarxa.** L'endoll és de **2,4 GHz**.
- [ ] **IPv6 i mDNS circulant per la xarxa local**, sense aïllament de clients al Wi-Fi.
      Matter va per IPv6 i multidifusió: si el router els talla, no es descobreix res.
- [ ] **Reserva DHCP** per a l'endoll al router (tasca A.2 de [fases.md](fases.md)).

> 🪤 **El Bluetooth el posa el mòbil, no el servidor.** L'emparellament el fa l'**app
> Companion**: és ella qui llegeix el QR i passa les credencials del Wi-Fi a l'aparell per
> BLE. Per això el `matter-server` **segueix sense `/run/dbus`** i el Bluetooth del portàtil
> **segueix apagat** —tal com diuen el [`docker-compose.yml`](../../docker-compose.yml) i el
> [runbook](runbook-servidor.md#-el-bluetooth-omple-el-log)—, i no s'han de tocar.

## El procediment, en ordre

| # | Pas | Detall |
|---|---|---|
| 1 | **Llegir l'etiqueta** | `P110M` o `P110`. Si no hi ha codi Matter imprès, para i vegeu la taula de dalt |
| 2 | **App de Tapo → afegir l'endoll** al Wi-Fi **definitiu** | El de la SIM, no el de casa, si es pot esperar (vegeu *Ara o quan hi hagi la SIM?*) |
| 3 | **App de Tapo → Configuració del dispositiu → Actualització de microprogramari** | Fins a **≥ 1.3.0**. **Apunta la versió que hi queda**: és una dada del registre |
| 4 | **Obtenir el codi Matter** | El de l'etiqueta de l'aparell. Si ja és a l'app de Tapo, l'app en genera un de **temporal** des de l'opció d'afegir-lo a una altra plataforma |
| 5 | **App Companion d'HA → Configuració → Dispositius i serveis → Afegeix → Matter** | Escaneja el QR o escriu les 11 xifres. Triga un parell de minuts |
| 6 | 🔴 **Renombrar les entitats ABANS que gravin res** | Vegeu la secció de sota. És la casella A.8, i no es pot desfer bé |
| 7 | **Reiniciar Home Assistant** | El `utility_meter` de [`rosada.yaml`](../../config/packages/rosada.yaml) s'enganxa a `sensor.deshumidificador_energia` **en arrencar**: si l'entitat no existia o s'acaba de renombrar, no s'hi enganxa fins al reinici |
| 8 | **Comprovar** | `bash scripts/comprova.sh`, i la llista de verificació de sota |

## Pas 6 — els noms, que és el pas que no es repeteix

El conveni és a [noms-entitats.md](noms-entitats.md) i per a aquest aparell diu:

| Què | `entity_id` |
|---|---|
| L'interruptor | `switch.deshumidificador` |
| Potència instantània | `sensor.deshumidificador_potencia` |
| Energia acumulada | `sensor.deshumidificador_energia` |

Matter els batejarà sol amb alguna cosa de l'estil `switch.tapo_p110m` i
`sensor.tapo_p110m_power`. **Es canvia l'ID d'entitat, no només el nom visible:**
Configuració → Dispositius i serveis → **Entitats** → l'entitat → **ID d'entitat**.

**Aquests tres noms no són decoratius:** `rosada.yaml` ja els té escrits a dins —els dos
`utility_meter` (diari i mensual) pengen de `sensor.deshumidificador_energia`, i el
`history_stats` de les hores diàries penja de `switch.deshumidificador`. Amb qualsevol altre
nom, aquests blocs queden mirant el buit **sense donar cap error**.

### Les entitats que sobren

Per Matter, un endoll amb mesura sol publicar també **tensió** i **corrent**. No fan falta per
a res del projecte i, gravades cada pocs segons durant dos anys, només són pes a la base de
dades.

→ **Decisió pendent** (vegeu [pendents.md](../pendents.md)): o bé entren a la llista
`exclude.entities` del [`recorder`](../../config/configuration.yaml) —que avui és buida a
posta, esperant justament aquest moment—, o bé s'accepten i s'obliden. El que **no** es pot
fer és excloure-les amb un glob: la norma del fitxer és **llista explícita, mai
`entity_globs`**.

## Què ha d'haver aparegut

Amb el microprogramari ≥ 1.3.0, a *Eines per a desenvolupadors → Estats*:

- [ ] `switch.deshumidificador` — encén i apaga (**amb l'endoll sense res endollat**, encara).
- [ ] `sensor.deshumidificador_potencia` en **W**.
- [ ] `sensor.deshumidificador_energia` en **kWh**, amb `state_class: total_increasing`.
      Sense aquest atribut no hi ha estadístiques de llarg termini i el `utility_meter` no
      compta.
- [ ] Els dos comptadors del `utility_meter` —energia diària i mensual— ja no diuen
      `unavailable`.

**Si l'entitat d'energia no hi és:** a la integració Matter, al dispositiu, hi ha l'opció de
**tornar a entrevistar-lo** (*re-interview*) — és el que li fa tornar a declarar què sap fer,
i és el primer que s'ha de provar després d'una actualització. Si després d'això segueix sense
aparèixer, el microprogramari encara no és ≥ 1.3.0.

## 🪤 Els paranys

### L'energia acumulada i el rellotge

Al fil de la comunitat s'hi reporta que **tensió, corrent i potència** van sense Internet,
però que l'**energia acumulada** depèn que l'aparell pugui sincronitzar l'hora **pel núvol**,
i que sense Internet queda `unavailable`.

**Encara no ho hem verificat, i importa:** els kWh/dia del deshumidificador són una de les
caselles de la [Porta B](fases.md#-porta-b). Al local hi haurà Internet per la SIM, o sigui
que en règim normal no hauria de sortir; el que caldrà saber és **què passa amb els kWh quan
la SIM caigui una estona** — si es perden les hores o si es recuperen en tornar.

→ Es comprova a casa, en fred: treu-li la sortida a Internet a l'endoll una hora i mira les
dues entitats.

### Actualitzar el microprogramari des d'HA

Es reporta que **falla** i que la via bona és l'app de Tapo. És un motiu més per deixar el
microprogramari fet **abans** d'emparellar, i per no tocar-lo mentre corri la sèrie.

### Treure'l de l'app de Tapo, o deixar-l'hi

Matter admet **diversos administradors**: pot estar alhora a l'app de Tapo i a Home Assistant.

- **Deixar-l'hi** vol dir conservar un fil cap al núvol de TP-Link... i conservar **l'única
  via que actualitza el microprogramari** sense haver de reemparellar-lo tot.
- **Treure'l** és més net, i és el que fa molta gent, però el dia que calgui una actualització
  s'ha de tornar a afegir a l'app de Tapo → i això és **reemparellar**, que és **partir la
  sèrie**.

> 🎯 **Recomanació:** **deixar-l'hi**. El projecte ja no rebutja el núvol per principi —la
> decisió de Matter era per *no dependre'n per funcionar*, i això es manté: qui decideix i
> qui grava és HA, en local. Un camí d'actualització que no obliga a reemparellar val més
> que la puresa.

### Entitats duplicades després d'una actualització

Amb la 1.4.1 hi ha qui s'ha trobat **sensors d'energia duplicats**. Si passa enmig de la
sèrie, **no s'esborra res a la lleugera**: s'anota la data a [pendents.md](../pendents.md) i
es decideix, que un forat explicat val molt més que un forat net.

## Ara, o quan hi hagi la SIM?

Avui l'aparell aniria al Wi-Fi de **casa**, perquè la SIM encara no està contractada (tasca
0.7). Emparellar-lo ara vol dir **tornar-lo a emparellar** al local: node nou, entitats noves,
i els noms del pas 6 aplicats **dues vegades**.

**Tot i així val la pena fer-ho ara, i a posta**, per dues coses que no es poden esperar:

1. **Saber si l'energia per Matter surt de debò.** Si no surt —model equivocat,
   microprogramari vell, o la dependència del núvol—, canvia la manera de mesurar els kWh del
   deshumidificador, i **això s'ha de saber abans** que arrenqui la sèrie, no al desembre.
2. **La prova 0.2b**, la del llindar de l'higròstat, que és bloquejant i encara està oberta.

És exactament per a això que hi ha la frontera **B.0**
([`scripts/inicia-serie.sh`](../../scripts/inicia-serie.sh)): el que es gravi ara és
**experimentació**, s'arxiva, i la sèrie de debò comença de zero amb els aparells ja a lloc.

> ⚠️ **El que sí que s'ha de fer bé ara mateix és el microprogramari**, perquè aquell no
> depèn de la xarxa i és el que estalvia un reemparellament futur.

## Registre

Quan estigui fet, apuntar al **registre d'instal·lació** de
[home-assistant.md](home-assistant.md#registre-dinstal·lació): data, **model exacte**,
**versió de microprogramari**, i quines entitats han aparegut. I tornar a mirar la memòria del
`matter-server`, que fins ara s'ha mesurat amb la **xarxa Matter buida**.
