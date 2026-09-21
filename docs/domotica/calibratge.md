# Calibratge creuat dels sensors — procediment

> **Estat: primera tanda feta el 21/09/2026, provisional.** Els desplaçaments de la franja
> **49–59 % d'HR** estan mesurats, però **no s'han aplicat**: falta la franja humida, que és
> on viurà el soterrani a l'hivern. Els de `rosada.yaml` segueixen sent identitat. Fase
> **A.13** de [fases.md](fases.md).

## Per què, i quant val

La decisió del soterrani és una **resta**: `ΔTd = Td_interior − Td_exterior`. Per tant el que
fa mal **no és l'error absolut** de cada sensor, sinó la **diferència entre dos**. Un error que
tinguin tots cinc per igual s'anul·la sol en la resta.

Tens **models barrejats** —3× T315 i 2× T310—, i entre models l'error sistemàtic no es
cancel·la. *(⚠️ La primera tanda ho va desmentir: **no és una qüestió de model**, cada sensor
té la seva desviació. Vegeu els resultats més avall.)*

El premi és concret: amb la dispersió per sota de **0,3 °C** es pot baixar `delta_td_on` de
**2,0 a ~1,2 °C**, i això són **hores de ventilació gratuïta** cada setmana. Amb l'objectiu nou
—optimitzar el consum— aquest és exactament el guany que es busca.

### El pressupost d'error

Amb la fórmula de Magnus, a 20 °C:

| Error | Efecte sobre Td |
|---|---|
| 1 % d'HR | **≈ 0,2 °C** |
| 1 °C de T | **≈ 0,95 °C** |

La temperatura pesa gairebé tant com la humitat, cosa que és fàcil de passar per alt. Per
arribar a 0,3 °C de dispersió calen **~1,5 % d'HR i ~0,2 °C** entre els dos sensors que
decideixen.

## ⚠️ El gra de la mesura mana sobre el mètode

Els Tapo donen l'**HR en percentatges sencers** i la T en dècimes, i Home Assistant **només
enregistra quan el valor canvia**: unes 6 mostres d'humitat en 6 hores.

Un 1 % d'HR ja són 0,2 °C de Td, o sigui **dos terços del pressupost en una sola lectura**. I
amb l'aire quiet els cinc sensors es queden clavats en un enter: per molta estona que hi
dediquis, no en trauràs res més fi.

D'aquí surt tot el disseny de l'experiment:

> **Rampes lentes, no replans.** En una rampa cada sensor creua el 60→61 % en un instant una
> mica diferent, i aquest desfasament és informació **per sota del gra**. Un replà mort no
> dona dither i et deixa clavat a ±0,5 %.

I d'aquí surt també per què calen **les dues rampes**, la seca i la humida: si el hub triga
sempre una mica més a enviar un sensor concret, aquest **retard sistemàtic s'assembla
exactament a un desplaçament de calibratge**. En pujada desplaça cap a un costat i en baixada
cap a l'altre, i fent-ne la mitjana es cancel·la. Amb una sola rampa no hi ha manera de
distingir-ho, i et quedaries amb un número que sembla calibratge i és latència.

## Abans de començar

- [ ] **Bateries** dels cinc sensors.
- [ ] Els cinc **junts**, sobre superfície no metàl·lica, a mitja alçada, **fora del raig** de
      l'aire condicionat: un sensor dins del doll llegeix el doll, no l'habitació.
- [ ] Un **ventilador petit apuntant a la paret** (mai als sensors) per barrejar l'aire. En
      aire quiet cada sensor es fa el seu microclima, i aquest és l'error més gros d'una prova
      de co-ubicació.
- [ ] **Encendre `input_boolean.mode_calibratge`.** Mentre està encès,
      `sensor.decisio_del_soterrani` val `calibratge` i cap automatisme no actua.
- [ ] No tocar-los ni respirar-hi a prop durant la prova: l'alè puja l'HR local durant minuts.

## El recorregut — unes 36 h

| | Tram | Durada | Per a què |
|---|---|---|---|
| 1 | **Estabilització**, sense tocar res | 2 h | Base de referència i dispersió de partida |
| 2 | **Baixada lenta** amb l'aire condicionat, fins on arribi (~40–45 %) | 6–8 h | Branca seca |
| 3 | **Pujada lenta** amb tovalloles molles o vapor, fins al 75–85 % | 6–8 h | El tram que importa: el soterrani a l'hivern serà 65–90 % |
| 4 | **Retorn a ambient**, sense fer res | 4 h | **Prova d'histèresi** |
| 5 | **Nit sencera** sense intervenir | 8–10 h | Rang de temperatura gratuït |

**Ritme:** que l'HR no es mogui més de **~7 % per hora**. Més de pressa i el que mesuraràs serà
la diferència de **temps de resposta** entre models, no de calibratge.

El **tram 4** és el que respon si el desplaçament és constant. Si un sensor no torna a la
mateixa lectura *relativa als altres* després d'haver passat pel 85 %, aquell sensor té
histèresi i **no admet cap corba**: se li posa una constant i els seus valors alts es prenen
amb pinces.

Si el tram 3 es queda curt, el millor recanvi és el **bany després de dutxes**: arriba al 90 %
sense esforç.

## Després

```bash
export HA_URL=http://<el-teu-servidor>:8123
export HA_TOKEN_FILE=~/.ha_token
python3 tools/calibratge.py --descarrega --hores 48
```

L'eina **troba sola la finestra** a partir del marcador, parteix les rampes, ajusta i escriu
les línies per enganxar. El que has de mirar de la seva sortida:

| Què diu | Què vol dir |
|---|---|
| `rang assolit: HR 44–81 %` | **Si el rang és curt, no s'ajusta cap pendent** i només es posa un desplaçament. És correcte: un pendent sense recorregut és soroll disfressat de ciència |
| Comparació entre rampes | Si `c_t` o `c_rh_b` no s'assemblen entre baixada i pujada, hi ha **retard o histèresi**. El número no s'ha de fer servir |
| Dispersió de Td abans → després | El criteri. **≤ 0,30 °C** per poder abaixar el llindar |

Els números van a les cinc plantilles de [`packages/rosada.yaml`](../../config/packages/rosada.yaml),
que ja tenen el forat preparat:

```jinja
{% set c_t = 0.0 %}{% set c_rh_a = 1.0 %}{% set c_rh_b = 0.0 %}
```

⚠️ **Es corregeix només el Td derivat. La lectura crua no es toca mai**, de manera que l'arxiu
conserva la mesura i la correcció per separat i sempre es pot desfer.

I en acabat: **apagar el mode calibratge** i repartir els sensors.

## ⚠️ Això no serà un calibratge d'hivern

Es fa a casa al setembre, a 22–28 °C. El soterrani al gener serà de 8 a 15 °C, i l'error dels
capacitius depèn de la temperatura.

Per això, **al costat dels números hi va escrit el rang de validesa**. Quan es repeteixi al
soterrani a l'hivern, el git conservarà les dues i es veurà si el calibratge depèn de la
temperatura — que és una dada que ara no tenim i que val la pena tenir.

Repetir-ho és barat: els sensors ja hi seran, i només cal tornar a encendre el marcador.

## Per què es MARCA el període i no s'aparta

La temptació és desar les dades del calibratge en un altre lloc perquè no contaminin la sèrie.
No es fa, i el motiu és aquest:

**Aquestes dades no es poden repetir.** Són l'única mesura de la desviació entre sensors que
existirà mai amb ells tots junts; un cop repartits pel local, ja no hi tornaran a ser. Són
valuoses, no brutícia.

Marcar el període amb un helper —que queda **registrat a l'històric**— fa que **l'arxiu
s'expliqui sol**: d'aquí a un any qualsevol sabrà per què hi ha un tram on cinc sensors del
soterrani deien el mateix des d'una taula del menjador. Sempre en pots excloure el tram; el
que no podries és recuperar la procedència si l'haguessis apartat.

## Primera tanda — 21/09/2026

Els cinc sensors junts a casa durant **~11 hores** (00:43–11:26), amb una estona d'aire
condicionat al final. **El marcador no es va encendre**, de manera que la finestra s'ha donat a
mà; el període queda dins de la base de dades d'experimentació, que `inicia-serie.sh` arxiva.

### Què diuen les dades

**La temperatura no necessita calibratge.** Els cinc coincideixen dins de **±0,1 °C**, que és
el gra del sensor: la desviació que es veu és quantització, no error.

**La humitat, sí — i molt.** Cada sensor té una desviació **estable tota la nit**:

| Sensor | Model | Correcció d'HR | Llegeix |
|---|---|---|---|
| `soterrani_fons` | T315 | **+2,2** | baix |
| `soterrani_centre` | T315 | **−1,1** | alt |
| `soterrani_gran` | T310 | +0,3 | — |
| `baixa` | T315 | **−1,2** | alt |
| `exterior` | T310 | 0,0 | — |

Entre el que llegeix més baix i els que llegeixen més alt hi ha **~3,4 punts d'HR**, que són
**~0,7 °C de Td**: més del doble del pressupost d'error.

| Dispersió de Td entre els cinc | |
|---|---|
| Sense corregir | **0,95 °C** |
| Amb només desplaçament | **0,24 °C** ✅ dins de l'objectiu de 0,30 |
| Amb pendent i desplaçament | 0,25 °C — **el pendent no afegeix res** |

### Tres coses que no s'esperaven

**1. No és una qüestió de model.** El pla suposava que l'error vindria del T310 contra el
T315. No: els dos T310 quadren entre ells, i entre els T315 hi ha el que llegeix més baix de
tots (`fons`) i dos dels que llegeixen més alt. **Cada sensor és el seu cas.**

**2. El màxim amplifica l'error.** La referència interior és el **punt de rosada més alt** dels
tres del soterrani. Sense corregir, **`centre` la marca el 99 % del temps** —no perquè sigui el
punt més humit, sinó perquè és el que llegeix més alt—, i això infla el Td de referència
**+0,16 °C**. Un màxim sempre tria el sensor amb el biaix més positiu. Quan estiguin repartits
pel soterrani, l'atribut `punt_mes_humit` assenyalarà el sensor esbiaixat, no el racó humit,
fins que es calibrin.

**3. L'eina ajustava un pendent que no havia d'ajustar.** Amb 10 punts de recorregut n'hi havia
prou per passar el llindar de llavors, però aquell pendent no millorava res i, extrapolat al
85 % de l'hivern, **inventava fins a 1,5 punts d'HR de correcció**. El llindar ha pujat a 20
punts, i l'eina escriu ara el rang de validesa al costat dels números.

### Què NO diuen

**El rang és de només 49–59 % d'HR i 25,9–27,0 °C.** El soterrani viurà al **65–90 %** a
l'hivern, que és precisament on els capacitius barats es tornen menys fiables. Aplicar aquests
desplaçaments allà és una extrapolació. I com que no hi va haver cap rampa controlada en els dos
sentits —la nit va ser plana i l'aire condicionat només va fer baixar—, **encara no es pot
descartar que part de la desviació sigui retard del hub**.

Per això no s'han aplicat: la tanda següent és barata i tapa exactament aquests dos forats.

## Segona tanda proposada — la franja humida

**Un tàper tancat amb sal de cuina.** Una pasta de sal comuna (NaCl) i una mica d'aigua —**amb
cristalls sense dissoldre a la vista**— manté l'aire d'un recipient tancat al **75,3 % d'HR**,
gairebé independentment de la temperatura. És el mètode clàssic de calibratge d'higròmetres, i
ho resol tot alhora:

| Què aporta | Per què importa |
|---|---|
| **Franja alta**, fins al 75 % | La que falta, i la que viurà el soterrani |
| **Pujada lenta**, en hores | Dona el desplaçament sense que el retard hi pesi |
| **Un valor absolut conegut** | El consens entre cinc sensors no et diu si tots cinc llegeixen alt; la sal, sí |
| **Dos graons**, de baixada i de pujada | Mesuren el **retard** de cada sensor, i si és **simètric** |

### Rampa lenta per al número, graó per al retard

Són dues magnituds diferents, i cadascuna demana una prova diferent:

| Vols mesurar… | Et cal | Per què |
|---|---|---|
| **El desplaçament** | rampa **lenta** | L'error que hi afegeix el retard és *ritme × retard*. A 7 %/h amb 5 minuts de retard són 0,6 punts. Una dutxa (~35 punts en 10 minuts) en donaria ~17, que taparien del tot els 1–2 punts que es busquen |
| **El retard** | **graó** ràpid | Es veu directament qui reacciona i quan |

El graó té un valor afegit. Les dues rampes cancel·len el retard **només si és simètric**, i els
capacitius acostumen a **assecar-se més a poc a poc del que s'humitegen**: si és així, la
mitjana no el cancel·la del tot. Els dos graons **comproven aquesta suposició** en comptes de
donar-la per bona.

La dutxa es va descartar també per dues raons més: **escalfa** (i 1 °C de T són ~0,95 °C de Td,
de manera que barreja temperatura i humitat) i **l'aire no hi està barrejat**.

### El recipient

- **Un tàper o una caixa de plàstic** (també serveix el vidre). **Mai de metall:** una olla
  tapada fa de gàbia i els sensors **no poden transmetre** — mesurarien, però no arribaria cap
  lectura al hub.
- **Com més petit, més ràpid** s'equilibra: en un tàper mitjà, **2–4 hores**.
- Hi han de cabre **els cinc alhora**, sense apilar, sense tocar la sal i amb una mica d'aire al
  voltant. Fer-ho en dues tandes no serveix.
- **Tancat del tot.** A diferència d'unes tovalloles molles, la sal només fixa el 75 % si no hi
  entra aire de fora.

### La pasta

- **2–4 cullerades de sal fina de cuina.** No serveix la «baixa en sodi» (és una barreja de KCl
  i NaCl i dona un altre valor) ni la que porta herbes o all.
- Aigua **de mica en mica** fins que tingui la **textura de sorra mullada**. Reposar-la cinc
  minuts: si ja no es veuen cristalls, s'ha dissolt tota i cal més sal.
- En un **platet**, i els sensors **aixecats** sobre un drap plegat o una reixeta, **sense tocar
  mai la pasta**: és corrosiva i condueix.
- **La sal no es gasta.** Es guarda en un pot tapat per repetir-ho a l'hivern (però no per
  cuinar).

### El recorregut

1. **Encendre `input_boolean.mode_calibratge`.**
2. **Tancar**, i esperar el **replà**: la humitat dels cinc quieta durant una hora. No obrir per
   mirar; es segueix des del tauler.
3. **Graó de baixada:** treure **el suport amb els cinc a sobre**, d'una vegada, a l'habitació.
   Tornar a tancar el tàper, perquè es mantingui humit. **Apuntar l'hora.**
4. **Una hora** a l'aire de l'habitació.
5. **Graó de pujada:** tornar el suport al tàper i tancar ràpid. **Apuntar l'hora.**
6. **1–2 hores** més, i **apagar el marcador**.

⚠️ **Moure el suport, no els sensors.** Agafats un per un, hi ha segons de diferència entre ells
i calor de mans en uns i no en els altres, i totes dues coses s'assemblen justament al retard que
es vol mesurar. Movent el suport, es mouen tots cinc al mateix instant i ningú no els toca.

⚠️ **Haver-los tocat per posar-los** altera els primers minuts: la calor de les mans escalfa la
carcassa i l'alè i la pell pugen l'HR local. S'esvaeix en 10–30 minuts, i per això **l'anàlisi
en descarta els primers 30** després de tancar. El número bo surt del replà, hores després.

### Què se n'ha de mirar

- **On s'estabilitza cada sensor contra el 75,3 %.** Si tots cinc donen el 78 %, tots llegeixen
  2,7 punts alt —cosa que el consens no pot veure mai—. És un ancoratge absolut, que val per si
  algun dia es reprèn la via documental.
- **Als graons, qui reacciona i quan**, i si el retard de baixada s'assembla al de pujada.
- ⚠️ **La resolució temporal del graó** depèn de cada quant informa el hub quan els valors canvien
  de pressa, i això encara no se sap. El mateix graó ho dirà.

⚠️ **Evitar el 100 %.** Si l'aire arriba a condensar sobre els sensors, poden quedar-se enganxats
hores. Amb sal no hi arriba; amb aigua sola, sí.

**Opcional, per a un punt més alt:** el clorur de potassi (KCl) **pur** dona el **84 %**.

## Registre

| Data | Rang assolit | Dispersió abans → després | Notes |
|---|---|---|---|
| 21/09/2026 | HR 49–59 % · T 25,9–27,0 °C | **0,95 → 0,24 °C** (només desplaçament) | ~11 h a casa, marcador sense encendre. Temperatura sense correcció. **No aplicat**: falta la franja humida |

> **Incidències de la tanda en marxa** (marcador encès des de les 12:09 del 21/09/2026):
>
> - **18:15** — el **deshumidificador** s'endolla i arrenca. ✅ **En una altra habitació, a
>   posta** per no influir en el calibratge (confirmat per l'usuari), i amb un aire condicionat
>   que també asseca: per això ell llegia 44 % amb els sensors al 66–72 %. **No toca les
>   rampes.**
> - **18:49:41** — **reinici d'HA** per carregar `tuya-local`, decidit amb l'usuari. L'API
>   torna al cap de **9 s**, i als cinc sensors **no hi queda cap `unavailable` gravat** ni
>   cap salt: la rampa humida segueix llisa.
