# El deshumidificador — com funciona i què n'ha de saber HA

> Escrit el **21/09/2026**, el dia que va entrar a HA per `tuya-local`, a partir del manual i
> de **set experiments** fets aquell vespre a casa, en una habitació apart del calibratge.
> L'aparell: **Qlima D 825 PA Smart** ([inventari.md](inventari.md#deshumidificador)).
> Les proves es poden repetir: [`tools/prova_deshumidificador.py`](../../tools/prova_deshumidificador.py).

## En una frase

**Obeeix, recorda i es mesura**: una ordre per `tuya-local` arriba a l'aparell i el compressor
respon en menys de 10 segons, recorda la configuració després d'un tall de corrent, i els watts
de l'endoll diuen sense ambigüitat què fa. **Però en mode AUTO ignora el llindar**, i això ho
canvia tot per a qui el vulgui governar.

## Els dos camins, i per a què serveix cadascun

| | `tuya-local` (Wi-Fi, local) | P110M (Matter) |
|---|---|---|
| Què dona | El que l'aparell **creu**: mode, llindar, HR pròpia, avaria | El que l'aparell **fa**: watts i kWh |
| Si l'aparell es queda sense corrent | ⚠️ **No se n'assabenta**: segueix mostrant l'últim estat (perd la connexió al cap de ~30 s i no marca res com a no disponible) | 0 W a l'instant |
| Per a què | **Ajustar** (llindar, mode) i **llegir** l'estat intern | **Saber la veritat** i fer el tall dur |

> 📌 **Regla que en surt:** l'estat real es llegeix als **watts**, mai a `tuya-local` sol. És
> la regla de [requisits.md](requisits.md) —«watts, no relés»— aplicada a un segon camí.

## La signatura de consum

Mesurada als experiments (vegeu més avall). És el que permet saber què fa l'aparell sense
preguntar-li:

| Estat | Watts | Com es reconeix |
|---|---|---|
| **Compressor en marxa** | **345–370 W** (puja a poc a poc mentre s'escalfa; la placa en diu 470) | > 150 W |
| **Només el ventilador** | **15 · 31 · 48 W** a velocitat baixa · mitjana · alta | 5–50 W: el ventilador sol, els ~5 min que segueix després d'aturar el compressor, o purificar |
| **En espera** | **~1,1 W** | < 5 W |
| **Aturat per dipòsit** (P2) | **~0,8 W** | < 5 W **i** el codi d'avaria a 32 |

## Què diu el manual, i què n'hem comprovat

Manual oficial, pàgines 29–34 de la versió anglesa
([ManualsLib](https://www.manualslib.com/manual/3455713/Qlima-D-825-Pa-Smart.html)):

| Funció | El manual | Comprovat el 21/09/2026 |
|---|---|---|
| **Modes** | Manual · Roba · Nit · AUTO | Per `tuya-local`: `normal` · `laundry` · `sleep` · `auto` |
| **Llindar** | «CO, 40 %, 45 %… 80 %, CO». *«Only dry clothes mode and AUTO mode could not set humidity»* | ✅ **En AUTO el rebutja sense dir res**: es va demanar 55 % en AUTO i es va quedar al 80 %. El **35** que admet HA es comporta com el **CO** (assecar sense parar); falta veure-ho a la pantalla → [pendents](../pendents.md) |
| **Operació** | «ECO dehumidifier / purify / dehumidifier» | Les dues de deshumidificar gasten **el mateix** (357 i 371 W): per potència no hi ha cap «ECO» visible. **Purificar = ventilador sol**, i l'aparell s'hi posa sol en mode Roba — experiment 3 |
| **Velocitat** | 1 · 2 · 3 · AUTO | `tuya-local` en dona tres (33/67/100 %) i no l'AUTO |
| **Reinici i memòria** | Contradictori (vegeu [inventari.md](inventari.md#-una-contradicció-al-manual-que-cal-provar)) | ✅ **Recorda-ho tot i es reprèn sol** — experiment 2 |
| **Protecció del compressor** | 5 min entre aturada i arrencada | ✅ I **també en arrencar**: després d'un tall de corrent va esperar ~5 min abans d'engegar el compressor. Tallar l'endoll no li fa perdre la protecció — experiment 3 |
| **Dipòsit ple (P2)** | S'atura, 10 xiulets, indicador | ✅ **Codi d'avaria 32**, tant **ple** com **tret**, i s'esborra en 1 s en posar-lo buit. **Cap xiulet** en tota la prova — experiment 8 |
| **Desgebratge (P1)** | Automàtic amb fred | Per veure a l'hivern |
| **Bomba** | Botó PUMP; fins a 4 m | Sense bomba de moment (a casa es buida el dipòsit a mà) |
| **Codis** | C1 · C2 · C8 (sensors) · P4 (sensor d'HR) · **P34 fuita de refrigerant** | Cap avaria vista |
| **Filtre** | Avís a les 360 h de funcionament | — |

## Els experiments del 21/09/2026

Tots amb [`tools/prova_deshumidificador.py`](../../tools/prova_deshumidificador.py), que
restaura la configuració d'abans en acabar i no deixa mai l'endoll apagat. L'habitació: una
altra que la del calibratge; amb aire condicionat fins a les ~19:10, i sense a partir d'aquí.

### 1. Resposta — l'ordre arriba i el compressor obeeix ✅

Llindar al 35 % i al 80 %, dos cicles de 10 min (19:06–19:46). **Les quatre fases van respondre
en menys de 10 s** i el compressor va fer el que se li demanava **el 100 % del temps**: 349 i
365 W en marxa, 1 W aturat.

**I la troballa del final:** en restaurar, l'eina va tornar primer el mode AUTO i després el
llindar, i el llindar **es va quedar al 80 %**. És la confirmació pràctica del manual: en AUTO
l'aparell no accepta el llindar. L'eina ara el restaura **en Manual** i torna el mode l'últim.

### 2. Memòria (la prova 0.2b)

✅ **Superada.** Configuració inconfusible (Manual · 70 % · velocitat baixa), compressor quiet 6 minuts, i
**un minut sense corrent** tallant l'endoll (20:11:02–20:12:04, **0,0 W** gravats). En tornar
el corrent, **l'aparell mateix** —una lectura sencera nova a les 20:12:11, no la memòria de
`tuya-local`— deia **Manual · 70 % · velocitat baixa**, i va arrencar sol el ventilador.

**Conseqüència:** la 🔴 de fases 0.2b queda tancada, i l'arquitectura (a) —l'higròstat de
l'aparell regula, HA només fa l'enclavament i els horaris— queda **confirmada**.

Dues coses que va ensenyar de passada:

- ⚠️ **`tuya-local` no va marcar l'aparell com a no disponible** durant el tall: va perdre la
  connexió al cap de 32 s i va seguir mostrant l'últim estat. Per això la regla de dalt.
- 📌 **L'HR que mesura l'aparell només val amb el ventilador en marxa.** En arrencar va baixar
  del 60 al 50 % en 40 s, a mesura que el ventilador movia l'aire pel sensor. Amb el
  ventilador aturat llegeix l'aire quiet que té al voltant.

### 3. Operació — ECO, purificar, deshumidificar

Mode normal i llindar en continu, 8 min per operació (20:12–20:49):

| Operació (`tuya-local`) | Valor que envia | Watts | Compressor |
|---|---|---|---|
| `dehumidify` | `dehum_air` | **357 W** | 100 % |
| `dehumidify_and_purify` (com venia) | `dehum30_air` | **371 W** | 100 % |
| `purify` | `airpurify` | **30,5 W** | 0 % |
| torna a `dehumidify` | `dehum_air` | 362 W | arrenca **en 10 s** |

- **Per potència no hi ha cap «ECO».** Les dues de deshumidificar difereixen menys del que el
  compressor puja sol en escalfar-se. Si l'«ECO» del manual fa alguna cosa, és en com cicla, i
  això només es veu **mesurant litres**. Les etiquetes són les del D820A, i no se sap quina de
  les dues és l'ECO del botó.
- **Purificar és el ventilador sol, i l'aparell hi canvia el mode tot sol a Roba**
  (`dry_clothes`). En tornar a deshumidificar, torna a Manual. HA ho ha de saber: triar
  purificar no és innocent.
- ✅ **La protecció del compressor també compta en arrencar.** Aquest experiment va començar
  just després del tall de corrent de l'experiment 2, amb el llindar en continu: el compressor
  va trigar **~5 min** a engegar. [inventari.md](inventari.md#-la-protecció-del-compressor-ja-és-a-laparell)
  temia que un tall li fes perdre la protecció; no la perd, en arrencar espera. **HA ha de
  seguir respectant el seu mínim d'aturada**, però ara amb xarxa doble.

### 4. Ventilador — les tres velocitats amb el compressor

Mode normal, llindar en continu, 5 min per velocitat (segona tanda, 21:34–21:54; la primera es
va espatllar perquè la prova del dipòsit va aturar l'aparell enmig):

| Velocitat | Watts |
|---|---|
| Baixa (33 %) | **356 W** |
| Mitjana (67 %) | **358 W** |
| Alta (100 %) | **363 W** |

**Amb el compressor en marxa, la velocitat gairebé no hi compta: ~7 W de la baixa a l'alta**, i
ni tan sols són tots del ventilador, perquè el compressor puja sol mentre s'escalfa. Sol, en
canvi, el ventilador va de 15 a 48 W (experiment 5): amb el compressor, l'aparell no el deu fer
anar igual.

**Conseqüència per a l'eficiència: velocitat alta per defecte quan asseca**, però **a confirmar
en litres**. Per ~7 W més mou molt més aire; alhora, més cabal refreda menys la bateria, i cada
kg d'aire hi deixa menys aigua. Normalment guanya el cabal, sobretot amb l'aire humit, però no
sempre. Amb fred, al soterrani, la velocitat alta a més allunya el glaç.

### 5. El ventilador sol — què costa només moure aire

Operació purificar, 4 min per velocitat (21:10–21:26):

| Velocitat | Watts | Per hora | 24 h en vall | 24 h en punta |
|---|---|---|---|---|
| Baixa (33 %) | **15,5 W** | 0,016 kWh | 3,5 c€ | 8,6 c€ |
| Mitjana (67 %) | **30,7 W** | 0,031 kWh | 6,9 c€ | 17,1 c€ |
| Alta (100 %) | **47,9 W** | 0,048 kWh | 10,8 c€ | 26,6 c€ |

*(Preus amb impostos de [subministraments.md](../local/subministraments.md): 0,0940 €/kWh en
vall i 0,2317 en punta.)*

**Val la pena per remenar l'aire?** És barat: una hora al dia a velocitat alta és **mig cèntim
en vall i poc més d'un en punta**. Però cal tenir clar què fa i què no:

- ✅ **Remena l'aire de la sala** —el fabricant hi dona 200 m³/h, gairebé dues vegades el volum
  del soterrani per hora—: trenca les bosses d'aire quiet i humit dels racons, iguala la
  temperatura i ajuda les superfícies a assecar-se per convecció. I passa l'aire pel filtre
  HEPA.
- ❌ **No renova l'aire amb el de fora ni treu aigua.** Això ho fan els ventiladors del local
  (la ventilació) i el compressor (la deshumidificació). Remenar no canvia el punt de rosada de
  la sala.
- ⚠️ En purificar, l'aparell es posa en mode Roba: HA l'ha de **tornar a Manual i al llindar**
  en acabar, o quedarà en un mode que no governa.

La idea útil, doncs: **ventilador sol d'estona en estona quan no cal assecar**, per evitar
racons estancats, i sobretot si els tres sensors del soterrani mostren diferències grans entre
ells —la `dispersio` de `sensor.soterrani_punt_de_rosada_de_referencia`. És una idea per a la
Fase C, no una decisió.

### 6. Modes — Manual, Nit, Roba i AUTO amb el llindar en continu

8 min per mode (10 en AUTO), segona tanda (21:54–22:28), HR de l'habitació 46–47 %:

| Mode | Watts | Compressor | Què hi canvia l'aparell sol |
|---|---|---|---|
| Manual (`normal`) | **366 W** | 100 % | — |
| Nit (`sleep`) | **374 W** | 100 % | Posa la velocitat **baixa** |
| Roba (`laundry`) | **374 W** | 100 % | — |
| AUTO | **366 W** | 100 % | — |

- **Els modes no canvien què gasta el compressor**: les diferències són l'escalfament. Només
  canvien el ventilador i **quan decideix engegar-lo**.
- **En AUTO, al 46–47 %, va assecar sense parar**; aquell mateix vespre en AUTO, al 44 %, feia
  tandes de 2 min i s'aturava 5. **Sembla que en AUTO manté cap al 45 %** pel seu compte, i no
  el llindar, que en AUTO no es pot canviar (experiment 1). És una estimació de dues
  observacions, no una mesura.
- **Per a HA: Manual.** És l'únic mode en què el llindar mana, que és la palanca de tota la
  lògica.

### 7. Assecat intern — quant va el ventilador després d'aturar-se

6 min de compressor i llindar al 80 % per aturar-lo, sense i amb l'assecat intern (22:30–22:57):

| | El ventilador segueix després d'aturar el compressor |
|---|---|
| Sense assecat intern | **5,0 min** |
| Amb assecat intern | **5,0 min** |

**Cap diferència.** Els 5 minuts de ventilador són el comportament normal de l'aparell quan el
llindar l'atura, i l'assecat intern no els allarga. El més probable és que l'assecat intern actuï
quan s'**apaga** l'aparell, no quan l'atura el llindar; aquesta prova no ho cobreix →
[pendents.md](../pendents.md). Per a HA, avui: **l'assecat intern no costa res de més** en el
funcionament normal.

La tanda va acabar restaurant bé la configuració d'abans (AUTO · 55 % · velocitat alta), ja amb
la restauració verificada.

### 8. El dipòsit — per quina dada surt el P2

Amb l'usuari al davant, que treia, omplia i tornava a posar el dipòsit (20:36–21:33):

| Què es va fer | Què va passar |
|---|---|
| Treure'l **mentre purificava** (compressor aturat) | **Res**: ni codi ni canvi de consum |
| Treure'l **amb el compressor en marxa** (20:59:24) | **Codi d'avaria 0 → 32** i tot aturat, a **~0,8 W** |
| Tornar-lo a posar buit (21:10:03) | Codi a 0 en 1 s |
| Treure'l per omplir-lo mentre purificava | Res… fins que va tornar a deshumidificar (21:26:21): **32** de seguida |
| Posar-lo **ple** (21:29) | Segueix a **32**, aturat |
| Buidar-lo i tornar-lo a posar (21:32:20) | Codi a 0 en **1 s**, i el compressor en **7 s** (la protecció ja havia passat) |

- ✅ **El P2 és el codi 32** de la dada 19, que `tuya-local` ja publica a
  `binary_sensor.deshumidificador_avaria` (atribut `fault_code`). **Dipòsit ple i dipòsit tret
  donen el mateix codi.** Les dades **106 i 107 no s'hi van moure**: queden per identificar (el
  P1, la bomba?).
- ⚠️ **Només es comprova quan deshumidifica.** Mentre purifica, un dipòsit tret no es detecta.
- 🔇 **Cap xiulet** en tota la prova, tot i que el manual en promet deu. En canvi, **xiula un
  cop per cada ordre que rep per `tuya-local`**, com si es premés un botó: les ordres d'HA se
  senten.
- 💧 Després d'una hora i poc de compressor el dipòsit era **completament sec**, amb el tap de
  desguàs posat i el terra sec. No és cap fuita: a 26 °C i un 45–60 % d'HR en treu poca (~0,3 L/h
  a ull), i abans d'arribar al dipòsit omple la safata interior —i, en un model amb bomba,
  segurament el seu dipòsit. **Els litres per kWh de debò demanen una nit sencera** →
  [pendents.md](../pendents.md).

## Què ha de saber HA de l'aparell

Per ordre d'importància. El que ja té entitat hi surt; el que no, és pendent.

| Què | Per què | D'on |
|---|---|---|
| **El mode** | En AUTO i en Roba el llindar **no fa res** (en AUTO sembla mantenir cap al 45 % pel seu compte). Si algú el posa en AUTO, HA ha de saber que ja no el governa | `humidifier.deshumidificador` (mode) |
| **L'estat real, pels watts** | «Endollat» no vol dir «assecant». Compressor / ventilador / espera, amb la signatura de dalt | `sensor.deshumidificador_potencia` |
| **Dipòsit ple (P2)** | S'atura i no seca. **Codi d'avaria 32** (experiment 8). I es confirma amb els watts: ~0,8 W quan li tocaria assecar | `binary_sensor.deshumidificador_avaria` (`fault_code` 32) + watts |
| **Avaries** | Sobretot **P34, fuita de refrigerant** (és propà) | `binary_sensor.deshumidificador_avaria` |
| **Desgebratge (P1)** | L'hivern al soterrani: estona descongelant en comptes d'assecar | ⏳ per identificar |
| **Hores de compressor** | El filtre cada 360 h, i les hores al dia són una casella de la Porta B. Es compten amb els watts, sense dependre de l'aparell | Watts |
| **L'operació** | **Purificar no asseca** i posa l'aparell en mode Roba: si hi és, HA no el governa | `select.deshumidificador_mode_aire` |
| **La velocitat** | Quan asseca, **alta per defecte**: amb el compressor només hi suma ~7 W (experiment 4). Si treu més aigua, a confirmar en litres. En mode Nit l'aparell la baixa sol | `fan.deshumidificador` |
| **El temporitzador** | Si algú el posa a mà, s'apagarà sol | `sensor.deshumidificador_temps_restant` |
| **El bloqueig infantil** | En un local, que ningú no li canviï el mode des dels botons | `lock.deshumidificador_bloqueig_infantil` |

## Si HA cau: el pla B ja hi és, i no demana programar res a l'aparell

L'experiment 2 ho confirma: **l'higròstat de l'aparell regula sol, recorda la configuració i es
reprèn sol**. El que cal és que la configuració en què el deixa HA sigui una en què l'aparell
es valgui per si mateix:

1. **Configuració de repòs: Manual · 55 % · velocitat alta · bomba activada · bloqueig
   infantil.** És on HA el deixa sempre, i on es queda si HA cau.
2. **Els canvis de HA, sempre temporals i amb tornada.** Si HA el posa en continu per aprofitar
   la vall i cau enmig, l'aparell es quedaria assecant sense parar: no fa mal, però paga punta.
   Per això HA ha de **restaurar la configuració de repòs cada cop que arrenca**.
3. **L'endoll torna encès** després d'un tall (`power_on_behavior: on`), i l'aparell es reprèn
   sol (experiment 2).
4. **L'app Smart Life**, pel núvol, segueix sent una via manual independent d'HA. Per això no
   s'ha tret l'aparell de l'app.

> 📌 Què passa amb tot el sistema —no només amb el deshumidificador— si cau la llum, el portàtil
> o internet: [home-assistant.md](home-assistant.md#què-passa-si-cau-la-llum-el-portàtil-o-internet).

> ⚠️ **En AUTO, com venia, no és una configuració de repòs vàlida**: HA no li pot canviar el
> llindar, i el que decideix l'aparell no es pot llegir enlloc.

## El que queda obert

→ [pendents.md](../pendents.md)
