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

> ✅ **Resolt el 21/09/2026: és un P110M.** Els documents deien «P110» i alhora que la font
> era Matter, i això no podia ser. L'aparell **s'anuncia a la xarxa local com a dispositiu
> Matter** (`DN=Smart Wi-Fi Plug`, `DT=266`, fabricant TP-Link) i porta el microprogramari
> **1.4.3**, molt per damunt de l'1.3.0 que cal per al consum. Les dues condicions, doncs,
> estan complertes.
>
> Per a la propera vegada, la comprovació de cinc segons és aquesta: **si hi ha codi Matter
> imprès a l'aparell, és un model «M»**. I per veure què s'anuncia de debò a la xarxa:
> `ssh local-ha "timeout 8 avahi-browse -rpt _matterc._udp | grep '^='"`.

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

## 🔴 Quan l'emparellament falla: `PASE timeout`

A la interfície d'HA només hi surt **«Something went wrong»**, que no diu res. El que diu
alguna cosa és el registre del `matter-server`:

```bash
ssh local-ha "docker logs --tail 60 matter-server 2>&1 | grep -viE 'Packet too small'"
```

**Això és el que va sortir el 21/09/2026**, tres vegades seguides:

```
Starting Matter commissioning using Node ID 2 and IP fe80::…
Msg Retransmission to 0:0000000000000000 failure (max retries:4)
PASESession timed out while waiting for a response from the peer. Expected message type was 33
Secure Pairing Failed  ·  CHIP Error 0x00000003: Incorrect state
Error while handling: commission_on_network: Commissioning failed for node 2
```

**Com es llegeix:** el «missatge 33» és la **primera resposta** que ha de donar l'aparell quan
se li demana d'establir la sessió d'emparellament. No és que la contrasenya sigui dolenta —
això fallaria més tard i amb un altre error. És que **l'aparell no contesta**.

### Descartar la xarxa en tres ordres

Abans de tocar res, val la pena saber si el problema és de xarxa o de l'aparell:

```bash
# 1. L'endoll s'anuncia com a emparellable? (CM=2 → finestra oberta)
ssh local-ha "timeout 8 avahi-browse -rpt _matterc._udp | grep '^='"

# 2. Hi arribem per IPv4?
ssh local-ha "ping -c2 LA-IP-DE-L-ENDOLL"

# 3. I per IPv6 d'enllaç local, que és el que Matter fa servir de debò?
ssh local-ha "ping -6 -c3 'fe80::…%enp1s0'"
```

El 21/09/2026 les tres van sortir bé: l'endoll anunciava `CM=2` —finestra d'emparellament
**oberta**—, i responia tant per IPv4 com per IPv6 d'enllaç local en 4 ms. **La xarxa no era
el problema**, i això descarta d'una tacada l'IPv6, el mDNS, l'aïllament de clients del router
i el tallafoc.

### 🎯 La causa que hi encaixa: per quina interfície surt el servidor

L'adreça a la qual el servidor prova d'emparellar és una **`fe80::`**, i una adreça així **no
identifica una màquina: identifica una màquina *en un enllaç concret***. Per enviar-hi res,
cal dir també **per quina interfície** es surt.

I aquest amfitrió en té **quatre** amb adreça `fe80::`:

```
enp1s0       UP        192.168.1.102/24   fe80::4d20:daf2:d41e:5828/64   ← el cable, l'única bona
wlp0s20f3    DOWN      (Wi-Fi, apagada)
tailscale0   UNKNOWN   100.118.82.120/32  fe80::7a7b:7456:3078:32f6/64
docker0      DOWN      172.17.0.1/16      fe80::7019:aff:fe55:33cb/64
```

Si el servidor Matter tria la que no toca, els paquets **se'n van a un forat**: l'aparell no
els rep, no contesta mai, i surt exactament el `PASESession timed out` de dalt. Encaixa amb
tot el que s'ha vist —l'endoll respon a un `ping` per `fe80::…%enp1s0`, o sigui **quan la
interfície l'hi diem nosaltres**.

Per això el `matter-server` té una opció que es diu **exactament això**:

```
--primary-interface PRIMARY_INTERFACE   Primary network interface for link-local addresses
```

→ Posada al [`docker-compose.yml`](../../docker-compose.yml) el 21/09/2026, amb els dos
arguments del `CMD` per defecte de la imatge al davant, que `command:` els substitueix
sencers.

> **Per què el hub no va patir-ho:** el H110 s'anuncia amb la seva **adreça de la xarxa**
> (`192.168.1.100`), no amb una d'enllaç local. Quan l'adreça és normal, no hi ha cap
> interfície a triar i el problema no apareix. És el tipus d'error que només es veu amb
> l'aparell que el destapa.

### 🪟 Des del Windows o des de l'Android?

**Des del navegador, i prou**, mentre l'aparell **ja sigui a la Wi-Fi**: és el cas d'aquí, i
per això HA fa `commission_on_network`. L'app Companion d'Android **no és obligatòria**.

L'**Android** cal quan l'aparell **encara no és a cap xarxa** —acabat de treure de la caixa o
de fàbrica—, perquè llavors algú li ha de passar les credencials de la Wi-Fi per **Bluetooth**,
i això ho fa el mòbil.

> 🎯 **Però com a pla B val la pena.** Quan s'empara des de l'app d'Android, qui fa la
> conversa amb l'aparell és **el mòbil**, no el servidor: no depèn ni de la interfície ni de
> l'IPv6 d'enllaç local del portàtil. Si el camí del navegador segueix fallant, el del mòbil
> **és un camí diferent de debò**, no el mateix intent repetit.

### El que queda, i què s'hi fa

Si l'aparell hi és, s'anuncia i respon a un ping però **no contesta l'emparellament**, la causa
és de les tres de sota — i totes tres es curen amb la mateixa recepta.

| Causa | Per què dona un timeout |
|---|---|
| **El codi ja ha caducat** | El codi que dona l'app de Tapo **val ~15 minuts i un sol ús**. Quan venç, hi ha aparells que **segueixen anunciant `CM=2`** encara que la finestra ja estigui tancada: sembla que estigui a punt i no ho està |
| **Una sessió a mig fer** | Matter només admet **una** sessió d'emparellament alhora. Un intent que ha fallat pot deixar l'aparell ocupat, i el següent el troba «en estat incorrecte» |
| **Codi imprès en comptes del de l'app** | El de l'etiqueta és el de fàbrica. Un cop l'aparell és a l'app de Tapo, **el que val és el que genera l'app** en compartir-lo amb una altra plataforma |

**La recepta, i en aquest ordre:**

1. **Desendolla l'endoll 10 segons i torna'l a endollar.** Això tanca qualsevol sessió a mig
   fer. Espera que torni a la xarxa (mig minut).
2. **Genera un codi nou a l'app de Tapo** — l'opció d'afegir-lo a una altra plataforma— i
   **no el generis fins que HA estigui esperant-lo**.
3. **Enganxa'l a HA de seguida.** Del codi a l'intent, com menys minuts millor.
4. **Un intent cada cop.** Si falla, torna al pas 1: reintentar amb el mateix codi sobre un
   aparell ocupat només afegeix un node mort més al comptador.
5. Si tres rondes netes fallen, prova-ho des de l'**app Companion d'HA** amb el mòbil a la
   mateixa Wi-Fi: hi entra el **BLE del mòbil**, que és un camí diferent del de la xarxa.

> 📌 **Els intents fallits deixen rastre inofensiu:** cada un consumeix un número de node
> (2, 3, 4…). No cal netejar res; el node bo serà el següent número lliure.

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

## ✅ La xarxa ja és la definitiva

Aquesta secció deia *«espera't a tenir la SIM»*. **Ja no cal:** el **router de la SIM ja hi
és**, i el 21/09/2026 tot penja d'ell —el servidor per **cable** (`enp1s0`), i el hub, l'endoll
i el mòbil per Wi-Fi.

Això vol dir que **l'emparellament que es faci ara ja és el bo**: quan la màquina vagi al
local, el router hi va amb ella i l'SSID no canvia. La regla de dalt es compleix sola.

> ⚠️ **El que encara no és definitiu és la posició dels sensors**, que són a casa fent el
> calibratge creuat. Per això el que es gravi ara segueix sent **experimentació** i l'arxiva
> [`scripts/inicia-serie.sh`](../../scripts/inicia-serie.sh) el dia que comenci la sèrie de
> debò (frontera **B.0**). Emparellar no s'haurà de repetir; els 28 dies, sí que comencen
> després.

## Registre

Quan estigui fet, apuntar al **registre d'instal·lació** de
[home-assistant.md](home-assistant.md#registre-dinstal·lació): data, **model exacte**,
**versió de microprogramari**, i quines entitats han aparegut. I tornar a mirar la memòria del
`matter-server`, que fins ara s'ha mesurat amb la **xarxa Matter buida**.
