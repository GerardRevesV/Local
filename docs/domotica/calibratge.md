# Calibratge creuat dels sensors — procediment

> **Estat: dues tandes mesurades, cap d'aplicada (22/09/2026).** La primera dona la franja
> **49–59 % d'HR**; la segona, el **replà del tàper de sal al 73 %**, i diu que els desplaçaments
> de la primera **no hi valen** i que tots cinc llegeixen baix → [el replà](#el-replà--22092026).
> Falta el punt en fred: la [tercera tanda, a la nevera](#tercera-tanda--la-nevera). Els de
> `rosada.yaml` segueixen sent identitat. Fase **A.13** de [fases.md](fases.md).

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

> ⚠️ **Corregit el 22/09/2026:** fins llavors l'eina demanava l'històric **sense `end_time`**, i
> Home Assistant en torna només **24 h des de l'inici**, demanis les hores que demanis
> (comprovat amb HA 2026.9.3). Amb `--hores 48` o les 72 per defecte, l'ajust es quedava les
> 24 h **més velles** i perdia les més recents —les rampes de la sal i de la nevera— **sense
> cap avís**. Només afecta les descàrregues de més de 24 h, però **qualsevol calibratge tret amb
> `--descarrega` abans de la correcció s'ha de tornar a calcular.**

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

## Segona tanda — la franja humida

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

### El replà — 22/09/2026

Tàper tancat a les **12:09 del 21/09**, amb el marcador encès. **Al replà des de les ~05:00 del
22/09**, i quiet més de set hores: cap sensor s'hi mou més d'un punt, que és el gra. Va trigar
**~17 hores**, no les 2–4 previstes: fins al 70 % en unes 7 h, i els últims tres punts, tota la
nit. L'habitació es va escalfar fins a 29,6 °C a la tarda, i com més calent és l'aire, més aigua
ha d'evaporar la pasta per arribar al mateix percentatge.

Mitjanes de 05:00 a 12:20, a **27,8 °C**, on la sal fixa el **75,2 %**. Com a la primera tanda,
la correcció és el que s'ha de **sumar** a la lectura:

| Sensor | Llegeix | Correcció contra la mediana | La del 21/09, al 49–59 % | **Correcció contra la sal** |
|---|---|---|---|---|
| `soterrani_fons` | 72,0 | +0,8 | +2,2 | **+3,2** |
| `soterrani_centre` | 74,8 | **−2,0** | −1,1 | +0,4 |
| `soterrani_gran` | 72,0 | +0,8 | +0,3 | **+3,2** |
| `baixa` | 74,0 | −1,2 | −1,2 | +1,2 |
| `exterior` | 72,8 | 0,0 | 0,0 | **+2,4** |

**1. La temperatura torna a quadrar**: els cinc, dins de **±0,05 °C** de la mediana. Confirmat
que no cal corregir-la.

**2. Els desplaçaments del 21/09 no valen al 73 %.** Aplicats al replà, la dispersió de Td baixa
de **0,61 a 0,40 °C**: millora, però queda per sobre dels 0,30. `baixa` i `exterior` no es mouen,
però `fons` passa de +2,2 a +0,8 i `centre`, de −1,1 a −2,0: en aquests dos **la desviació depèn
de l'HR**, amb canvis més grans que el gra d'un replà (±0,5). Va ser bona decisió no aplicar-los.
I el recorregut ja va del 49 al 75 %, 26 punts: per sobre dels 20 que l'eina demana per ajustar
un pendent.

**3. Tots cinc llegeixen baix contra la sal**, de 0,4 a 3,2 punts; la mediana, uns **2,4**. És
el que el consens no podia veure mai. A la resta ΔTd no li fa res, perquè s'anul·la; sí que pesa
en tot el que és **absolut**: el marge contra la paret (≈0,5 °C de Td) i els llindars d'HR del
deshumidificador.

⚠️ **Amb dues condicions.** Que la tapa tanqui del tot: una fuita petita deixa el replà per sota
del 75,3 % i es confondria amb uns sensors que llegeixen baix, i el sotrac de les 15:00 (vegeu
les [incidències](#registre)) demostra que, si es mou, la tapa deixa entrar aire. I que **la
pasta sigui a la mateixa temperatura que els sensors**: la sal fixa el 75,3 % a la seva
temperatura, i a 28 °C cada grau de diferència són ~5 punts d'HR. Els 2,4 punts de la mediana
equivalen a una pasta **només 0,5 °C més freda** que els sensors —la taula, per exemple—, i
ningú no ho va mesurar. *(Es va veure a la nevera, el 22/09, on la diferència era de graus.)*
L'ancoratge absolut, doncs, és **provisional**; les correccions **entre sensors** no en depenen.

**Dispersió de Td al replà, sense corregir: 0,61 °C** (al 55 % del 21/09, 0,95).

**Els graons ja no calen per als números.** Servien per saber si el retard del hub contaminava
els desplaçaments trets de **rampes**. Els d'aquesta tanda surten d'un **replà**, on el retard no
hi pesa, i la primera tanda va ser gairebé tota plana. L'entrada a la nevera dona igualment un
graó on es veu qui reacciona i quan.

## Tercera tanda — la nevera

**Per què.** Les dues tandes s'han fet a 26–29 °C, i el soterrani al gener serà a **8–15 °C**.
L'error dels capacitius pot dependre de la temperatura, i sense un punt en fred no se sabria fins
a l'hivern. La sal hi continua valent: a 5–10 °C fixa el **75,7 %**, pràcticament el mateix. I
com que la segona tanda ja té un replà gairebé a la mateixa HR, **la diferència entre tots dos
replans és l'efecte de la temperatura, i prou**.

**No és massa fred.** Una nevera a 4–8 °C és dins del que aguanten. El congelador, no: ni cal ni
convé, perquè el soterrani no hi baixarà mai.

### On

- A la zona **menys freda i més quieta**: el **calaix de les verdures**, si hi cap, o un
  prestatge del mig. L'ideal són uns **8 °C**, com el soterrani.
- **Lluny de la paret del fons**, que és on hi ha l'evaporador: és el punt més fred, i allà sí
  que podria condensar dins del tàper.
- ⚠️ **Sobre un drap plegat i embolicat amb un altre**, secs. La sal fixa el 75,7 % **a la
  temperatura de la pasta**; si la pasta, damunt del prestatge fred, és més freda que els
  sensors, ells llegeixen menys (a 5 °C, cada grau de diferència són ~5 punts). El drap aïlla el
  tàper del prestatge i dels corrents d'aire, i fa que tot sigui a la mateixa temperatura. *(Après
  el 22/09: sense drap, 2 °C de diferència entre sensors i la pasta fent baixar l'aigua de
  l'aire.)*

### Els riscos, i com s'eviten

| Risc | Per què | Com s'evita |
|---|---|---|
| **La ràdio** | La nevera és una caixa de metall, com l'olla descartada. Per la junta de la porta sovint en surt prou, però no es pot garantir | Es prova la primera mitja hora, abans de jugar-s'hi la nit |
| **Condensació en entrar** | Tancat, l'aire del tàper (28 °C, Td 22 °C) s'entelaria per dins en refredar-se, i gotejaria | Entra **obert**: l'aire humit en surt i el substitueix el de la nevera. Els sensors, mentre es refreden, són més calents que l'aire del voltant i no hi condensa res. Es tapa al cap d'una hora, allà dins |
| **Condensació en sortir** | Uns sensors a 6 °C en una habitació a 28 °C «suen» a l'instant, com una llauna freda | Surt **tapat**, i no s'obre fins que és a temperatura d'habitació: l'aigua condensa per fora del plàstic |
| **La porta i el compressor** | Cada obertura hi fica aire calent; el compressor fa pujar i baixar la T un o dos graus | Avisar a casa que aquella nit **no l'obrin gaire ni moguin el tàper** (vegeu el sotrac del 21/09). La resta, el tàper l'esmorteeix |

### El recorregut

El **marcador segueix encès** des del 21/09: aquesta tanda continua la segona i no s'apaga
entremig.

1. **Destapar el tàper i posar-lo a la nevera**, amb la sal i el suport a dins, sense tocar els
   sensors. La tapa, al costat, perquè es refredi també. **Apuntar l'hora.**
2. **La primera mitja hora, la prova de ràdio.** Els cinc han d'enviar lectures noves amb la
   temperatura baixant; es mira des del tauler, sense obrir. Si en falta algun, provar un lloc
   més a prop de la porta; si no n'arriba cap, s'abandona: sense dades a HA, la tanda no serveix.
3. **Al cap d'una hora**, quan la T dels cinc ja no baixi, **tapar el tàper allà dins**, ràpid i
   sense treure'l. **Apuntar l'hora.**
4. **Tota la nit.** En fred tot s'evapora més a poc a poc: compta amb **12 hores o més**. El replà
   el marquen les dades —l'HR dels cinc quieta almenys una hora—, no el rellotge.
5. **Treure'l tapat**, eixugar-lo per fora i **no obrir-lo** fins que la T dels cinc sigui la de
   l'habitació, **1–2 hores**. **Apuntar l'hora.**
6. **Obrir-lo i deixar-los 1–2 hores a l'aire de l'habitació**, junts. És la **prova
   d'histèresi** del tram 4: si, a la mateixa HR, un sensor no torna a la desviació que tenia el
   21/09 després d'haver passat pel 75 % i pel fred, aquell sensor no admet cap corba.
7. **Apagar el marcador.**

### Com es llegeix

Per **replans**, no per rampes:

| Replà | HR | T | Què en surt |
|---|---|---|---|
| La nit del 20–21/09 | ~55 % | ~26 °C | Desplaçaments contra la mediana |
| El tàper, 22/09 | 73 % (sal: 75,2) | 27,8 °C | Desplaçaments i ancoratge absolut |
| La nevera | sal: ~75,7 | ~6–8 °C | El mateix, **en fred** |

La proposta per decidir què s'aplica:

- **Si el replà fred dona les mateixes correccions que el calent** (dins del gra, ±0,5), el
  calibratge no depèn de la temperatura entre 6 i 28 °C: pendent i desplaçament amb els dos
  replans calents, i s'apliquen.
- **Si no**, mana el **fred**, que és el que s'assembla a l'hivern del soterrani: se n'apliquen
  les constants, i es repeteix al soterrani al gener.
- **L'ancoratge absolut**, si les dues sals coincideixen, es dona per bo.

⚠️ **`tools/calibratge.py` no fa aquesta lectura**: parteix la finestra per rampes, compara
contra la mediana i barrejaria el fred i el calent en un sol ajust. ⏳ Cal afegir-hi els replans i
la sal; fins llavors, l'anàlisi d'aquesta tanda es fa a part. I la finestra ja fa **més de
24 h**: l'eina ja la baixa sencera ([corregit el 22/09](#després)), però qualsevol altra
descàrrega ha de portar `end_time`, perquè sense HA en torna només 24.

## Registre

| Data | Rang assolit | Dispersió abans → després | Notes |
|---|---|---|---|
| 21/09/2026 | HR 49–59 % · T 25,9–27,0 °C | **0,95 → 0,24 °C** (només desplaçament) | ~11 h a casa, marcador sense encendre. Temperatura sense correcció. **No aplicat**: falta la franja humida |
| 22/09/2026 | HR 73 % (replà del tàper de sal, 75,2 %) · T 27,8 °C | **0,61 °C** sense corregir · 0,40 amb els desplaçaments del 21/09 | Tàper tancat el 21/09 a les 12:09, replà des de les ~05:00. Tots cinc llegeixen **baix** contra la sal (0,4–3,2 punts). **No aplicat**: falta el punt en fred |

> **Incidències de la tanda en marxa** (marcador encès des de les 12:09 del 21/09/2026):
>
> - **15:00–15:20** — **algú mou el tàper** i la tapa deixa entrar aire: l'aigua de l'aire baixa
>   de 18,1 a 16,7 g/m³, i `centre` i `gran` perden 4–5 punts en cinc minuts. En un tàper tancat
>   amb sal l'aigua de l'aire només pot pujar, i la T no salta. **Tram descartat**; com a graó no
>   serveix, perquè no se'n sap l'hora exacta ni si va afectar tots cinc alhora.
> - **18:15** — el **deshumidificador** s'endolla i arrenca. ✅ **En una altra habitació, a
>   posta** per no influir en el calibratge (confirmat per l'usuari), i amb un aire condicionat
>   que també asseca: per això ell llegia 44 % amb els sensors al 66–72 %. **No toca les
>   rampes.**
> - **18:49:41** — **reinici d'HA** per carregar `tuya-local`, decidit amb l'usuari. L'API
>   torna al cap de **9 s**, i als cinc sensors **no hi queda cap `unavailable` gravat** ni
>   cap salt: la rampa humida segueix llisa.
> - **22/09, ~05:00** — **replà** del tàper → [el replà](#el-replà--22092026).
> - **22/09, 12:45:20** — **el tàper entra destapat a la nevera** (tercera tanda). Per
>   col·locar-lo, els sensors s'han hagut de **tocar mínimament**; la T no en mostra rastre. En
>   baixar l'HR de pressa, **el hub informa cada 6–12 s** per sensor: la resolució temporal
>   d'un graó, que era la incògnita, és de segons. L'ordre de reacció: `exterior` 12:45:21,
>   `gran` :22, `centre` :26, `baixa` :30, `fons` :36.
> - **22/09, 13:18** — ✅ **prova de ràdio superada**: en 30 min cap sensor no calla (la T de
>   cadascun arriba com a mínim cada 2,4 min) i no hi ha cap `unavailable`. La nevera no fa de
>   gàbia. L'aire de dins és sec, **~40 %**, i els sensors van per 12–13 °C, encara baixant.
> - **22/09, 13:44:35** — **tàper tapat** dins de la nevera, amb els sensors a ~8 °C. L'HR salta
>   de ~40 a ~55 % en dos minuts: és l'aire de l'habitació que entra en obrir la porta i queda
>   atrapat (el Td passa de −4,8 a −0,5 °C).
> - **22/09, 13:52–14:40** — ⚠️ **l'aigua de l'aire BAIXA dins del tàper tapat** (Td de +0,3 a
>   −1,1 °C; 4,8 → 4,4 g/m³), i entre sensors hi ha **2,1–2,4 °C de diferència** de T, quan a
>   l'habitació quadraven a ±0,05. En un tàper tancat amb sal, amb l'aire al 55–64 %, l'aigua
>   només hauria de pujar. L'explicació més probable: **la pasta és més freda que els
>   sensors**, sobre el prestatge fred, i la sal fixa el 75,7 % **a la seva temperatura**, no a
>   la dels sensors; amb 2–3 °C de diferència, on són ells l'aire marca ~60 %. També hi podria
>   haver una fuita a la tapa o un costat tocant la paret del fons. **Remei**: un drap plegat a
>   sota i un altre al voltant, sense obrir-lo, perquè tot el tàper sigui a la mateixa
>   temperatura.
> - **22/09, 15:50–16:44** — el Td **deixa de baixar i s'atura a ~−2,1 °C** (4,1 g/m³), amb els
>   sensors a 3,1–5,0 °C i encara 1,9–2,0 °C de diferència entre ells. Reforça la pasta freda i no
>   la fuita: una fuita l'hauria fet seguir baixant cap als −4,8 °C de l'aire de la nevera. Aquest
>   Td és el que dona la sal a **~2 °C**, més fred que qualsevol dels cinc. La nevera és **més
>   freda del previst**, 3–5 °C i no 7–8.
> - **22/09, ~16:45** — **el tàper, embolicat amb un drap** (l'hora surt de les dades: un sotrac
>   de +0,2–0,3 °C als cinc alhora, en obrir la nevera). Després, fins a les ~17:20, la T puja
>   0,5 °C —el drap era a temperatura d'habitació— i torna a baixar. A les 18:30 el Td ja
>   **torna a pujar** (−2,1 → −1,9 °C): la sal guanya. La diferència de T entre sensors, però,
>   **segueix en 1,9 °C**. La nit ho dirà: si amb el drap s'esvaeix, era un gradient; **si es
>   manté, és dels sensors en fred**, i és justament el que calia saber (1 °C de T són ~1 °C de
>   Td).
