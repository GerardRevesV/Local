# Calibratge creuat dels sensors — procediment

> **Estat: preparat, sense executar.** Les peces hi són i els desplaçaments són
> `(0, 1, 0)` —identitat—, de manera que avui no corregeixen res. Fase **A.13** de
> [fases.md](fases.md).

## Per què, i quant val

La decisió del soterrani és una **resta**: `ΔTd = Td_interior − Td_exterior`. Per tant el que
fa mal **no és l'error absolut** de cada sensor, sinó la **diferència entre dos**. Un error que
tinguin tots cinc per igual s'anul·la sol en la resta.

Tens **models barrejats** —3× T315 i 2× T310—, i entre models l'error sistemàtic no es
cancel·la.

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

## Registre

| Data | Rang assolit | Dispersió abans → després | Notes |
|---|---|---|---|
| *(pendent)* | | | |
