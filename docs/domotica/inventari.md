# Inventari d'aparells

> Actualitzat el **20/09/2026** amb el maquinari que ja està comprat. Això **substitueix** la
> proposta de maquinari de [control-punt-rosada.md](control-punt-rosada.md) i corregeix la
> decisió de ràdio de [decisio-stack.md](decisio-stack.md).

## ✅ Ja comprat i funcionant

### Ecosistema TP-Link Tapo

| Aparell | Model | Ubicació | Estat |
|---|---|---|---|
| Hub | **Tapo H110** ✅ *(hub IR + sub-GHz)* | corridor | Actiu |
| Endoll intel·ligent | **Tapo P110** ✅ *(mesura consum)* | corridor | Actiu — deshumidificador |
| **Mòduls de relé** | **2× Tapo S110E** | — | ⏳ **Comprats, sense instal·lar** |
| Sensor T/HR | **Tapo T315** | Soterrani — *Centre* | Actiu |
| Sensor T/HR | **Tapo T315** | Soterrani — *Fons* | Actiu |
| Sensor T/HR | **Tapo T310** | Soterrani — *Gran* | Actiu |
| Sensor T/HR | **Tapo T315** | **Planta baixa** — *Dalt* | Actiu |
| Sensor T/HR | **Tapo T310** | **Exterior** — *Fora* (protegit ✅) | Actiu |
| Sensor d'inundació | **Tapo T300** (?) | Soterrani — Centre | Actiu |
| Càmeres | Tapo | — | N'hi ha |

### Distribució dels sensors

```
        EXTERIOR                    PLANTA BAIXA              SOTERRANI
      ┌───────────┐               ┌───────────┐         ┌─────────────────┐
      │   Fora    │               │   Dalt    │         │   Gran   (dalt  │
      │   T310    │               │   T315    │         │   T310    delmapa)
      │ protegit  │               │           │         ├─────────────────┤
      └───────────┘               └───────────┘         │  Centre  (mig)  │
       Td exterior                 Td de referència     │  T315           │
       ← la meitat                 de la planta baixa   ├─────────────────┤
         del criteri                                    │  Fons    (avall,│
                                                        │  T315    dona al│
                                                        │          passadís)
                                                        └─────────────────┘
                                                         Td interior
                                                         ← l'altra meitat
```

**Per què aquesta distribució va bé:** tres punts al soterrani permeten veure si la humitat és
uniforme o **localitzada**. Si *Fons* va sistemàticament més humit que *Gran*, això ja apunta
a una causa local —una paret, una mitgera, el terreny— i no a condensació general per manca de
ventilació. És informació de diagnòstic que un sol sensor no donaria.

El de *Dalt* serveix de control: si la planta baixa i el soterrani es mouen junts, l'origen és
ambiental; si el soterrani va pel seu compte, l'origen és del soterrani.

**Lectura de referència (20/09/2026, 16:25):** Centre 22,4 °C / 66 % · Dalt 23,5 °C / 61 % ·
Fons 23,5 °C / 62 % · Fora 23,9 °C / 68 % · Gran 22,7 °C / 64 %.

> Amb aquestes lectures, el punt de rosada interior de referència és **15,80 °C** (el punt
> *Fons*, el més humit dels tres) i l'exterior **17,64 °C** — ΔTd = **−1,83 °C**: ara mateix **ventilar afegiria aigua**. És exactament el cas que l'automatisme
> ha d'evitar, i es veu ja al primer cop d'ull.

### Servidor de Home Assistant

**Acer TravelMate B3 — TMB311-32-C4JR** (plataforma N20Q14, fabricat el 29/06/2022).

| Característica | Valor |
|---|---|
| Ràdio | **Intel AX201NGW** — Wi-Fi 6 + Bluetooth 5 |
| Xarxa per cable | **RJ-45 gigabit** *(a confirmar visualment)* |
| Alimentació | 45 W: 19 V ⎓ 2,37 A **o USB-C PD** 20 V ⎓ 2,25 A |
| Consum en servei | ~8–12 W → **< 1 €/mes** |
| Bateria | **42,5 Wh reals** de 53 de disseny (80 % de salut) → **~4 h** de marge |
| Refrigeració | **Sense ventilador** |
| CPU | **Intel Celeron N5100** — 4 nuclis ✅ |
| RAM | **4 GB** soldats (3,6 útils) ✅ |
| Disc | **SSD NVMe Samsung 128 GB** ✅ — no és eMMC |
| Sistema | Linux Mint 22.3 |

**Veredicte: suficient per a l'stack decidit**, perquè l'stack és petit i va sobre SQLite.
✅ **Mesurat el 21/09/2026** amb els **dos** contenidors en marxa: HA 436 MB i `matter-server`
**88 MB** — el 19 % dels 3.716 MB. El segon contenidor de Matter **no compromet la memòria**;
qui se la menja és l'escriptori gràfic i un Firefox obert (~1,9 GB entre tots dos). Les
especificacions completes, el veredicte raonat i les xifres són a
[home-assistant.md](home-assistant.md#-la-ram-mesurada--i-la-sorpresa-no-és-matter).

> ⚠️ **Va a la planta baixa, no al soterrani.** I és l'únic aparell de la cadena amb bateria:
> en un tall de corrent el hub H110 i el router cauen igualment.

### Deshumidificador

**QLIMA D 825 PA SMART** (ref. Leroy Merlin 91164803, EAN 8713508793047)

| Característica | Valor |
|---|---|
| Capacitat | **25 L/24 h** |
| **Consum elèctric** | **470 W** (2,2 A) |
| Cabal d'aire | 200 m³/h |
| Per a estances de | 140–165 m³ *(el soterrani ≈ 115 m³ — hi cap de sobres)* |
| Dipòsit | 3,8 L |
| **Bomba de condensats incorporada** | ✅ Sí — la «PA» del nom |
| **Desguàs continu** | ✅ Sí, amb el tub inclòs |
| **Reinici automàtic després d'un tall** | ✅ **SÍ** |
| Higròstat ajustable | ✅ 40–80 % HR |
| Temporitzador | Màx. 9 h |
| Velocitats de ventilador | 3 |
| Control | Electrònic + **WiFi (app Smart Life / Tuya)** |
| Refrigerant | **R290** (propà), 70 g, GWP 3 |
| Filtres | Malla + HEPA |
| Soroll | < 47 dB(A) a 1 m |
| Dimensions / pes | 355 × 255 × 572 mm · 17 kg |
| Protecció | IPX4 |
| Garantia | 3 anys |

---

## 🎉 Tres coses que això desbloqueja

### 1. El reinici automàtic està confirmat

Era **la verificació bloquejant** de tot el disseny: si el deshumidificador no es reprengués
sol després d'un tall, el control per endoll intel·ligent no serviria de res. La fitxa de
producte ho diu explícitament: **«Reinicio automático: Sí»**.

→ L'arquitectura **(a)** de [control-punt-rosada.md](control-punt-rosada.md) queda confirmada:
l'higròstat propi de la màquina regula, i Home Assistant només fa l'**enclavament** amb els
ventiladors i les **franges horàries**.

### 2. La preocupació del Zigbee al soterrani desapareix

Els sensors Tapo **no fan servir Zigbee ni Wi-Fi**: parlen amb el hub per **ràdio sub-GHz de
868 MHz**. A 868 MHz la penetració a través de formigó armat és **notablement millor** que a
2,4 GHz — és el mateix argument que feia recomanable Z-Wave, però sense pagar-lo.

→ **Fora: SLZB-06, ZHA, coordinador Zigbee, prova de cobertura de 48 h.** ~45 € i una decisió
irreversible menys.

### 3. La bomba resol el dipòsit

A 25 L/dia, un dipòsit de 3,8 L **s'omple en menys de 4 hores**. Sense desguàs continu
l'aparell s'aturaria sol tres vegades al dia i l'automatisme no se n'assabentaria.

→ Amb la **bomba incorporada** el condensat es pot enviar cap amunt fins a un desguàs, sense
dependre de la gravetat. **El desguàs continu no és opcional: és obligatori.**

---

## Del manual oficial (`UM_Dehumidifier_D_825_PA_SMART`)

Baixat de `assets.pvg.eu`. Això resol gairebé totes les preguntes obertes.

| Qüestió | Resposta del manual |
|---|---|
| **Rang de funcionament** | **Mínim 5 °C / 35 % HR · Màxim 35 °C / 90 % HR** |
| **Descongelació automàtica** | ✅ Sí. En ambients freds es glaça i entra sol en mode desgebratge, amb l'indicador **P1** |
| **Protecció del compressor** | ✅ **5 minuts** entre aturada i nova arrencada, **implementada a l'aparell** |
| **Altura màxima de bombeig** | **4 metres** |
| **Dipòsit ple** | Indicador + **10 xiulets** + aturada automàtica (codi **P2**). En buidar-lo, el compressor torna al cap de 5 min |
| **Manteniment** | Missatge a la pantalla a les **360 hores** de funcionament |
| **Indicador lluminós d'HR** | Vermell ≥ 80 % · Groc 56–78 % · Blau ≤ 54 % |
| **Codis d'error** | **C1/C2/C8** = termistor o sensor obert/curtcircuitat, o **fuita de refrigerant** → servei tècnic. **P1** = desgebrant. **P2** = dipòsit ple |
| Altres funcions | Bloqueig per a nens, assecat interior, temporitzador 0–9 h |

### 🎉 La protecció del compressor ja és a l'aparell

El manual ho diu: **«el compresor dispone de un periodo de cinco minutos entre el inicio del
funcionamiento y el apagado»**. És una segona capa de seguretat per sota de la nostra.

> ⚠️ **Però no ens estalvia la nostra.** Aquesta protecció viu al microcontrolador de
> l'aparell i necessita que **l'aparell tingui corrent** per comptar. Si Home Assistant li
> talla l'alimentació, el comptador probablement es perd. **El temps mínim d'aturada de 5
> minuts s'ha d'implementar igualment a la lògica.**

### 🔴 Una contradicció al manual que cal provar

El manual diu dues coses que no encaixen:

> **MEMÒRIA:** *«El aparato memorizará la última configuración cuando esté conectado a la toma
> de corriente […] El aparato funcionará con la **configuración predeterminada** cuando se
> haya **desconectado** de la toma de corriente.»*
>
> **REINICI AUTOMÀTIC:** *«El aparato se encenderá automáticamente y funcionará según la
> **última configuración** cuando vuelva la corriente.»*

Un tall de llum i un endoll intel·ligent que obre el circuit **són elèctricament
indistingibles**: l'aparell no pot saber la diferència. Però si el comportament real fos el
primer —tornar a la configuració de fàbrica— **cada cop que Home Assistant l'apagués i el
tornés a encendre perdria el llindar d'humitat configurat**, i tota l'arquitectura (a) se'n
va en orris en silenci.

**🧪 Prova concreta, cinc minuts:**

1. Posa l'higròstat a un valor inconfusible, per exemple **45 %**.
2. Desendolla'l de la paret. Espera un minut.
3. Torna'l a endollar.
4. **Mira si torna a 45 % o si torna a la configuració per defecte.**

> Si torna a 45 %, endavant amb el disseny previst. Si torna a la de fàbrica, haurem de
> **deixar-lo permanentment alimentat** i governar-lo d'una altra manera — segurament sí que
> caldria la integració Tuya després de tot. **És la prova amb més impacte per minut invertit
> de tot el projecte.**
>
> *21/09/2026:* aquesta «altra manera» ja té nom i és viable: **`tuya-local`**, sense compte
> de desenvolupador. Vegeu [la decisió reoberta](#decisió-no-integrem-el-deshumidificador-per-tuya--es-reobre-provar-tuya-local)
> més avall.

### 🟠 Rendiment a l'hivern

Funciona fins als **5 °C**, o sigui que no s'aturarà. Però amb desgebratge automàtic: per sota
d'uns 15 °C passarà una part del temps descongelant-se en comptes d'assecar, i els 25 L/dia de
catàleg (mesurats a 30 °C / 80 % HR) no s'hi assemblaran gens.

**Conseqüència per a la Fase B:** cal registrar **litres/dia i kWh/dia junt amb la temperatura
del soterrani**. El rendiment real a 12 °C és una dada que no tenim i que canvia el càlcul
d'estalvi.

## ⚠️ El que encara cal verificar

### 1. 🟡 Calibratge creuat

Tens **models barrejats** (3× T315 i 2× T310). Això fa el pas de calibratge **més important**,
no menys: l'error sistemàtic entre models diferents no es cancel·la sol.

**Deixa'ls 24 h junts a la mateixa habitació**, apunta la desviació de cadascun respecte de la
mediana, i li aplico un *offset* fix a Home Assistant. Cost zero, i permet baixar el llindar
de decisió de 2,0 °C a ~1,2 °C — que són hores de ventilació gratuïta guanyades.

### 2. ~~🟡 Credencials de Tapo~~ → ✅ **resolt, i per un camí millor**

> 🔴 **Escrit el 20/09, superat el 21/09.** Deia que la integració oficial `tplink` suporta el
> hub H110 i el consulta localment per IP, i que el pegat era que la configuració inicial
> demana **correu i contrasenya del compte Tapo**. Les dues meitats han canviat.

**`tplink` no suporta aquest hub.** El H110 xifra amb **TPAP**, i la biblioteca que porta
HA 2026.9.3 (`python-kasa` 0.10.2) només coneix KLAP, AES i XOR: el rebutja amb *«Unsupported
device»*. És un problema obert d'upstream
([`python-kasa#1590`](https://github.com/python-kasa/python-kasa/issues/1590)), no nostre.

**La via és Matter**, amb el contenidor `matter-server`. I això **tanca la preocupació de les
credencials en comptes d'esquivar-la**: per Matter no hi ha compte Tapo, ni núvol, ni
contrasenya, ni res que caduqui. L'emparellament és local i les claus viuen a `./matter-data`.

→ Reserva igualment una **IP fixa per al hub** al router: Matter va per IPv6 i multidifusió,
  però l'àlies estable segueix estalviant maldecaps.
→ ⚠️ **`matter-data/` conté les claus dels aparells emparellats.** És al `.gitignore` perquè
  són secrets, i per això és fàcil oblidar-la **a la còpia de seguretat**. Perdre-la obliga a
  reemparellar, i reemparellar **parteix les sèries**.

---

## Els 2× Tapo S110E són els relés dels ventiladors

Un **S110E** és un **mòdul de relé** que va darrere l'interruptor o en línia, amb dos modes:

- **Contacte humit** — commuta directament la càrrega. És el mode per als ventiladors si estan
  cablejats a la xarxa.
- **Contacte sec** — contacte lliure de tensió, per governar equips que tenen la seva pròpia
  entrada de comandament.

I, el que aquí importa més, **mesuren consum**. Amb això es compleix la regla de
[monitoritzacio.md](monitoritzacio.md): *mesura watts, no relés*. «El relé estava tancat» és
feble; **«el ventilador va consumir 45 W durant 18 h/dia els 140 dies» és una prova.**

> ⚠️ **Verificar abans d'instal·lar-los:**
> - **Càrrega màxima** del S110E i si està homologat per a **càrrega inductiva** (motor), no
>   només resistiva. Els motors tenen corrent d'arrencada.
> - **Instal·lació en cablejat fix → instal·lador autoritzat**, conforme al REBT.
> - ✅ **Ja resolt a favor de Matter** per al hub, i el S110E també el suporta. Val la pena
>   emparellar-los **tots dos per Matter** i no barrejar vies: `tplink` ni tan sols accepta el
>   hub (xifratge TPAP), i Matter és més local —sense núvol ni compte.
> - Si permeten conservar l'**interruptor físic** com a entrada lògica (l'equivalent del mode
>   *detached*), que és el que dona el millor control manual.

## 🔧 El que encara falta

| Què | Per a què | Estat |
|---|---|---|
| **ESP32 + 2× DS18B20** | **Temperatura superficial de la paret freda** | Per comprar (~15 €) |

**I això és tot.** El maquinari del projecte està pràcticament complet.

> El **DS18B20 a la paret** segueix sent el component que més val per euro: és l'únic sensor
> que **discrimina directament** condensació de capil·laritat. Els Tapo diuen com està
> **l'aire**; només aquest diu com està **la paret**.

---

## Decisió: ~~NO integrem el deshumidificador per Tuya~~ → es reobre: provar `tuya-local`

> ### 🔄 Revisió del 21/09/2026 — dos dels tres motius han caigut
>
> | Motiu del 20/09 | Ara |
> |---|---|
> | `tuya-local` demana un compte de desenvolupador de Tuya IoT que caduca | ❌ **Ja no.** Té una **configuració assistida**: s'entra **un sol cop** amb l'app Smart Life, se n'extreu la *local key* **sense compte de desenvolupador**, i a partir d'aquí tot va en local |
> | Components de tercers per HACS, rebutjats | ❌ **Superat** pel canvi d'objectiu del mateix 21/09 ([decisio-stack.md](decisio-stack.md)) |
> | El D825 no és a la llista de `tuya-local` | ✅ **Segueix sent veritat** (hi ha D720, D812 i D820A). Però `tuya-local` reconeix els aparells **per les dades que exposen, no pel nom del model**: és probable que el D825 encaixi amb la configuració del D820A. **No se sabrà sense provar-ho** |
>
> **Què guanyaríem sobre el P110 sol:**
>
> - **El llindar d'HR des d'HA**, per exemple més baix a la franja vall.
> - **Engegar-lo i aturar-lo per ordre, sense tallar-li el corrent.** Així la protecció de 5
>   minuts del compressor **segueix comptant** (vegeu més amunt), i la prova 0.2b de la
>   memòria del llindar **deixa de ser bloquejant**.
> - **El seu estat**: l'HR que mesura ell, la velocitat, i els codis **P1** (desgebrant) i
>   **P2** (dipòsit ple). El P1 és la dada que ens falta per a l'hivern: quanta estona passa
>   descongelant en comptes d'assecar.
>
> **El P110 es queda igualment.** És qui mesura els kWh, i el tall dur si tot l'altre falla.
>
> **La prova, i com fer-la sense fer-nos mal:**
>
> 1. **Emparellar-lo amb Smart Life a la Wi-Fi del router SIM**, la mateixa que tindrà al
>    local. ⚠️ Cada cop que es **reemparella**, la *local key* **canvia** i HA el perd fins
>    que se'n torna a extreure. Emparellar-lo a la Wi-Fi de casa i tornar-ho a fer al local
>    seria fer la feina dues vegades.
> 2. **Reserva DHCP** per al deshumidificador, com la resta (A.2).
> 3. `tuya-local` per HACS, configuració assistida, i mirar **si el reconeix**.
> 4. Si el reconeix: **fixar-ne els noms a [noms-entitats.md](noms-entitats.md) abans** que
>    tinguin històric (regla A.8). **Al principi, només lectura i llindar:** l'actuador de la
>    lògica segueix sent el `switch.deshumidificador` del P110. Dos amos per al mateix aparell
>    no, fins que es decideixi a posta.
> 5. Si **no** el reconeix: no hem perdut res i seguim amb el P110 sol, com diu la decisió
>    original de sota.
>
> ⚠️ Si la prova 0.2b surt malament —que torni a la configuració de fàbrica després d'un
> tall—, això deixa de ser una millora i passa a ser **la via**.

*Decisió original del 20/09, conservada pel raonament:*

El Qlima és un dispositiu **Tuya/Smart Life**. Es podria integrar a Home Assistant de dues
maneres, i **descartem totes dues de moment**:

| Via | Per què no |
|---|---|
| Integració **Tuya oficial** | Passa pel núvol. Hi ha informes d'entitats mal mapades en deshumidificadors Qlima. *(21/09: ara s'hi entra amb un codi QR de l'app, però segueix depenent del núvol — la via, si n'hi ha, és `tuya-local`)* |
| **tuya-local** (HACS) | Local i millor, però cal extreure la *local key* amb un compte de desenvolupador de Tuya IoT, la llicència del qual **caduca i s'ha de renovar**. Suporta D720, D812 i D820A, **però el D825 no hi és a la llista** *(21/09: el compte ja no cal — vegeu la revisió de dalt)* |

**El que farem:** l'**higròstat propi** del Qlima regula la humitat, i el **Tapo P110** el
governa i en mesura el consum. Amb això tenim les dues coses que necessitem —engegar-lo o no,
i saber què gasta— **sense cap dependència de núvol nova ni cap llicència que caduqui**.

> És la decisió més alineada amb «com menys infraestructura millor» de tot el projecte:
> s'estalvia una integració, un compte de desenvolupador i un mode de fallada.
>
> Si més endavant vols ajustar el llindar d'HR **a distància**, es reobre. Mentre el llindar
> es posi un cop i no es toqui, no cal.

---

## 🛰️ Validar el sensor exterior contra dades oficials

**Idea teva, i és bona.** Comparar el sensor de *Fora* amb les dades d'un centre
meteorològic oficial serveix per a **tres coses alhora**, i costa una integració gratuïta:

### 1. Saber si el sensor és fiable

Es crea un sensor de **residu**:

```
residu = Td_fora(sensor propi) − Td_estacio(oficial)
```

En condicions normals el residu ha de ser petit i **estable**. Quan comenci a **derivar**,
vol dir que el sensor s'ha mullat, s'ha embrutat o s'està morint — i això es detecta
**setmanes abans** que faci prendre una decisió equivocada. És un vigilant de salut que no
costa cap maquinari.

> **Per què el punt de rosada i no la temperatura:** una estació a 3 km tindrà una temperatura
> diferent de la teva (illa de calor urbana, altitud, orientació) i una HR diferent. Però el
> **punt de rosada és una propietat de la massa d'aire** i varia molt poc a escala de
> quilòmetres. És l'única de les tres magnituds que es pot comparar honestament a distància —
> i és, casualment, la que ja fèiem servir per decidir.

### 2. El sensor de pluja que ens faltava

La lògica necessita **bloquejar la ventilació quan plou** (un sensor exterior mullat dona HR
falsa durant hores). Les integracions oficials donen **precipitació**, així que aquest bloqueig
surt de franc en comptes d'haver de comprar un sensor de pluja.

### 3. Reforçar el valor probatori

Això és el que crec que val més. Davant d'un pèrit, hi ha molta diferència entre:

> *«El meu sensor deia que fora hi havia 17,5 °C de punt de rosada.»*

i

> *«El meu sensor va seguir l'estació oficial de l'AEMET amb una desviació mitjana de 0,4 °C
> durant sis mesos, i aquí hi ha les dues sèries superposades.»*

La segona converteix un aparell de 15 € en **un instrument calibrat contra una referència
pública**. Per a la defensa de les humitats, això val molt més que el que costa muntar-ho.

### Quines fonts

| Font | Què dona | Com |
|---|---|---|
| **AEMET OpenData** | Integració **oficial** de Home Assistant. Dona `dew_point` directament, a més de temperatura, HR, pressió i precipitació, d'una estació concreta, actualitzat cada hora | Cal una **clau d'API gratuïta** a `opendata.aemet.es` i triar l'estació més propera |
| **Meteocat — XEMA** | Xarxa d'estacions automàtiques de la Generalitat, amb estacions **dins de Barcelona** i dades cada 30 min | No té integració oficial a HA; caldria consultar-ne l'API des de `nit.py` |
| **Met.no** | Integració gratuïta i sense clau | ⚠️ És un **model de predicció**, no una observació. Serveix de reserva, no per validar |

**Recomanació:** començar amb **AEMET OpenData** (oficial, gratuïta, dona el punt de rosada
ja calculat i la precipitació). Si l'estació més propera queda lluny, afegir **Meteocat XEMA**
com a segona referència des de `nit.py`, que ja fa una connexió diària.

> ⚠️ **La font oficial és per validar i per detectar pluja, no per decidir.** La decisió de
> ventilar la pren **sempre el sensor local**: l'aire que entra per la reixa és el del carrer,
> no el de l'estació. Si algun dia el sensor local cau, el sistema **s'atura** (fallada
> segura); no passa a decidir amb dades d'una estació a quilòmetres.

## ⚡ Dos avisos operatius

### Cicle curt del compressor

Com que l'aparell **es reprèn sol** en tornar el corrent, si Home Assistant encén i apaga
l'endoll de pressa, el compressor **arrenca contra pressió** i es fa malbé.

→ El **temps mínim d'aturada de 5 minuts** deixa de ser una recomanació i passa a ser
**obligatori** a la lògica. Vegeu [control-punt-rosada.md](control-punt-rosada.md).

### Refrigerant R290 (propà)

Són 70 g de gas **inflamable**. No és perillós en una estança normal —i un soterrani de ~46 m²
ho és de sobres— però:

- No tancar-lo en un armari petit ni en un espai sense ventilació.
- Cap font d'ignició a prop.
- Si es manipula o es transporta, tombat mai; dret i deixant-lo reposar abans d'engegar-lo.

## 💶 Què costa fer-lo anar

A 470 W i amb la [tarifa Naturgy Noche](../local/subministraments.md):

| Franja | €/h | 8 h/dia | 30 dies |
|---|---|---|---|
| 🟢 Vall | 3,5 c€ | 0,28 € | **8,3 €** |
| 🟡 Pla | 5,1 c€ | 0,41 € | 12,3 € |
| 🔴 Punta | 8,6 c€ | 0,69 € | **20,6 €** |

**Desplaçar-lo de punta a vall estalvia uns 12 € al mes** amb 8 h diàries. I si l'automatisme
del punt de rosada aconsegueix substituir-ne una part per ventilació —30–150 W en comptes de
470 W— l'estalvi s'hi suma. Aquesta taula és la que la Porta B ha de validar amb dades reals.
