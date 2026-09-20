# Control per punt de rosada — proposta

> **Estat: proposta, no decidida.**

## A) La lògica

### Per què punt de rosada i no humitat relativa

L'HR és una **raó**, no una quantitat: diu quant vapor hi ha respecte al màxim que l'aire pot
contenir **a aquella temperatura**. Com que la pressió de saturació es duplica
aproximadament cada 11 °C, comparar l'HR de dos aires a temperatures diferents no té sentit
físic.

Cas típic de Barcelona a l'agost:

| | T | HR | Punt de rosada | Vapor (g/kg) |
|---|---|---|---|---|
| Soterrani | 20 °C | 75 % | **15,4 °C** | ~11,0 |
| Exterior | 30 °C | 65 % | **22,6 °C** | ~17,4 |

L'exterior *sembla* més sec (65 % < 75 %) i en realitat porta **un 60 % més d'aigua**. Si
ventiles, aquell aire entra, es refreda fins a 20 °C, la seva HR puja a ~90 %, i qualsevol
paret per sota de 22,6 °C —totes, en un soterrani— **condensa**. És l'error clàssic que
empitjora els soterranis a l'estiu.

**Per què el punt de rosada i no la humitat absoluta:** els g/m³ **no** són conservatius
(depenen de la densitat de l'aire, o sigui de T). El punt de rosada sí que ho és, té unitats
de °C i es compara directament amb temperatures de superfície.

> **Avantatge col·lateral important:** com que Td és invariant a l'escalfament, un sensor
> exterior que agafi una mica de sol i llegeixi T massa alta **segueix donant un Td
> aproximadament correcte**, perquè llegirà l'HR proporcionalment més baixa. El criteri és
> robust a l'error d'instal·lació més freqüent. *(No et salva si el sensor es mulla.)*

### Fórmula

Coeficients d'**Alduchov & Eskridge (1996)**:

```
a = 17,625    b = 243,04 °C

γ(T, HR) = ln(HR/100) + (a · T) / (b + T)
Td       = (b · γ) / (a − γ)
```

T en °C, HR en %. Error de la fórmula: **±0,1 °C** — irrellevant. *(Evita la variant antiga
a = 17,27 / b = 237,7: té ~3× més error.)*

### D'on ve l'error de debò: els sensors

Sensibilitat al punt de treball 20 °C / 70 % HR:

| Font d'error | Sensibilitat | Amb sensor típic |
|---|---|---|
| Error d'HR | **0,22 °C de Td per cada 1 % HR** | ±3 % → ±0,66 °C |
| Error de T | **0,96 °C de Td per cada 1 °C** | ±0,3 °C → ±0,29 °C |
| Un sensor, combinat | | **≈ ±0,72 °C** |
| **ΔTd amb dos sensors** | ×√2 | **≈ ±1,0 °C** |

**Conclusió operativa:** qualsevol llindar de decisió **per sota de 2 °C està dins del
soroll** i farà repicar el relé per motius purament instrumentals. Això fixa la histèresi, i
no és un número inventat.

Dues coses que es fan de franc i milloren molt el rendiment:

1. **Compra tots els sensors del mateix model i del mateix lot** (interiors i exterior).
   L'error sistemàtic es cancel·la parcialment a la **resta**, que és justament la magnitud
   que decideix.
2. **Abans d'instal·lar-los, deixa'ls 24 h junts en una mateixa habitació**, registra la
   desviació de cadascun respecte de la mediana i aplica aquest *offset* fix a Home
   Assistant. Passes de ±3 % absolut a ±0,5 % relatiu i pots baixar el llindar a ~1,2 °C,
   guanyant hores de ventilació útil. **Cost: zero.**

### Condició de ventilació amb histèresi

```
ARRENCAR si:  Td_int − Td_ext  ≥  Δ_ON     (per defecte 2,0 °C)
ATURAR   si:  Td_int − Td_ext  ≤  Δ_OFF    (per defecte 0,8 °C)
```

Amb **Δ_OFF < Δ_ON sempre** — validar-ho al codi, o algú ho posarà al revés amb el lliscador.
Banda morta de 1,2 °C, coherent amb la incertesa calculada.

I un **objectiu**, perquè ventilar per sota del que necessites és malgastar energia i, a
l'hivern, calor:

```
Td_objectiu = Magnus(T_int, HR_objectiu)     (HR_objectiu ≈ 55 %)
ATURAR també si:  Td_int ≤ Td_objectiu
```

### L'objectiu correcte no és l'HR de l'aire

El fong creix quan l'HR **a la superfície** supera ~80 % sostingut, cosa que equival a una
temperatura superficial uns **2,5–3 °C per sobre del punt de rosada de l'aire**. El criteri
que de veritat importa és:

```
Marge = T_superfície_paret_freda − Td_int    →    mantenir ≥ 3 °C
```

Això demana un **DS18B20 enganxat a la paret més freda i tapat amb aïllant (~3 €)**. És el
KPI que mesura de debò si guanyes la batalla contra el fong, i **cap tutorial d'Internet el
posa**. Molt recomanat.

### Bloquejos de seguretat

Tots en AND amb la condició de ventilació, cadascun amb el seu llindar exposat com a helper.

| Bloqueig | Valor inicial | Raó |
|---|---|---|
| **T interior mínima** | no ventilar si T_int < 13 °C | Refredar el soterrani a l'hivern **baixa la temperatura de les parets i empitjora** el risc de condensació. Contraintuïtiu però cert |
| **Pluja** | bloqueig + 45 min de marge després | La regla de Td ja hauria de bloquejar, però un sensor exterior mullat dona HR falsa durant hores |
| **HR exterior alta** | bloqueig si HR_ext > 95 % durant > 10 min | Detector de pluja/boira de pobre, independent de la integració meteorològica |
| **Temps mínim d'engegada** | 12 min | Renovar l'aire triga, i els sensors tenen inèrcia (minuts en aire quiet). Menys de 10 min no mesura res |
| **Temps mínim d'aturada** | 10 min | Evita repicar i protegeix el motor |
| **Màx. arrencades/hora** | 4 | Xarxa de seguretat per si algú abaixa els temps mínims des de la interfície |
| **Sensor caigut o ranci** | `unavailable` o > 20 min sense actualitzar → **ventiladors OFF** | Fallada segura: sense dada exterior fiable, ventilar és una aposta |
| **Plausibilitat** | descarta T fora de [−10, 50] °C o HR fora de [1, 100] % | Els sensors Zigbee barats escupen valors absurds, sobretot amb bateria baixa |
| **Splits en marxa** | no ventilar si el split refrigera | Ventilar mentre climatitzes és tirar euros per la reixa |
| **Horari de silenci** | configurable, p. ex. 23:00–08:00 | Soroll en un local amb veïns a sobre |

### Relleu entre ventilador i deshumidificador

Ordres de magnitud a verificar amb les màquines reals: **extractor 30–150 W**,
**deshumidificador per compressor 300–700 W**. És a dir, **entre 5 i 20 vegades més car per
hora**.

**Enclavament dur, prioritat al ventilador:**

```
Si (ventilació viable)       →  ventilador ON,   deshumidificador OFF
Si (ventilació NO viable)
   i (Td_int > Td_objectiu)  →  ventilador OFF,  deshumidificador ON
Altrament                    →  tots dos OFF
```

**Mai simultanis.** Si deshumidifiques mentre extreus aire cap al carrer **estàs
deshumidificant Barcelona**: pagues 600 W per assecar aire que expulses immediatament. És
l'error més car possible, i l'enclavament l'ha de fer impossible **per construcció**, no per
coincidència de condicions.

- **Retard de commutació de 5 min** en passar de ventilar a deshumidificar: just després
  d'aturar el ventilador els sensors llegeixen un transitori.
- **Anti-cicle curt del compressor: mínim 5 min OFF, idealment 20–30 min ON.** Un compressor
  hermètic arrenca contra pressió si el reconnectes abans que s'equilibri el circuit;
  repicar-lo el mata. **És el límit de maquinari més rígid de tot el sistema.**

### 💶 Encaix amb la tarifa Naturgy Noche

Amb la [tarifa contractada](../local/subministraments.md), la punta costa **2,47 vegades** la
vall. Això afegeix una capa econòmica a la lògica:

- **El deshumidificador hauria de treballar preferentment en vall** (00:00–08:00 entre
  setmana i **tot el cap de setmana**). Quan la ventilació no és viable i la situació no és
  urgent, val la pena **ajornar el deshumidificador fins a la vall** en comptes de fer-lo
  anar en punta.
- **Els ventiladors no s'han de vetar mai per preu:** consumeixen poc i el criteri que els
  governa és físic. Si l'aire de fora asseca, ventilar surt a compte sempre.
- **Les dues lògiques empenyen en la mateixa direcció:** la finestra de ventilació gratuïta a
  Barcelona és sobretot **nocturna**, que és justament la franja vall.
- Cal exposar un **llindar d'urgència**: si el marge de condensació a la paret baixa de
  ~2 °C, el deshumidificador s'engega **encara que sigui punta**. La salut de la paret va
  abans que el preu.

### Dues arquitectures per al deshumidificador

| | (a) Higròstat propi, endoll només com a interruptor | (b) Higròstat a «continu», HA ho controla tot |
|---|---|---|
| Robustesa | **Alta**: si HA cau, segueix regulant sol | Baixa: si HA cau, o va sempre o mai |
| Control fi | Nul | Total |
| Anti-cicle curt | El gestiona la màquina | **L'has de programar tu, sense excusa** |

**Recomanació: (a) per començar**, amb l'higròstat de la màquina a l'objectiu i HA fent
només l'enclavament i els horaris. És la que degrada bé. Passa a (b) només si les dades del
primer mes mostren que l'higròstat intern és massa tosc (molts ho són).

> ⚠️ **Verificació bloquejant:** molts deshumidificadors **no es reprenen sols després d'un
> tall de corrent** — es queden en *standby* esperant que algú premi el botó físic. Si el teu
> és d'aquests, **tot el control per endoll intel·ligent és inútil**. Prova-ho: engega'l,
> desendolla'l, torna'l a endollar, mira si arrenca sol.
>
> Comprova també si desguassa per tub. Si no, el dipòsit s'omple, s'atura sol i l'automatisme
> no se n'assabenta — detecta-ho com a «endollat però consumint < 50 W» = alarma de dipòsit ple.

> ⚠️ **Límit físic:** els deshumidificadors per compressor perden molt rendiment per sota de
> ~15 °C i per sota de ~12 °C es glacen. Si el soterrani baixa de 15 °C al gener, caldria
> valorar-ne un dessecant. **Mesura la temperatura del soterrani un hivern sencer abans de
> comprar la màquina.**

## B) On viu la lògica

| Opció | Canviar llindars sense codi | Depurabilitat | Robustesa |
|---|---|---|---|
| **Automatitzacions HA + Jinja** | Nativa | **Molt bona**: el visor de traces diu quina condició ha fallat i amb quins valors | Bona: un sol procés |
| **Node-RED** | Bona | Molt bona en flux | Add-on separat, pot caure a part |
| **AppDaemon** | Via `apps.yaml` | Mitjana | **Feble**: procés extern que pot morir en silenci |
| **pyscript** | Bona | Mitjana-bona | Bona: corre dins HA |
| **Servei Python propi** | Te l'has de fer | Excel·lent en local, **pèssima en producció** | **La pitjor**: tokens, reconnexió, systemd, ordre d'arrencada |

**Recomanació: automatitzacions natives d'HA, amb un truc d'arquitectura.**

El truc és **treure les matemàtiques de l'automatisme**:

1. Crea **sensors de plantilla** que calculin Td_int i Td_ext. Són entitats: es grafiquen i
   es verifiquen d'un cop d'ull. *(Alternativa: la integració HACS **Thermal Comfort** ja
   dona punt de rosada a partir de qualsevol parell T/HR, sense escriure una línia.)*
2. Crea un sensor de plantilla **ΔTd = Td_int − Td_ext**.
3. L'automatisme queda reduït a **comparacions numèriques i temporitzacions**.

Amb això desapareixen les dues objeccions habituals contra HA natiu (Jinja il·legible,
lògica inescrutable). I el **visor de traces** —que et diu, per a cada execució, quina
condició concreta va bloquejar i amb quin valor— **no té equivalent en cap de les altres
opcions**. Per a un sistema el problema del qual serà *«per què no va ventilar ahir a les
3»*, això val més que la potència del llenguatge.

> Com a enginyer de telecos et vindrà la temptació del servei Python propi. El problema aquí
> **no és el llenguatge: és la màquina d'estats amb temporitzacions**, i HA ja regala `for:`,
> `last_changed` i els helpers `timer`. El 90 % del que escriuries és fontaneria ja feta.
> **El següent graó natural és pyscript** (Python dins d'HA), no Node-RED ni AppDaemon —
> i només quan la màquina d'estats passi de 2–3 automatismes.

### «Què passa si cau el servidor» — la resposta honesta

**Cap de les cinc opcions sobreviu**, perquè totes corren al mateix portàtil. Debatre
Node-RED contra AppDaemon per robustesa és discutir la disposició de les cadires. La
robustesa real es compra **al nivell de dispositiu**:

1. **Configura el comportament d'arrencada de cada endoll/relé.** Endoll del
   deshumidificador → *power-on: ON*. Relés dels ventiladors → *OFF*. Així una caiguda d'HA
   degrada a «el deshumidificador regula sol amb el seu higròstat, els ventiladors aturats».
   Estat segur. **Aquesta línia de configuració val més que tota la discussió de frameworks.**
2. **Amb ESPHome, posa lògica local a bord.** Un ESP32 amb sensors cablejats pot calcular Td
   i decidir sense HA. És l'única capa de control que sobreviu de veritat.
3. **El portàtil:** desactiva la suspensió per tapa tancada i per inactivitat a Mint
   (`logind.conf`) o t'aturaràs el sistema tu mateix el primer dia. I fixa la retenció del
   `recorder` des del minut zero (vegeu [monitoritzacio.md](monitoritzacio.md)): omplir el
   disc és, estadísticament, **la causa número u de mort d'una instal·lació d'HA**.

## C) Paràmetres ajustables i control manual

### Helpers

**`input_number`** (amb `min`/`max` que impedeixin valors suïcides):

| Helper | Rang | Defecte |
|---|---|---|
| `delta_td_on` | 1,0 – 5,0 °C | 2,0 |
| `delta_td_off` | 0,0 – 3,0 °C | 0,8 |
| `hr_objectiu` | 45 – 65 % | 55 |
| `marge_superficie_min` | 1,5 – 5,0 °C | 3,0 |
| `t_int_minima` | 8 – 18 °C | 13 |
| `hr_ext_bloqueig` | 88 – 100 % | 95 |
| `min_on_ventilador` | 5 – 60 min | 12 |
| `min_off_ventilador` | 5 – 60 min | 10 |
| `min_off_deshumidificador` | 5 – 30 min | 5 |

**`input_boolean`**: `automatismes_actius`, `mode_prova`, `permet_nit`, `vacances`.
**`input_select.mode_soterrani`**: `Auto` / `Forçar ventilació` / `Forçar deshumidificador` /
`Tot aturat`. **`timer.override_manual`**: 2 h per defecte.

### El patró que evita que tu i l'automatisme lluiteu

1. **Tots els automatismes porten com a primera condició `mode_soterrani == Auto`.** En mode
   manual, l'automatisme **no és que perdi la baralla: és que no entra al ring**. No hi ha
   carrera possible. Qualsevol solució del tipus «l'automatisme detecta que l'usuari ha tocat
   una cosa i s'aparta» és fràgil; aquesta és determinista.
2. **Separa intenció d'actuació.** Els helpers són la *intenció de l'usuari*; els `switch`
   són l'*estat del maquinari*. **L'automatisme llegeix helpers i escriu switches, mai a
   l'inrevés.** Si l'automatisme escriu als helpers tindràs bucles de realimentació i
   deixaràs de saber qui ha demanat què. És l'error de disseny més comú a mesura que una
   instal·lació creix.
3. **Tota sortida d'`Auto` arrenca `timer.override_manual`, i en acabar torna a `Auto` sol.**
   Això resol el mode de fallada més freqüent del món real, que no és un bug: és que un
   dimarts forces la ventilació, te'n vas, i tres setmanes després descobreixes que fa un mes
   que l'automatisme no fa res.
4. **`Tot aturat` no caduca** (és per a manteniment o vacances), però pinta'l en vermell i
   genera un recordatori diari. Opcional però recomanat: que surti igualment de `Tot aturat`
   si el marge de condensació baixa de 2 °C.
5. **Override físic.** Si els ventiladors estan cablejats a un interruptor de paret, un relé
   Shelly en **mode *detached*** deixa l'interruptor funcionant com a **entrada lògica** a HA
   en comptes de tallar el corrent: prémer-lo passa a `Forçar ventilació` durant 2 h. És la
   millor experiència possible i costa el mateix relé que necessitaves igualment. **Molt
   recomanat.**

### Dues eines de depuració, el primer dia

**Sensor de motiu.** Un sensor de plantilla que digui en text pla per què el sistema fa el
que fa: `"Ventilant"`, `"Exterior massa humit (ΔTd=0,4 °C)"`, `"Bloqueig per pluja"`,
`"Esperant min_off (4 min)"`, `"Objectiu assolit"`, `"Sensor exterior no disponible"`. Vint
minuts de feina, i és **l'element de més valor per hora invertida de tot el projecte**:
converteix cada «per què no fa res?» en una mirada al panell.

**Mode de prova.** L'automatisme avalua tota la lògica i **registra la decisió sense accionar
res**. Deixa'l així 2–4 setmanes. Valida els llindars contra dades reals abans que un relé es
mogui, i respon la pregunta que de veritat importa: **quantes hores l'any hauria ventilat de
franc?** Si són 200 h, el projecte s'amortitza; si en són 900, és un èxit; si en són 40, ja
saps que l'objectiu d'estalvi no anava enlloc i t'has estalviat els relés.

## D) Maquinari

### El problema de la cobertura, primer

Amb un soterrani i un forjat de formigó armat pel mig, «poso un dongle USB al portàtil i ja
arriba» és la premissa que et farà perdre dos caps de setmana: el formigó armat atenua
brutalment a 2,4 GHz. Per ordre de recomanació:

1. **Coordinador Zigbee en xarxa, col·locat al soterrani.** Un **SLZB-06/06M** (~35–45 €) es
   connecta per **Ethernet o PoE**, no per USB. Poses la ràdio **on són els dispositius**.
   Elimina el problema d'arrel per ~15 € més que un dongle USB. **Recomanació principal.**
2. **Els endolls fan de repetidors.** Tot dispositiu Zigbee alimentat és un router de la
   malla. Posa'n un a l'escala entre planta baixa i soterrani i tindràs el salt cobert.
   Planifica'ls, no els posis on toqui per casualitat.
3. **ESPHome sobre ESP32 amb Ethernet cablejat** (Olimex ESP32-POE o ESP32 + W5500, ~25 €):
   immune per definició a la cobertura, perquè no fa servir ràdio. I et deixa lògica local.

**Si res d'això funciona, Z-Wave.** A 868 MHz la penetració en formigó és notablement millor
— això és física, no màrqueting. El problema és el preu: 2–3× el Zigbee. **Opció de rescat
vàlida, no primera elecció.** No la compris «per si de cas»: compra Zigbee, fes la prova de
cobertura i decideix amb dades.

> **Dos detalls que estalvien un dia de feina:** el dongle USB sempre amb **allargador USB
> d'1 m** (els ports USB 3.0 generen soroll a 2,4 GHz que ensorra el Zigbee; és un problema
> documentat i molt real). I tria **canal Zigbee 15, 20 o 25**, lluny dels canals Wi-Fi.

### Sensors

| Funció | Recomanació | Preu |
|---|---|---|
| **T/HR interior** (×3: paret humida, centre a 1,5 m, prop de l'extracció) | Zigbee: Sonoff SNZB-02P o Aqara WSDCGQ11LM | 12–20 €/u |
| **T/HR exterior** | Mateix model, dins un **abric de radiació** ventilat, a l'ombra, sota ràfec | 15 € + 10 € |
| **T superfície paret freda** | DS18B20 sobre ESP32/ESPHome, enganxat i tapat amb aïllant | 3 € + ESP32 |
| **Referència d'alta precisió** | SHT31/SHT35 al mateix ESP32 — patró per calibrar els Zigbee barats | 8–15 € |
| **CO₂ (diagnòstic)** | SCD40/SCD41 | 30–45 € |
| **Pluja** | Integració Met.no o AEMET | 0 € |

El **sensor exterior és el punt feble de tot el sistema**: mai al sol directe ni exposat a
pluja. Fes servir el sensor local com a **primari** i la integració meteorològica com a
**reserva i comprovació de plausibilitat** (si difereixen més de 4 °C de Td, sospita de
sensor mullat). Una estació a 3 km pot equivocar-se per diversos graus de Td respecte de
l'aire que de veritat entra per la reixa.

El **CO₂ serveix de traçador** per mesurar renovacions/hora reals: mires la corba de
decaïment quan arrenca el ventilador i en dedueixes el cabal efectiu. És l'única manera
barata de saber si els extractors mouen aire de debò o només fan soroll. Es pot posar
temporalment i retirar.

### ⚠️ Una incògnita estructural que ho pot canviar tot

Els sistemes són **d'extracció cap a l'exterior**: posen el soterrani en **depressió** i
l'aire de reposició entra **per on pot**.

- Si entra per reixes a l'exterior → perfecte, el criteri de Td exterior és el correcte.
- Si entra **de la planta baixa** → estàs comparant el Td que no toca, i a l'estiu xuclant
  aire climatitzat cap avall per llençar-lo al carrer. El criteri correcte passaria a ser el
  Td de la planta baixa.
- Si entra **per fissures en contacte amb el terreny** → **estàs xuclant activament aire
  saturat del subsol i el ventilador pot estar empitjorant les humitats.**

**Verifica el camí de l'aire físicament** (paperet o fum a les obertures amb els ventiladors
en marxa) **abans d'invertir en automatització**. Si és el tercer cas, el projecte canvia de
naturalesa. Si cal, posa un quart sensor **al punt d'entrada real** i fes servir aquell com a
«exterior» a la fórmula — que és, al capdavall, l'aire que de debò entra.

### Commutació i mesura

| Funció | Recomanació | Preu |
|---|---|---|
| **Mesura del deshumidificador** | **Shelly Plug S Gen3** (Wi-Fi, API local, sense núvol) | ~22–28 € |
| Alternativa Zigbee | Sonoff S60 / S31 Lite ZB amb mesura | 15–20 € |
| **Commutació ventiladors** | **Shelly Plus 1PM** encastat, un per ventilador | 15–25 €/u |
| **Splits per IR** | ESP32 amb ESPHome (`climate_ir`) + LED emissor **i receptor** IR | ~10 € |

**Per què Shelly i no Tuya genèric:** API HTTP/MQTT **local documentada**, sense dependència
de núvol, comportament d'arrencada configurable i mesura decent. Un endoll Tuya de 12 € depèn
d'un servidor extern i pot deixar de funcionar amb una actualització de firmware.

**Per als ventiladors, el punt clau és si estan cablejats o endollats.** La ventilació
forçada sol estar cablejada fixa, i llavors el que toca és un **relé darrere l'interruptor**
(no un endoll): manté l'interruptor físic operatiu i habilita el mode *detached*.

> ⚠️ **Intervenció en instal·lació fixa: que la faci un instal·lador autoritzat**, conforme al
> REBT. Els motors són càrrega inductiva: comprova que el relé està homologat per a càrrega
> de motor, no només resistiva.

**Els splits per IR són llaç obert:** HA envia l'ordre i *creu* que s'ha executat. Si algú
toca el comandament, HA es desincronitza i decidirà sobre un estat fals. Dues solucions, i
la segona és la bona:

1. Mesura de consum al circuit del split → si consumeix > 200 W, el compressor va. Estat
   **real**.
2. Posa un **receptor IR** al mateix ESP32: HA *escolta* el comandament físic i actualitza el
   seu estat. **Costa 1 € més i converteix un sistema mentider en un sistema honest.**

### Pressupost per fases

| Fase | Contingut | Cost |
|---|---|---|
| **0 — Mesurar** (2–4 setmanes, sense actuar) | Coordinador SLZB-06 + 4 sensors T/HR + endoll amb mesura | **~110–130 €** |
| **1 — Control** | 2 relés per als ventiladors + 1 endoll-repetidor | **+ ~55 €** |
| **2 — Refinament** | ESP32 PoE + SHT31 + DS18B20 + IR TX/RX | **+ ~55 €** |
| **3 — Opcional** | CO₂, Shelly EM global, SAI | **+ 80–250 €** |
| | **Nucli funcional** | **~220–240 €** |

Mà d'obra elèctrica no inclosa. La variant Z-Wave costaria aproximadament el doble.

## Punts febles del disseny — la part honesta

1. **L'origen de la humitat encara no el sap ningú, i ho canvia tot.** Si és
   **capil·laritat o aigua freàtica** —que és el que normalment vol dir «humitats» en un
   soterrani— la font d'aigua és il·limitada i entra per l'estructura, no per l'aire. Cap
   lògica de control resol això: el deshumidificador anirà quasi contínuament i l'únic
   resultat serà **quantificar amb precisió quant costa el problema**. Que no és poc —és
   exactament l'argument numèric per justificar una obra— però no és el que promet l'objectiu
   d'estalvi. **Mesura els litres/dia que retira el deshumidificador: és el diagnòstic.** Per
   sobre de ~8–10 L/dia sostinguts, la conversa ja no és de domòtica sinó de construcció.
2. **L'estalvi pot ser petit a l'estiu, i no és un bug.** A Barcelona, de juny a setembre el
   Td exterior sol moure's entre 18 i 23 °C, i un soterrani fresc estarà sovint per sota.
   L'automatisme dirà **«no ventilar» la major part de l'estiu**, i tindrà raó. La finestra
   de ventilació gratuïta és sobretot **nits d'octubre a maig** i dies de ponent. L'estalvi
   pot ser molt real, però està concentrat **fora de l'estiu**, que és quan la intuïció diu
   el contrari. No en sabrem la xifra fins a tenir dades.
3. **El camí de l'aire de reposició és la incògnita més cara.** Vegeu més amunt.
4. **Deriva dels sensors.** Els sensors d'HR barats deriven 1–2 %/any, i molt més si pateixen
   condensació o pols — i l'exterior de Barcelona patirà les dues coses. Com que el sistema
   decideix per una **resta**, una deriva diferencial de 3 % HR (≈0,7 °C de Td) es menja mig
   llindar. **Posa't al calendari una comparació anual.** Com a patró absolut, el **test de
   la sal**: pasta saturada de NaCl en recipient tancat = 75,3 % HR a 20 °C, molt repetible.
   Cost zero.
5. **El portàtil és un punt únic de fallada** amb tres morts conegudes: suspensió, disc ple
   per creixement de la base de dades, i actualitzacions que mouen el dongle a un altre
   `/dev/tty*`. Mitiga amb `by-id` per al port sèrie, retenció configurada, còpies
   automàtiques i suspensió desactivada.
6. **Reinici de l'automatisme:** quan HA es reinicia, `last_changed` es reinicia també i els
   temps mínims ON/OFF es perden — i les primeres setmanes es reiniciarà sovint. Mitiga amb
   un `input_datetime` persistent, o amb un bloqueig global de 10 min després de l'arrencada.
   **Detall petit, fàcil d'oblidar, i que apareix just quan menys t'ho esperes.**

## Llista de verificació abans de gastar diners

- [ ] **El deshumidificador arrenca sol després d'un tall de corrent?** *(Si no → el control
      per endoll no serveix.)*
- [ ] Placa de característiques: potència, L/dia, temperatura mínima de treball, desguàs per tub.
- [ ] **Per on entra l'aire de reposició quan els extractors funcionen?** *(Prova de fum.)*
- [ ] Potència i tipus dels extractors. Estan endollats o cablejats? Hi ha interruptor de paret?
- [ ] **Prova de cobertura:** un dispositiu Zigbee al soterrani amb el coordinador a la planta
      baixa, 48 h, mirant LQI i paquets perduts. Decideix amb aquesta dada.
- [ ] Rang de temperatura del soterrani a l'hivern (condiciona el tipus de deshumidificador).
- [ ] Quina paret és la més freda i humida (termòmetre IR de mà, ~20 €) → allà va el DS18B20.
- [ ] Hi ha punt de xarxa, PLC o Ethernet des del router SIM fins al soterrani?
- [ ] Horaris de soroll admissibles per als veïns.

## Ordre de treball proposat

**Fase 0 (setmanes 1–4): només mesurar.** Sensors, endoll amb mesura, sensors de plantilla de
Td, panell amb gràfics i sensor de motiu, mode de prova activat. **Cap relé.** Al final
tindràs litres/dia reals, consum real del deshumidificador i **quantes hores hauria
ventilat** amb cada joc de llindars. Amb això, els paràmetres d'aquest document deixen de ser
estimacions i passen a ser les teves dades.

**Fase 1 (setmana 5+): actuar.** Relés, enclavament, temporitzacions, selector de mode amb
caducitat.

**Fase 2: refinar.** Marge de superfície com a objectiu de control, calibratge creuat,
splits, validació de renovacions amb CO₂.

> **No saltis la Fase 0.** És la que decideix si l'objectiu d'estalvi té sentit econòmic, i
> costa la meitat del pressupost total amb zero risc elèctric.
