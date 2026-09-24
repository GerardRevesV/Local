# Calibratge creuat dels sensors — procediment

> **Estat: ✅ calibratge d'humitat fet i desplegat el 23/09/2026 a les 16:48:53 (versió
> `2026-09-23`)** → [els números](#els-números--23092026). Dispersió de Td entre els cinc:
> **0,88 → 0,21 °C** per blocs dins de mostra (**~0,3–0,5 fora de mostra**), vàlid **entre el 51
> i el 73 % d'HR a 26–30 °C**. La temperatura no
> es corregeix. ⏳ **Queda obert el fred**: la [tanda de la nevera](#tercera-tanda--la-nevera) no va
> poder donar l'ancoratge —gradients de 2–3 °C dins del tàper—, o sigui que **no se sap si el
> calibratge depèn de la temperatura**, i es repeteix al soterrani a l'hivern. El mètode és a [com
> s'ajusta la correcció](#com-sajusta-la-correcció-i-on-saplica); les dades crues i l'script que
> en treu cada xifra, [al repositori](#les-dades-crues-al-repositori). Fase **A.13** de
> [fases.md](fases.md).

## Per què, i quant val

La decisió del soterrani és una **resta**: `ΔTd = Td_interior − Td_exterior`. Per tant el que
fa mal **no és l'error absolut** de cada sensor, sinó la **diferència entre dos**. Un error que
tinguin tots cinc per igual s'anul·la sol en la resta.

Tens **models barrejats** —3× T315 i 2× T310—, i entre models l'error sistemàtic no es
cancel·la. *(⚠️ La primera tanda ho va desmentir: **no és una qüestió de model**, cada sensor
té la seva desviació. Vegeu els resultats més avall.)*

El premi és concret: amb la dispersió per sota de **0,3 °C** es pot baixar `delta_td_on` de
**2,0 a ~1,2 °C**, i això són **hores de ventilació gratuïta** cada setmana. *(23/09/2026: dins de
mostra s'hi arriba, 0,21 °C, però fora de mostra és ~0,3–0,5 i la referència interior té un
biaix de +0,1 °C; baixar-lo encara no queda justificat → [els números](#els-números--23092026).)* Amb l'objectiu nou
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

⚠️ **Revisat el 23/09/2026, amb les dades a la mà: això era mig cert.** El raonament del *dither*
es manté —i el replà del 22/09 en va donar un exemple de llibre, amb `fons` clavat a 72,00 set
hores—, **però ajustar minut a minut sobre la rampa és pitjor**, no millor: els pendents surten
de 0,80 a 1,22 segons el sensor. El que funciona és **partir-ho tot en blocs de 20 minuts**, que
aprofita la rampa i els replans alhora → [d'on surten els punts de
l'ajust](#don-surten-els-punts-de-lajust-blocs-no-replans-sols-ni-minut-a-minut).

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

**Ritme:** que l'HR no es mogui més de **2 punts per hora**. Més de pressa i el que mesuraràs
serà la diferència de **temps de resposta** entre sensors, no de calibratge, i l'eina descarta
aquells blocs *(abans deia ~7 %/h; les dades del 21–23/09 van demostrar que era massa: amb ~6 min
de retard entre sensors, 7 punts/h fan 0,7 punts d'error)*.

El **tram 4** és el que respon si el desplaçament és constant. Si un sensor no torna a la
mateixa lectura *relativa als altres* després d'haver passat pel 85 %, aquell sensor té
histèresi i **no admet cap corba**: se li posa una constant i els seus valors alts es prenen
amb pinces.

Si el tram 3 es queda curt, el millor recanvi és el **bany després de dutxes**: arriba al 90 %
sense esforç.

## Després

Amb les dades baixades en un CSV (vegeu [les dades crues](#les-dades-crues-al-repositori)):

```bash
python3 tools/calibratge.py --csv <fitxer>.csv --versio AAAA-MM-DD [--exclou INICI/FI …]
```

o directament de Home Assistant, amb `HA_URL` i `HA_TOKEN_FILE` i `--descarrega --hores 48`.
La finestra la treu sola del marcador **tram per tram** (si s'apaga entremig, allò d'entremig no
compta); per a trams sense marcador, `--finestra INICI/FI`.

> ⚠️ **Corregit el 22/09/2026:** fins llavors l'eina demanava l'històric **sense `end_time`**, i
> Home Assistant en torna només **24 h des de l'inici**, demanis les hores que demanis
> (comprovat amb HA 2026.9.3). Qualsevol calibratge tret amb `--descarrega` abans de la
> correcció s'ha de tornar a calcular.

**El que decideix** —i fa sortir amb codi 1 si falla—:

| Què diu | Què vol dir |
|---|---|
| `Blocs de 20 min: N utilitzables`, i el recorregut | Calen 10 blocs, i **20 punts d'HR de recorregut** per ajustar pendent; si no, només desplaçament. Un pendent sense recorregut és soroll disfressat de ciència |
| `⚠ … pendent …, sensor encallat?` | Un pendent fora d'1 ± 0,10 no és calibratge: és un sensor clavat en un valor |
| Blocs contra minut a minut, **a tots dos extrems** | Dos mètodes independents. Si difereixen més d'1 punt en algun extrem, el número no s'ha de fer servir |
| Dispersió de Td **per blocs**, amb la correcció que es desplega | El criteri: **≤ 0,30 °C** |

**El que només informa:** la dispersió minut a minut (hi pesa el gra de la mesura), el percentil
90 i la dispersió **per franges d'HR** —una mediana global la pot aguantar una sola franja—, la
pujada contra la baixada a una HR comuna, i la **incertesa** de la correcció al 85 i al 90 % per
bootstrap de blocs de 2 h.

L'eina escriu les línies per enganxar a
[`custom_templates/calibratge.jinja`](../../config/custom_templates/calibratge.jinja), que és
**l'únic lloc on viuen els números**: la versió, el diccionari i el rang de validesa. I
`python3 tools/calibratge.py --prova` falla si el que hi ha al fitxer no és exactament el que surt
de les dades del repositori.

⚠️ **Es corregeix només el derivat. La lectura crua no es toca mai**, de manera que l'arxiu
conserva la mesura i la correcció per separat i sempre es pot desfer.

### Desplegar un calibratge

1. `python3 tools/calibratge.py --prova` i `python3 tools/replica.py --prova`, tots dos verds.
2. Al servidor, **primer** `homeassistant.reload_custom_templates` i **després**
   `template.reload` (o reiniciar). Al revés, els punts de rosada es queden sense
   `calibratge.jinja` a la memòria, sense valor, i la decisió passa a `sense_dades`.
3. Comprovar que **existeixen les deu entitats noves** amb el nom exacte —
   `sensor.{soterrani_fons,soterrani_centre,soterrani_gran,baixa,exterior}_humitat_calibrada` i
   `sensor.{soterrani_fons,soterrani_centre,soterrani_gran,planta_baixa,exterior}_punt_de_rosada_cru`;
   si en surt alguna amb `_2` al final, s'ha de renombrar **abans** que gravi res. Ho fa
   `bash scripts/comprova.sh`: mira cada `default_entity_id` dels paquets i cada entitat del
   tauler, i canta les que falten i les còpies `_2`— i que **l'atribut
   `calibratge` sigui la versió** a les deu que fan servir la correcció: les cinc
   `*_humitat_calibrada` i els cinc `*_punt_de_rosada` (els `_cru`, a posta, no el porten).
4. **Apuntar l'hora exacta** al [registre d'instal·lació](home-assistant.md#registre-dinstallació)
   i al [registre d'aquí](#registre): totes les sèries derivades —els punts de rosada, la
   referència, els ΔTd, la HR màxima— fan un salt en aquell instant. Amb el primer calibratge i
   els sensors junts: el Td de `fons` puja **+0,3 a +0,8 °C** i la HR màxima baixa **~1,5 punts**,
   però el ΔTd interior − planta baixa gairebé no es mou (−0,03 °C), perquè abans la referència la
   marcava `centre`, que llegeix alt com la planta baixa. Al local, el salt del ΔTd dependrà de
   quin punt sigui la referència. Cada fila porta la versió a l'atribut `calibratge`, però el salt
   s'ha d'explicar igualment.

## Com s'ajusta la correcció, i on s'aplica

*Escrit el 23/09/2026, amb les dades de les tres tandes a la mà. Aquesta secció mana sobre el
mètode que es descrivia abans de tenir-les.*

### En T i HR, no en punt de rosada

La correcció s'aplica **a les dues magnituds que el sensor mesura** —T i HR— i el punt de rosada
surt de Magnus a partir d'elles ja corregides. **No** es corregeix el Td amb un desplaçament seu,
ni es busquen punts propers en una taula. Tres raons:

1. **L'error viu a la mesura, no al càlcul.** El que està desviat és l'element capacitiu d'HR i,
   si de cas, el termòmetre. Corregint-los, la correcció val a qualsevol temperatura i humitat;
   és física, no un pedaç al resultat.
2. **Un desplaçament de Td no és portable.** Barreja dues coses que es comporten diferent: 1 °C
   d'error de T entra sencer al Td, mentre que 1 punt d'HR hi entra com ~0,2 °C —i aquest factor
   canvia amb la temperatura—. El mateix número no valdria al soterrani a l'hivern.
3. **No tot el que decideix és un Td.** La urgència de la v2 mira la **HR més alta** dels tres
   punts, i els llindars del deshumidificador també són en HR. `rosada.yaml` la calcula com el
   **màxim de les tres humitats calibrades**, que és exacte per a qualsevol calibratge. *(Fins al
   23/09/2026 es desfeia Magnus amb el Td calibrat i la T crua, que només era exacte amb `t` = 0.)*
   Amb la correcció en HR, tot plegat queda consistent; amb un pedaç al Td, el Td aniria calibrat
   i la HR no.

**Per què no una taula de punts propers:** en tindríem **tres** (49–59 % a 26 °C, 73 % a 28 °C i
la nevera), que no fan graella; interpolar-hi seria ajustar soroll. El model lineal en HR
(`c_rh_a·HR + c_rh_b`) ja recull la dependència que s'ha vist —la desviació de `fons` i `centre`
canvia amb la humitat— i l'eina només ajusta el pendent si hi ha **20 punts d'HR de recorregut**,
que ara sí que hi són (51 → 73 % a la referència).

### D'on surten els punts de l'ajust: blocs, no replans sols ni minut a minut

Un replà sencer promitjat dona **un sol punt** per sensor: 441 mostres al mateix 72–73 % no
allarguen el recorregut, només afinen aquell punt. I ni això sempre: al replà del 22/09, `fons` i
`gran` van estar clavats a **72,00** set hores seguides —sense *dither*—, de manera que el seu
valor real és 71,5–72,5 i **promitjar no ho arregla**. Amb dos replans en tens dos punts i una
recta exacta, sense cap manera de saber si és bona.

L'altre extrem, **ajustar minut a minut sobre una rampa**, és pitjor encara. Provat amb la pujada
del 21/09 (575 min, 57 → 71 %), els pendents surten disparats i incoherents entre sensors —de
**0,80 a 1,22**— i la correcció que en resulta s'allunya fins a **5 punts** de la dels replans.
Tres motius: el recorregut és curt (12–17 punts per sensor, per sota dels 20 que demana l'eina),
la variable independent porta l'error de quantització (±0,5), cosa que **esbiaixa el pendent cap
avall**, i el retard hi és encara que sigui petit.

**El punt mig funciona:** partir la finestra marcada en **blocs de 20 minuts**, fer la mitjana de
cada bloc i ajustar sobre els blocs **en sentit invers** —el sensor en funció de la referència, i
després s'inverteix—, que és com s'esquiva el biaix. I **descartar els blocs on l'aire es mou
massa de pressa**, perquè allà el retard entre sensors (~6 min entre el més ràpid i el més lent)
fabrica desviacions que semblen calibratge: l'error és *ritme × retard*, i amb el llindar a
**2 punts d'HR/hora** queda en 0,2 punts com a màxim. El ritme es mira amb el pendent de la
**mitjana dels cinc sobre 60 minuts**, i **només si els dos blocs veïns hi són sencers**: un bloc
al costat d'un tram exclòs té la finestra coixa i pot semblar lent quan no ho és.

> ⚠️ **Revisat el 23/09/2026.** El primer filtre mirava el primer i l'últim minut de la
> *mediana*, que és un enter: el tall real anava de 4 a 6 punts/hora segons on queia el graó, i
> deixava passar el **transitori de després de tancar el tàper** (21/09, 12:40–14:20), amb fins a
> 6 punts de divergència entre sensors. Amb el filtre nou, surt. Una segona revisió va trobar
> que dos blocs més (21/09 14:20 i 23/09 13:00) hi entraven perquè tocaven un tram exclòs i el
> ritme es calculava amb un sol veí: d'aquí la regla dels veïns sencers. Entre tot, i amb la
> finestra acabant a l'última dada (13:33 i no 13:45), la dispersió per blocs passa de 0,27–0,28
> a 0,21 °C. També es va trobar que l'eina no ordenava les files dins de cada bloc: amb el
> filtre i la finestra d'abans, això feia sortir 91 blocs en comptes de 98 (ara en són 84). Els
> números que hi havia en aquesta secció eren d'una exploració amb l'eina d'abans, i s'han tret:
> els bons són a [els números](#els-números--23092026).

La prova de si el número és de fiar és que **dos mètodes independents diguin el mateix**: l'ajust
per blocs i el minut a minut coincideixen dins de **0,37 punts** a l'extrem baix (51 %) i de
**0,18** a l'alt (73 %). *(A l'extrem alt, perquè al mig dues rectes s'assemblen sempre.)*

⚠️ **I la temperatura? A aquestes dades no es pot separar.** El model corregeix segons l'HR i
prou. Per saber si l'error també depèn de la T caldria tenir la mateixa HR a temperatures ben
diferents, i no hi és: cada franja d'HR cau dins d'un interval de **0,2–0,5 °C** (només la del
70–75 % arriba a 2,4), i a més **l'HR i la T van de bracet** en tot l'experiment —del 51 al 73 %
d'HR, la T puja 1,8 °C—, de manera que qualsevol efecte de la temperatura queda absorbit pel
pendent d'HR. Mirant els residus contra la T, només `fons` insinua alguna cosa (−0,35 punts/°C,
R² 0,28); els altres quatre, entre −0,02 i +0,14. I el de `fons` té una explicació més avorrida:
**estava clavat a 72,00** set hores mentre la referència es movia, i això sol ja fabrica un residu
que sembla dependre de la temperatura.

Amb un recorregut de només **26,4–29,6 °C**, extrapolar-ho als 12 °C del soterrani seria inventar
(el pendent de `fons` hi donaria uns +6 punts). Per això la dependència de la temperatura **no
s'ajusta**: es mesura amb un segon replà de sal en fred i isoterm, que és el que la tercera tanda
havia de ser i el que caldrà repetir al soterrani a l'hivern.

### ⚠️ Una rampa de temperatura també ha de ser lenta

La temptació, quan es veu el tàper passar de 10 a 23 °C en tres quarts d'hora, és aprofitar-ho
com a escombratge de temperatures intermèdies. **No serveix.** Mesurat el 23/09/2026, amb el
tàper fora de la nevera i tancat:

| Ritme | Diferència de T entre els cinc | Desviació de `centre` |
|---|---|---|
| −0,06 °C/min | 3,4 °C *(encara a la nevera: gradient)* | −2,6 |
| +0,46 °C/min | 3,7 °C | −1,5 |
| +0,36 °C/min | 2,8 °C | 0,0 |
| +0,24 °C/min | 1,6 °C | 0,0 |

**La desviació de cada sensor canvia amb el ritme i s'encongeix quan la rampa s'alenteix**: és
**retard tèrmic**, no calibratge. D'aquests números en surt que entre el sensor més ràpid i el més
lent hi ha uns **6 minuts** d'inèrcia, i que perquè això doni menys de 0,1 °C d'error la rampa ha
d'anar per sota de **~1 °C/hora** (6 min × 1 °C/h = 0,1 °C). La d'aquell dia anava a 14–28 °C/h:
entre 14 i 28 vegades massa de pressa. Els graons serveixen per veure **qui reacciona i quan**;
per calibrar, calen derives lentes —una nit— o el soterrani mateix.

*(De passada, valida la lectura de la segona ronda de nevera: allà el ritme era de 0,06 °C/min,
o sigui que el retard només podia explicar ~0,36 °C dels 3,4 de diferència. La resta era el lloc.)*

### Si el punt fred serveix: dos ancoratges i interpolació, no «el més proper»

Amb un replà calent (~28 °C) i un de fred (~5 °C) es pot fer que la correcció **depengui de la
temperatura**, que és el que demana el soterrani. La forma proposada:

- **El pendent en HR, del calent.** En fred l'HR només recorre el 66–74 %: no hi ha palanca per
  ajustar-hi cap pendent, i el que s'hi mesura és el **desplaçament**.
- **El desplaçament, interpolat linealment entre els dos ancoratges** segons la T del moment, i
  **retallat** fora del tram 5–28 °C. El soterrani viurà entre 8 i 20 °C, o sigui **dins**: es
  fa interpolació i no extrapolació, que és tota la diferència.

⚠️ **Interpolar, no triar el punt més proper.** Agafar «la calibració mesurada a la temperatura
més propera» introdueix un **graó** just al mig del rang: creuant els 16 °C, la correcció
saltaria de cop, el Td amb ella, i la decisió de ventilar podria canviar sense que hagués canviat
res al soterrani. Un control amb histèresi no s'ha de barrejar amb una taula que fa salts.

**El criteri per decidir si s'implementa**, un cop la prova d'intercanvi doni l'ancoratge fred:
si els desplaçaments en fred s'assemblen als de calent **dins del gra (±0,3 punts)**, no cal tocar
res i es documenta que s'ha comprovat; si difereixen més, s'implementa la interpolació a les cinc
plantilles de `rosada.yaml` i **també a `tools/replica.py`**, que ha de seguir dient el mateix.

**L'intercanvi, però, no fabricarà l'ancoratge fred.** La idea era posar-los en fila i invertir-la:
amb les posicions *p* i *6−p* i un gradient lineal, la mitjana de les dues rondes és la mateixa
per a tots cinc —(g₁+g₅)/2 = (g₂+g₄)/2 = g₃— i la posició s'anul·la, com pesar dues vegades amb
els plats de la balança canviats. ⚠️ **Al tàper real no hi caben en fila**: hi van com poden, i
sense posicions conegudes la cancel·lació no està garantida —un sensor es podria quedar les dues
vegades al racó fred i el seu error sortiria doblat, disfressat de calibratge—. **Decidit el
23/09 amb l'usuari: no es fa servir cap número basat en la posició.**

La segona ronda de nevera es fa igualment, **1,5 h i amb els cinc col·locats de manera ben
diferent**, però com a **verificació qualitativa**:

- Si les desviacions entre sensors **canvien** en canviar la col·locació → són del lloc, no dels
  sensors. L'ancoratge fred **no és aprofitable**, no s'implementa cap interpolació en T, i la
  dependència de la temperatura queda per al soterrani a l'hivern.
- Si **es mantenen** → apunta a error propi de cada sensor en fred, i llavors sí que val la pena
  muntar-ho bé (un recipient petit, isoterm, o un bany d'aigua freda) abans de tocar `c_t`.
  ⚠️ Amb un matís: la col·locació nova ha de ser **realment diferent**; si per casualitat deixa
  els mateixos sensors a la mateixa zona freda, el patró es mantindria sense voler dir res.

✅ **Resposta de la prova d'intercanvi (23/09):** tres col·locacions, tres patrons diferents; la
desviació de T dins de la nevera **és del lloc**, no dels sensors → [les
incidències](#registre). No s'implementa cap interpolació en temperatura.

**I en acabat**, el marcador `input_boolean.mode_calibratge` **es queda encès** durant el
trasllat —mentre és encès, res no actua— i **s'apaga just abans d'`inicia-serie.sh`**, al local,
amb els sensors ja al seu lloc. Si s'oblida, la sèrie de debò començaria amb la decisió dient
`calibratge`, i per això `inicia-serie.sh` **s'hi nega**; amb `--apaga-marcador` l'apaga ell
just abans d'aturar HA, perquè el canvi quedi a la base arxivada.

## ⚠️ Això no serà un calibratge d'hivern

Es fa a casa al setembre, a 26–30 °C. El soterrani al gener serà de 8 a 15 °C, i l'error dels
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
**~0,95 °C de Td** (a 26,5 °C i 55 %, 1 punt en són 0,28): el triple del pressupost d'error.

| Dispersió de Td entre els cinc | |
|---|---|
| Sense corregir | **0,95 °C** |
| Amb només desplaçament | **~0,25 °C** ✅ dins de l'objectiu de 0,30 |
| Amb pendent i desplaçament | ~0,25 °C — **el pendent no afegeix res**, i fora del rang inventa |

### Tres coses que no s'esperaven

**1. No és una qüestió de model.** El pla suposava que l'error vindria del T310 contra el
T315. No: els dos T310 quadren entre ells, i entre els T315 hi ha el que llegeix més baix de
tots (`fons`) i dos dels que llegeixen més alt. **Cada sensor és el seu cas.**

**2. El màxim amplifica l'error.** La referència interior és el **punt de rosada més alt** dels
tres del soterrani. Sense corregir, **`centre` la marca el 99 % del temps** —no perquè sigui el
punt més humit, sinó perquè és el que llegeix més alt—, i això infla el Td de referència
**+0,18 °C**. Un màxim sempre tria el sensor amb el biaix més positiu. Quan estiguin repartits
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
| **El desplaçament** | rampa **lenta** | L'error que hi afegeix el retard és *ritme × retard*. A 2 punts/h amb ~6 minuts de retard són 0,2 punts; a 7 punts/h, 0,7. Una dutxa (~35 punts en 10 minuts) en donaria ~17, que taparien del tot els 1–2 punts que es busquen |
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
nit. L'habitació es va escalfar fins a 29,6 °C (a les 21:00), i com més calent és l'aire, més aigua
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
de **0,61 a 0,40 °C** (sobre les mitjanes de la finestra; minut a minut, de 0,67 a 0,43): millora, però queda per sobre dels 0,30. `baixa` i `exterior` no es mouen,
però `fons` passa de +2,2 a +0,8 i `centre`, de −1,1 a −2,0: en aquests dos **la desviació depèn
de l'HR**, amb canvis més grans que el gra d'un replà (±0,5). Va ser bona decisió no aplicar-los.
I la referència ja va del 49 al 73 %, 24 punts: per sobre dels 20 que l'eina demana per ajustar
un pendent.

**3. Tots cinc llegeixen baix contra la sal**, de 0,4 a 3,2 punts; la mediana, uns **2,4**. És
el que el consens no podia veure mai. A la resta ΔTd no li fa res, perquè s'anul·la; sí que pesa
en tot el que és **absolut**: el marge contra la paret (≈0,5 °C de Td) i els llindars d'HR del
deshumidificador.

⚠️ **Amb dues condicions.** Que la tapa tanqui del tot: una fuita petita deixa el replà per sota
del 75,3 % i es confondria amb uns sensors que llegeixen baix, i el sotrac de les 15:00 (vegeu
les [incidències](#registre)) demostra que, si es mou, la tapa deixa entrar aire. I que **la
pasta sigui a la mateixa temperatura que els sensors**: la sal fixa el 75,3 % a la seva
temperatura, i a 28 °C cada grau de diferència són ~4,4 punts d'HR. Els 2,4 punts de la mediana
equivalen a una pasta **només 0,5 °C més freda** que els sensors —la taula, per exemple—, i
ningú no ho va mesurar. *(Es va veure a la nevera, el 22/09, on la diferència era de graus.)*
L'ancoratge absolut, doncs, és **provisional**; les correccions **entre sensors** no en depenen.

**Dispersió de Td al replà, sense corregir: 0,61 °C** sobre les mitjanes de la finestra (0,67 minut a minut; la nit del 21/09 al 55 %, 0,95 minut a minut).

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
7. **El marcador, encès** fins al local: s'apaga just abans d'`inicia-serie.sh` → [com es
   desplega](#desplegar-un-calibratge) i [el mètode](#com-sajusta-la-correcció-i-on-saplica).

### Com es llegeix

Les tres tandes van donar això:

| Tanda | HR | T | Què en surt |
|---|---|---|---|
| La nit del 20–21/09 | referència 51–57 % | 26,4–26,9 °C | 24 blocs per a l'ajust |
| El tàper, 21–22/09 | referència 65 → 73 % (sal: 75,2) | 27,2–29,6 °C | 60 blocs més (38 de la pujada i 22 del replà), i l'ancoratge absolut *(provisional)* |
| La nevera, 22–23/09 | 62–74 % | 3,1–8,4 °C | **Res per a l'ajust**: gradients de 2–3 °C dins del tàper, i la desviació de T segueix el lloc. Després, a l'habitació, cap bloc: el primer no tenia el veí sencer |

El mètode és a [com s'ajusta la correcció](#com-sajusta-la-correcció-i-on-saplica), i els números
que en surten, a sota.

## Els números — 23/09/2026

Ajustats amb `tools/calibratge.py` sobre **84 blocs de 20 minuts** (24 de la nit del 21/09, 38 de
la pujada del tàper i 22 del replà), versió **`2026-09-23`**, i escrits a
[`custom_templates/calibratge.jinja`](../../config/custom_templates/calibratge.jinja).
`HR_corregida = a · HR + b`; la T no es corregeix. **Desplegats el 23/09/2026 a les 16:48:53**
→ [com es desplega](#desplegar-un-calibratge). Totes les xifres d'aquesta secció les treu
[`dades/calibratge-2026-09-analisi.py`](dades/calibratge-2026-09-analisi.py), que imprimeix
l'informe de l'eina i el que l'eina no calcula.

| Sensor | `a` | `b` | Correcció al 55 % | al 73 % | al 85 %* | al 90 %* |
|---|---|---|---|---|---|---|
| `soterrani_fons` | 0,9473 | +5,12 | +2,22 | +1,27 | +0,64 | +0,38 |
| `soterrani_centre` | 0,9516 | +1,45 | −1,21 | −2,08 | −2,66 | −2,91 |
| `soterrani_gran` | 1,0344 | −1,72 | +0,17 | +0,79 | +1,20 | +1,38 |
| `baixa` | 0,9992 | −1,21 | −1,25 | −1,27 | −1,28 | −1,28 |
| `exterior` | 0,9989 | +0,08 | +0,02 | −0,00 | −0,01 | −0,02 |

\* *Extrapolat: el rang mesurat acaba al 73 %.*

| Criteri | Resultat |
|---|---|
| Dispersió de Td, **per blocs**, amb el que es desplega | **0,88 → 0,21 °C** ✅ per sota de l'objectiu de 0,30 |
| Per franges d'HR | 45–60 %: 0,99 → **0,22** (24 blocs) · 60–70 %: 1,43 → **0,54** (8) · 70–80 %: 0,73 → **0,20** (52) |
| Percentil 90, per blocs | 1,24 → 0,43 °C |
| Dispersió de Td, minut a minut | 0,88 → 0,26 °C |
| Blocs contra minut a minut | Coincideixen dins de **0,37 punts** al 51 % i de **0,18** al 73 % ✅ |
| **Histèresi** (nit del 21/09, 54,7 %, contra 23/09 13:00–13:33, 53,8 %) | Cap sensor no es mou més de **0,49 punts** després d'haver passat pel 75 % i per 3 °C ✅ Cap sensor necessita constant |
| `t` | **0,00 per als cinc**: coincideixen en T dins de ±0,05 °C, que és el gra |

**El que aquests números NO diuen**, i s'ha de saber abans de fer-los servir per decidir:

- **Són dins de mostra.** Ajustant sense un tram i provant sobre aquell tram, la dispersió puja:
  **0,52 °C** a la nit (0,22 dins de mostra; i sense la nit, no hi ha prou recorregut per ajustar
  cap pendent), 0,30 a la pujada i 0,30 al replà. El 0,21 és el millor cas; la xifra honesta
  per a condicions noves és **~0,3–0,5 °C**. ✅ **I es va comprovar amb dades noves:** de 13:40 a
  16:00 del 23/09, amb els cinc junts a l'habitació i després d'exportar el CSV —o sigui, dades
  que l'ajust no ha vist mai—, la dispersió per blocs passa de **1,01 a 0,36 °C** (mediana de 7
  blocs, HR 48–54 %, al límit baix del rang). *(Una lectura sola no serveix per a això: amb l'HR
  en enters, un instant concret pot donar tant 0,29 com 0,57 per pura sort.)* ✅ **I un cop
  desplegat, amb el que grava HA:** de 13:00 a 18:16 del 23/09, amb els cinc junts
  (13:00–13:33 encara era dins de l'ajust), la separació entre els cinc —mediana, cada 2 min—
  passa de **1,02 a 0,37 °C** de Td (fins a les 16:50) i de **3,0 a 1,3 punts** d'HR. Abans de
  les 16:48 el calibrat és calculat amb els números desplegats; des de llavors, les **220
  lectures de `*_humitat_calibrada` que ha gravat HA són idèntiques al càlcul**. Amb l'HR en
  enters, cinc sensors no poden quedar més a prop de **~0,7 punts** d'HR, pel mateix gra que
  posa el terra del Td a ~0,17 °C.
- **Dins de mostra, gairebé tot el que queda és el gra.** Amb un model perfecte i l'HR en enters,
  la dispersió mínima és de ~0,17 °C, per blocs i minut a minut: en un replà, un sensor clavat en
  un enter arrossega el mateix error tot el bloc, i promitjar no ho treu. Per sobre d'això, la
  recta només deixa ~0,04 °C.
- **La franja del 60–70 % és la pitjor** (0,54) i és precisament la del soterrani a la tardor.
  Només hi ha 8 blocs: la pujada del tàper hi va passar de pressa.
- **El recorregut és just**: 22 punts, amb un mínim de 20. En una de cada quatre rèpliques del
  bootstrap baixa de 20, o sigui que **el pendent depèn de pocs blocs dels extrems**.
- **Fora del rang, la incertesa creix.** 1σ per bootstrap de blocs de 2 h, sempre amb pendent:

  | | `fons` | `centre` | `gran` | `baixa` | `exterior` |
  |---|---|---|---|---|---|
  | 1σ al 85 % | ±0,40 | ±0,22 | ±0,16 | ±0,17 | ±0,02 |
  | 1σ al 90 % | ±0,49 | ±0,28 | ±0,20 | ±0,21 | ±0,02 |
  | Traient un tram, al 85 % | −0,05 … +1,49 | −2,90 … −2,16 | +0,68 … +1,33 | −1,42 … −1,13 | −0,02 … 0,00 |

  O sigui: per a `fons` el **risc de model** —quin tram mana el pendent— és de **~1,5 punts**, i
  per a `centre` de ~0,7, més que la incertesa estadística. 1 punt d'HR a 12 °C i 85 % són
  ~0,17 °C de Td.
- **La referència interior és un màxim, i un màxim puja amb el soroll.** Amb els cinc al mateix
  aire, el màxim dels tres del soterrani queda **+0,09 °C** per sobre de la seva mitjana, i el ΔTd
  interior − planta baixa, que hauria de ser 0, surt **+0,10 °C** de mitjana (p95 +0,23). És un
  biaix que sempre empeny cap a ventilar, i s'ha de tenir en compte si es baixa `delta_td_on`.
- **La temperatura queda fora.** Rang de validesa: **51–73 % d'HR i 26,4–29,6 °C**
  (`RANG_HR` i `RANG_T` al fitxer). El soterrani serà de 65–90 % i 8–20 °C, i no s'ha pogut
  mesurar si la correcció depèn de la T ([tercera tanda](#tercera-tanda--la-nevera)). Es
  repeteix al soterrani a l'hivern.
- **La histèresi no es va mirar en equilibri tèrmic.** El 23/09 els sensors encara s'escalfaven
  (`exterior`, +0,16 a +0,22 °C sobre la mediana), i el resultat depèn de quan comença la
  finestra (0,43–0,49 punts). Diu que no hi ha res gros; no diu que no hi hagi res.

### Les dades crues, al repositori

[`dades/calibratge-2026-09.csv`](dades/calibratge-2026-09.csv) — 3.486 punts de les onze entitats
(les deu dels sensors i el marcador), tal com els va gravar Home Assistant: `marca_temps`
(UTC), `entity_id`, `estat`. **Hi són perquè no es poden repetir**: són l'única mesura de la
desviació entre els cinc amb tots junts, i la base de dades d'HA purga i a més ha de viatjar al
local.

**Com es van treure** (23/09/2026, al servidor): `GET /api/history/period/2026-09-20T22:30:00+00:00`
amb `end_time` = el moment de la consulta (~11:45Z del 23/09), `filter_entity_id` = les onze i
`minimal_response`, escrit fila a fila amb el mateix format que `desa_csv`. HA només grava quan
el valor canvia: les últimes files són de les 11:33:45Z (13:33 local), i per això la finestra de
l'ajust acaba a les 13:33. Hi ha tres `unavailable` per entitat, tots de reinicis d'HA de menys de
23 s, i el valor d'abans i el de després són iguals.

L'ajust es refà sense HA:

```bash
python3 tools/calibratge.py --csv docs/domotica/dades/calibratge-2026-09.csv \
  --finestra 2026-09-21T00:43+02:00/2026-09-23T13:33+02:00 \
  --exclou   2026-09-21T11:26+02:00/2026-09-21T12:39+02:00 \
  --exclou   2026-09-21T14:50+02:00/2026-09-21T15:35+02:00 \
  --exclou   2026-09-22T12:45+02:00/2026-09-23T13:00+02:00 \
  --versio   2026-09-23
python3 docs/domotica/dades/calibratge-2026-09-analisi.py   # totes les xifres d'aquest doc
```

`--finestra` hi és per dues raons: la primera tanda es va fer **sense encendre el marcador**, i
el marcador **no es va apagar** abans d'exportar, de manera que la finestra que en surt aniria de
les 12:09 del 21/09 fins al final, nevera inclosa. Els tres `--exclou` són, per ordre: l'estona
entre tandes amb els sensors a la mà, el sotrac de les 15:00, i **tot el tram de la nevera**, que
té gradients de 2–3 °C i no serveix per ajustar. `tools/calibratge.py --prova` fa exactament
aquesta anàlisi i falla si `calibratge.jinja` no en surt.

## Registre

| Data | Rang assolit | Dispersió abans → després | Notes |
|---|---|---|---|
| 21/09/2026 | HR 49–59 % · T 25,9–27,0 °C | **0,95 → ~0,25 °C** (només desplaçament) | ~11 h a casa, marcador sense encendre. Temperatura sense correcció. **No aplicat**: falta la franja humida |
| 22/09/2026 | HR 73 % (replà del tàper de sal, 75,2 %) · T 27,8 °C | **0,61 °C** sense corregir · 0,40 amb els desplaçaments del 21/09 | Tàper tancat el 21/09 a les 12:09, replà des de les ~05:00. Tots cinc llegeixen **baix** contra la sal (0,4–3,2 punts). **No aplicat**: falta el punt en fred |
| 22–23/09/2026 | HR 62–74 % · T 3,1–8,4 °C (nevera) | — | Tres col·locacions, tres patrons: la desviació de T és **del lloc**. Gradients de 2–3 °C dins del tàper: **no aprofitable** per calibrar |
| **23/09/2026** | **HR 51–73 % · T 26,4–29,6 °C** (84 blocs de 20 min) | **0,88 → 0,21 °C** per blocs (0,88 → 0,26 minut a minut; fora de mostra ~0,3–0,5) | ✅ **Versió `2026-09-23`**, a `calibratge.jinja`: pendent i desplaçament d'HR, `t` = 0. Histèresi comprovada (≤ 0,49 punts). ✅ **Desplegat a les 16:48:53** → [registre d'instal·lació](home-assistant.md#registre-dinstallació) |

> **Incidències de la tanda en marxa** (marcador encès des de les 12:09 del 21/09/2026):
>
> - **15:00–15:20** — **algú mou el tàper** i la tapa deixa entrar aire: l'aigua de l'aire baixa
>   de 18,0 a 16,3–16,6 g/m³, i tots cinc cauen alhora, dins de 20 s (15:12:54–15:13:14);
>   `exterior`, el que més, de 61 a 53 %. En un tàper tancat amb sal l'aigua de l'aire només pot
>   pujar, i la T no salta. **Tram descartat**: és un graó que ningú no va provocar a posta.
> - **18:15** — el **deshumidificador** s'endolla i arrenca. ✅ **En una altra habitació, a
>   posta** per no influir en el calibratge (confirmat per l'usuari), i amb un aire condicionat
>   que també asseca: per això ell llegia 44 % amb els sensors al 66–71 %. **No toca les
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
>   cadascun arriba com a mínim cada 1,5 min) i no hi ha cap `unavailable`. La nevera no fa de
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
>   sensors a 3,1–5,5 °C i encara 1,8–2,1 °C de diferència entre ells. Reforça la pasta freda i no
>   la fuita: una fuita l'hauria fet seguir baixant cap als −4,8 °C de l'aire de la nevera. Aquest
>   Td és el que dona la sal a **~2 °C**, més fred que qualsevol dels cinc. La nevera és **més
>   freda del previst**, 3–5 °C i no 7–8.
> - **22/09, ~16:45** — sotrac petit (+0,2–0,3 °C als cinc alhora): la nevera oberta un moment.
> - **22/09, 18:33** — **el tàper, embolicat amb un drap.** En 20 min la T puja **3 °C** (de
>   3,1–5,1 a 6,4–7,8) i el Td, de −1,8 fins a **+1,3 °C** (18:50–18:56): el drap era a temperatura d'habitació i
>   escalfa el que embolica. Des de les 18:56 tot torna a baixar.
>   ⚠️ **Primer es va llegir malament**: el sotrac de les 16:45 es va prendre pel drap. El va
>   desmentir el mateix usuari, i la mida del salt ho confirma: un drap calent no fa 0,3 °C, en
>   fa 3.
>   🟡 **I dona mitja resposta**: en tornar-lo a col·locar, **l'ordre dels cinc canvia** (abans
>   `fons` > `centre` > `gran` ≈ `baixa` > `exterior`; després `fons` > `baixa` > `exterior` >
>   `centre` > `gran`). Un error propi de cada sensor no canviaria d'ordre, de manera que hi ha
>   **com a mínim un component de posició** en els 2 °C.
>   ⚠️ **Però no prova que els sensors mesurin igual en fred**, i la primera redacció ho deia —
>   malament. Dins del tàper els sensors **no es van intercanviar**; només va canviar l'entorn.
>   Que a 28 °C quadrin a ±0,05 no garanteix que a 5 °C ho facin: podria haver-hi les dues coses
>   alhora, gradient i error propi. **Per separar-ho cal intercanviar-los de lloc i repetir**: el
>   que segueixi la posició és gradient; el que segueixi el sensor és calibratge.
> - **23/09, 10:15–11:35 — segona ronda de nevera, amb els cinc col·locats diferent.** ✅ **La
>   desviació de T no és dels sensors: és del lloc.** Tres col·locacions, tres patrons diferents
>   (desviació respecte de la mediana, en °C):
>
>   | Col·locació | `fons` | `centre` | `gran` | `baixa` | `exterior` |
>   |---|---|---|---|---|---|
>   | 22/09, 14:00–18:30, sense drap | +1,2 | +0,7 | 0,0 | −0,1 | −0,9 |
>   | 22/09 21:00 – 23/09 08:00, amb drap | +0,4 | −0,8 | −0,8 | +0,4 | 0,0 |
>   | 23/09, 10:45–11:35, col·locació nova | +0,2 | **−2,3** | **+1,2** | 0,0 | −1,7 |
>
>   `centre` passa de +0,7 a −2,3 i `gran` de 0,0 a +1,2 **sense que els sensors hagin canviat**:
>   un error propi no es reordena així. Queda, doncs, que el que a 28 °C quadra a ±0,05 °C **no
>   s'ha pogut mesurar en fred**, perquè el banc de proves (un tàper dins d'una nevera) té
>   gradients de 3 °C que tapen qualsevol error de dècimes. ⚠️ Això **acota** l'error propi, no el
>   descarta: el que hi pogués haver quedaria per sota del gradient. **Conseqüència: no s'implementa
>   cap interpolació en temperatura**, i la pregunta va al soterrani a l'hivern.
>   *(De passada, un exemple de llibre de la no-uniformitat: `baixa` es va quedar al 60 % d'HR
>   mentre `fons`, `centre` i `gran` baixaven al 34–39 % (`exterior`, al 55–58) —contra `fons`, que era a la mateixa temperatura, ~8 °C de Td de diferència—,
>   perquè havia quedat arran de la pasta de sal.)*
> - **22/09 21:00 – 23/09 08:00, la nit a la nevera** — ⚠️ **el drap no va fer el tàper
>   isoterm**: entre sensors hi queden **0,6–1,9 °C**, i la nevera hi va afegir un cicle propi
>   (3,8 → 8,4 °C a les 02:00 i tornada avall). La conseqüència és que **el Td tampoc no és
>   igual a tot arreu**: amb una pasta que evapora en un punt i parets fredes que condensen en un
>   altre, el vapor viatja de les zones calentes a les fredes, i la dispersió de Td **segueix el
>   gradient** (~0,6–0,8 °C quan la diferència de T era de 0,8 °C; ~1,1–1,2 quan era d'1,5–1,8).
>   Per això l'HR es va quedar al 62–74 % sense arribar mai al 75,7 %, i **l'ancoratge absolut en fred no es pot fer servir**.
>   ✅ El que sí que se'n treu: **comparant parelles que són a la MATEIXA temperatura** —i que,
>   per tant, veuen el mateix vapor— la desviació entre elles surt **igual que en calent dins de
>   0,25 °C** (`fons`–`baixa`: 0,45 calent / 0,65 fred · `centre`–`gran`: 0,58 / 0,35). 🟡 Semblava
>   dir que **entre 5 i 28 °C el calibratge relatiu no canvia gaire**; ⚠️ **superat**: la segona
>   ronda de nevera (23/09) va mostrar que dins del tàper la T segueix el lloc, i la conclusió
>   final és que **no se sap** si el calibratge depèn de la temperatura.
>   ⚠️ **Amb una hipòtesi a sobre**: que les parelles «a la mateixa temperatura» hi siguin de
>   debò. Si en fred cada sensor mesurés la T amb un error propi, dos que **marquen** 5,6 °C no
>   hi serien, no veurien el mateix vapor, i el raonament cau. *(L'intercanvi de posicions del
>   23/09 va dir que la T segueix el lloc, cosa que ho fa més creïble, però no ho demostra.)*
>
> - **23/09, 20:15–22:05 — el trasllat al local.** El hub es desendolla a les 20:15 i els cinc
>   queden `unavailable` fins a les 21:37, quan Matter torna per la Wi-Fi. ⚠️ **Pel camí, `baixa`
>   es va poder mullar una mica** (segons l'usuari). En tornar, amb els cinc junts, marca **~6
>   punts d'HR per sobre** dels altres quatre —69 % cru a les 21:37 i 65 % a les 22:02, amb els
>   altres a 56–60 %— i baixa més de pressa que ells, amb la T pujant de 22,8 a 23,0 °C: el que
>   fa un sensor capacitiu que s'asseca. Els altres quatre, calibrats, coincideixen dins d'**1,2
>   punts** (22:02), però amb el deshumidificador assecant la sala a ~5 punts/h, més de pressa
>   que el filtre de ritme de l'eina. **Res d'aquest tram no serveix per calibrar**, per decisió
>   de l'usuari. ⏳ Queda comprovar que `baixa` **torna a coincidir** amb els altres quan sigui
>   sec: si no hi torna, el mullat li ha deixat un desplaçament i el seu calibratge ja no val.
>   **L'historial diu que és el camí, no el calibratge** (revisat el 24/09 a les 03:00, amb l'HR
>   calibrada cada 2 min des del 21/09 i els números desplegats): en **totes** les fases estables
>   amb els cinc a la mateixa T, `baixa` va a **±0,5 punts** de la mediana dels altres quatre —la
>   nit a casa (−0,4 a +0,2), el replà del tàper de sal (−0,2 a +0,5) i el 23/09 de 12:00 a 20:00,
>   dades que l'ajust no va veure mai (−0,5 a +0,3)—. Només se'n separa a les rampes ràpides i a
>   la nevera, on cada sensor tenia una T diferent: allà, en punt de rosada, queda dins de 0,6 °C.
>   Després del trasllat, amb la mateixa T que els altres: **+6,6 → +5,2 → +4,7 → +4,2 punts** de
>   mediana per blocs de 2 h (21:37–03:00), o sigui **s'asseca a ~0,25 punts/h**.
