# Lògica v2 — el pla per codificar-la

> **Estat: fases 0 a 3 fetes i desplegades (22/09/2026), en ombra.** Converteix en codi la proposta de [logica-v2.md](logica-v2.md),
> per fases petites: cada una és un PR, **es desplega recarregant, sense reiniciar HA**, i es
> pot provar sola. Mana [decisio-stack.md](decisio-stack.md), que hi apunta des de la revisió
> del 22/09/2026. Si aquest pla i `logica-v2.md` no diuen el mateix, **mana aquest** en el
> que és codi (noms, ordre, llindars de partida), i les diferències estan marcades amb ⚠️ a
> *Els estats*.

## En una frase

La v2 **substitueix la v1 dins de `sensor.decisio_del_soterrani`** i hi entra **en ombra**:
calcula i grava què faria —l'estat, el llindar i el mode del deshumidificador, si engegaria
els ventiladors i per què— **sense tocar cap aparell**, fins que s'encén a mà un interruptor
per aparell.

## Les decisions de codificació

| # | Què | Per què |
|---|---|---|
| **D1** | **La v2 va dins de `sensor.decisio_del_soterrani`**, amb el mateix `unique_id`: no hi ha una segona decisió al costat | Principi 5 de la v2: un sol punt de decisió. La v1 ja registra sense actuar, que és exactament el que farà la v2 en ombra; dues decisions en paral·lel serien dos punts de decisió. I **la sèrie de debò encara no ha començat** (`inicia-serie.sh`, al local): si la v2 hi entra abans, la sèrie comença ja amb ella. El canvi queda datat al registre d'instal·lació |
| **D2** | **La lògica, en una macro**: `config/custom_templates/decisio.jinja`, `decideix(entrades, parametres, minuts_fins_mitjanit)`, que torna JSON. El sensor passa a ser **per disparador** (cada minut i a cada canvi d'una entrada) i avalua la macro **una sola vegada** | L'estat, el motiu i el que s'ha de fer surten del mateix càlcul i no es poden desquadrar. A la v1 la lògica era dues vegades —a `state:` i a `motiu:`— i el 21/09/2026 s'havien desquadrat. I la rèplica es pot comparar **amb la macro de debò**: `replica.py --prova-ha` la fa avaluar a HA amb milers de casos i compara resultat a resultat, com `tarifa.py --prova-ha` |
| **D3** | **Es graven les entrades** a l'atribut `entrades`: tot el que ha fet servir la decisió, **menys l'hora i els paràmetres** | El test de deriva reprodueix cada fila exactament. L'hora no s'hi posa a posta: canviaria cada minut i faria una fila per minut; surt de la marca de temps de la fila. Els paràmetres ja tenen històric propi |
| **D4** | **Mode ombra = dos interruptors**: `input_boolean.actuacio_deshumidificador` i `input_boolean.actuacio_ventiladors`, **apagats** i sense `initial:` | Un reinici no els pot encendre ni apagar. Els automatismes que executen (Fase 3) hi són, però no fan res mentre estiguin apagats. La decisió grava si s'estava executant (atribut `actuacio`) |
| **D5** | **El deshumidificador es governa pel seu llindar** (`humidifier.deshumidificador`, per `tuya-local`), **no per l'endoll**. L'endoll mesura i queda sempre encès | Principi 6: el deshumidificador no s'apaga mai. ⚠️ **Supera dues coses escrites:** el «dos amos no» de [noms-entitats.md](noms-entitats.md) —l'amo passa a ser el `humidifier`, a posta— i l'**enclavament dur** de la tasca C.3 de [fases.md](fases.md): la v2 no apaga el deshumidificador quan ventila, li puja el llindar al 70 %, i en urgència treballen tots dos |
| **D6** | **Els ventiladors, darrere d'una interfície.** Un sol fitxer, `config/custom_templates/ventiladors.jinja`, diu quins relés són | Avui hi ha dos `input_boolean` virtuals, que permeten provar tota la cadena sense maquinari. El dia dels S110E s'hi escriu `switch.ventilador_1` i `switch.ventilador_2`, i res més |
| **D7** | **Paràmetres sense `initial:`**, i uns **valors de partida** que un automatisme posa **una sola vegada per paràmetre** (`input_number.parametres_versio`: cada fase que n'afegeix hi suma un bloc i puja la versió, o sigui que un paràmetre nou rep el seu valor encara que els vells ja el tinguin) | **Llegit al codi de la 2026.9.3 el 22/09/2026:** amb `initial:` l'helper arrenca **sempre** amb aquell valor —la sospita d'[R2](requisits.md#r2--tocar-els-paràmetres-de-lalgoritme-des-de-la-web) és certa—; sense, **restaura** l'últim; i sense estat previ agafa **el mínim del rang**, que per a `delta_td_on` seria 1,0 °C. L'automatisme cobreix aquest últim cas. Es fa per als nous i per als que es mouen de `rosada.yaml`: **resol R2 per a tots** |
| **D8** | **Un sol selector de mode**, `input_select.mode_soterrani` (el mateix, per no partir-ne la sèrie), amb opcions noves i sense `initial:`. Caducitat per mode amb `timer.override_manual` | El calibratge **no és un mode**: és `input_boolean.mode_calibratge`, i passa per davant de tot, com ara. La caducitat ara **s'atura** en passar a un mode que no caduca; abans no, i un temporitzador vell podia tornar a *Auto* un mode posat després |
| **D9** | **Tot es recarrega, res no reinicia.** Macros, plantilles, helpers, automatismes, scripts i `history_stats` tenen servei de recàrrega | Un reinici és un forat a l'històric. **Cap `utility_meter` nou**: només s'aplica reiniciant |
| **D10** | **La v2 viu a `config/packages/control.yaml`**: paràmetres, modes, decisió i executors. `rosada.yaml` es queda amb la física: punts de rosada, ΔTd, marge, calibratge i vigilància | Separa el que es mesura del que es decideix, i toca `rosada.yaml` el mínim possible mentre s'hi enganxen els desplaçaments del calibratge |

## Els modes

`input_select.mode_soterrani`. El primer és el de defecte. **La urgència automàtica passa
per davant de tots**, menys de *Tot aturat* i del calibratge.

| Mode | Per a què | Caduca | Deshumidificador | Ventiladors |
|---|---|---|---|---|
| **Òptim** | El dia a dia: la v2 tal com és, pel cost | no | Llindar del tram | Quan l'aire asseca, i la renovació diària |
| **Ocupat** | Algú hi dorm o hi treballa | 12 h | Mode **Nit**, llindar del tram | **Engegats**, fins i tot amb fred |
| **Prioritzar ventilació** | Renovar per sobre de l'estalvi: olors, després d'una sessió | 4 h | 70 % mentre ventila | **Engegats**, llevat de bloqueig |
| **Assecat intensiu** | Urgència a mà: una fuita, una entrada d'aigua | 12 h | **50 %**, sigui quin sigui el preu | Només si l'aire asseca |
| **Silenci** | Sense soroll: veïns, feina a dalt | 10 h | Mode **Nit**, llindar del tram | Aturats, llevat d'urgència amb aire que asseca |
| **Impressió** | Vapors de la resina | 3 h | Llindar del tram | **Engegats**, fins i tot amb fred |
| **Absència** | Vacances: menys renovació | no | Llindar del tram | Com *Òptim*, amb `renovacions_absencia` |
| **Llindar fix** | La **setmana de base** i els experiments: l'aparell a un llindar fix | no | `hr_fix` (55 %) en Manual | **No es toquen** |
| **Tot aturat** | Manteniment | no · recordatori diari | **No es toca** | Aturats |

- Les caducitats són de codi (git), no paràmetres: són comoditat, no comportament del control.
- *Llindar fix* és el que fa possible la setmana de base de [logica-v2.md](logica-v2.md#mètode)
  amb la Fase 3 desplegada: el llindar fix **sobreviu als talls de corrent**, perquè HA el
  torna a posar quan l'aparell torna amb la configuració de fàbrica.
- *Impressió* s'engega a mà. Quan hi hagi un endoll a la impressora, el seu consum podrà
  engegar-la sol: queda a *Fora d'aquest pla*.

## Els estats — el que es codifica

El primer que es compleix, mana.

| # | Estat | Quan | Deshumidificador | Ventiladors |
|---|---|---|---|---|
| 1 | `calibratge` | `mode_calibratge` encès | No es toca | No es toquen |
| 2 | `aturat` | Mode *Tot aturat* | No es toca | Aturats |
| 3 | `sense_dades` | Falta el Td, la HR o la T del soterrani, o un paràmetre | No es toca | ⚠️ **Aturats** |
| 4 | `urgencia` | HR màxima ≥ `hr_urgencia` (70 %; en surt 5 punts per sota), o marge de paret < `marge_superficie_min` (3,0 °C; en surt amb +0,5 °C), o mode *Assecat intensiu* | `hr_urgencia_objectiu` (50 %) | Si l'aire asseca i no hi ha bloqueig; ⚠️ **o si el mode és *Ocupat* o *Impressió*** |
| 5 | `ocupat` | Mode *Ocupat* | Nit, llindar del tram | Engegats |
| 6 | `impressio` | Mode *Impressió* | Llindar del tram | Engegats |
| 7 | `fix` | Mode *Llindar fix* | `hr_fix`, Manual | No es toquen |
| 8 | `bloquejat` | **Paràmetres incoherents**: Δ d'aturada ≥ Δ d'arrencada | Llindar del tram | Aturats |
| 9 | `ventilar` | ΔTd ≥ `delta_td_on` (2,0 °C), amb histèresi fins a `delta_td_off` (0,8 °C); sense bloqueig ni *Silenci* | `hr_mentre_ventila` (70 %) | Engegats |
| 10 | `higiene` | Mode *Prioritzar ventilació*; o falten minuts de renovació avui i **ara no mulla** (ΔTd ≥ `delta_td_higiene`) o **s'acaba el dia**. Sense bloqueig ni *Silenci* | `hr_mentre_ventila` | Engegats |
| 11 | `bloquejat` | ⚠️ **Es voldria ventilar** (9 o 10) però fa fred a dins (< `t_int_minima`) o, amb la referència *Exterior*, l'HR de fora és > `hr_ext_bloqueig` o plou | Llindar del tram | Aturats |
| 12 | `deshumidificar` | HR màxima > llindar del tram | Llindar del tram | Aturats |
| 13 | `repos` | La resta | Llindar del tram | Aturats |

**El llindar del tram** surt de `sensor.tarifa_periode`: `hr_vall` 55 · `hr_pla` 60 ·
`hr_punta` 65. Si el tram no se sap, el més baix dels tres (el costat segur). El mode de
l'aparell és **Manual** i la velocitat **alta**, llevat d'*Ocupat* i *Silenci*: mode **Nit**,
i la velocitat no s'hi toca (l'aparell ja la baixa sol).

**Les diferències amb [logica-v2.md](logica-v2.md)**, totes a posta:

1. ⚠️ **`sense_dades` atura els ventiladors** en comptes de deixar-los com estiguin. És el que
   demana la Porta C: *desconnectant un sensor, els ventiladors s'aturen*. I si només falta la
   **referència** (planta baixa o exterior), **no** és `sense_dades`: el deshumidificador
   segueix pel tram i la ventilació per ΔTd queda en suspens.
2. ⚠️ **Urgència amb *Ocupat* o *Impressió*: ventiladors engegats.** La persona o els vapors
   no esperen; és el «tots dos junts» que la v2 ja reserva per a la urgència.
3. ⚠️ **`bloquejat` només quan veta de debò una ventilació.** Amb la v1, un dia fred era
   `bloquejat` de cap a cap i amagava si calia assecar o no; ara les hores de `bloquejat` volen
   dir «hores que hauria ventilat i el fred no ha deixat». I **l'HR de fora i la pluja només
   bloquegen amb la referència *Exterior***: vigilen el sensor de fora, que amb la planta baixa
   no decideix res.
4. **La temperatura interior és la més baixa dels tres punts** (la v1 feia servir el centre):
   el bloqueig per fred mira el racó més fred, i un sensor caigut no deixa la decisió sense
   dades.
5. **La HR màxima és la calibrada**: el màxim de les tres `*_humitat_calibrada`, que és exacte
   per a qualsevol calibratge. *(Fins al 23/09/2026 es deduïa del Td calibrat i de la T de cada
   punt, que només era exacte amb el calibratge de la T a zero → [calibratge.md](calibratge.md).)*
6. **«El millor moment» per renovar s'aproxima per «un moment que no mulla»**
   (`delta_td_higiene`, 0 °C de partida). Sense previsió, és el que es pot saber en viu; les
   dades diran si una regla més fina paga. Si en tot el dia no n'hi ha cap, es ventila igualment
   abans de mitjanit i el deshumidificador ho compensa, com diu la v2.
7. **Les histèresis són fixes, a git**: 5 punts d'HR i 0,5 °C de marge per sortir de la
   urgència, 0,5 °C per a la renovació. Són marges contra l'oscil·lació, no objectius; si les
   dades en demanen d'altres, es converteixen en paràmetres.

## Els paràmetres

Tots sense `initial:` (D7). En **negreta**, els nous. Els valors són **hipòtesis de partida**.

| `input_number.` | Partida | Rang · pas | Què és |
|---|---|---|---|
| **`hr_vall`** · **`hr_pla`** · **`hr_punta`** | 55 · 60 · 65 % | 40–80 · 5 | Llindar del deshumidificador per tram (cost per litre) |
| **`hr_fix`** | 55 % | 40–80 · 5 | Mode *Llindar fix* |
| **`hr_urgencia`** | 70 % | 60–85 · 1 | HR màxima que dispara la urgència |
| **`hr_urgencia_objectiu`** | 50 % | 40–60 · 5 | On asseca la urgència, i s'atura sol |
| **`hr_mentre_ventila`** | 70 % | 50–80 · 5 | El deshumidificador mentre ventila per assecar o renovar |
| `marge_superficie_min` | 3,0 °C | 1,5–5,0 · 0,1 | Marge de paret per sota del qual és urgència (quan hi hagi la sonda de paret: DS18B20 o, a priori, Ecowitt) |
| `delta_td_on` · `delta_td_off` | 2,0 · 0,8 °C | 1–5 · 0–3 | Ventilar per assecar, amb histèresi |
| **`delta_td_higiene`** | 0,0 °C | −3–3 · 0,1 | ΔTd a partir del qual renovar ja no mulla |
| `t_int_minima` | 13 °C | 8–18 · 0,5 | Massa fred per ventilar |
| `hr_ext_bloqueig` | 95 % | 88–100 · 1 | El sensor de fora pot estar mullat (només amb referència *Exterior*) |
| **`renovacions_dia`** · **`renovacions_absencia`** | 3 · 1 | 0–12 · 0,5 | Renovacions d'aire al dia |
| **`cabal_ventiladors`** | 150 m³/h | 20–1000 · 10 | ⏳ **Hipotètic** fins que se sàpiga el real |
| **`volum_soterrani`** | 115 m³ | 50–300 · 5 | ~46 m² per l'alçada; el mateix volum que ja feia servir la v2 |
| `min_on_ventilador` · `min_off_ventilador` | 12 · 10 min | 5–60 · 1 | Fase 3: els relés no repiquen |
| **`ventiladors_max_minuts`** | 120 min | 15–480 · 5 | Fase 3: cap engegada no dura «per sempre» |

**Surten:** `hr_objectiu` (el substitueixen els tres del tram) i `min_off_deshumidificador` (la
v2 no talla mai el compressor; la protecció de 5 min la fa l'aparell, també en arrencar —
experiment 3 de [deshumidificador.md](deshumidificador.md)). El seu històric es queda.

`input_select.referencia_ventilacio`: **Planta baixa** (partida) · Exterior. Es graven sempre
tots dos ΔTd.

## Les fases

Cada fase: un PR, `tools/valida_yaml.py`, `tools/valida_xifres.py`, els tests de
`tools/replica.py` i `check_config` en un contenidor d'un sol ús al servidor, abans d'obrir-lo.
Es desplega **només després de fusionar-lo**: `git pull --ff-only` al servidor i recàrrega.

### Fase 0 — Aquest pla

Documentació: aquest fitxer, la revisió a [decisio-stack.md](decisio-stack.md), els noms nous
a [noms-entitats.md](noms-entitats.md) **abans de crear res**, i els pendents.

### Fase 1 — La decisió v2, en ombra

> ✅ **Codificada el 22/09/2026.** `replica.py`: 106 tests; `--prova-ha`: **3.029 casos** avaluats
> pel HA de debò, els 12 estats coberts, **cap diferència**, motiu inclòs —i amb una histèresi
> canviada a posta en una còpia de la macro, en troba 81—; `check_config` net; i les plantilles
> noves (HR màxima, ΔTd contra la planta baixa, la recollida d'entrades i la targeta del
> tauler), avaluades contra els estats reals sense desplegar res.
>
> 🐛 **I una prova de punta a punta** —un HA d'un sol ús al servidor, sense xarxa, amb aquesta
> configuració i uns sensors de mentida— va trobar el que cap prova per peces no veia: en un HA
> que arrenca **sense estat previ**, la decisió s'avaluava un instant abans que l'inicialitzador
> posés els valors de partida, amb `hr_urgencia` al mínim del rang (60), entrava en urgència i la
> histèresi l'hi mantenia. Ara, fins que els valors de partida hi són, diu `sense_dades`.
> 🚀 **Desplegada el 22/09/2026 a les 12:14** → [registre](home-assistant.md#registre-dinstallació).

**Entra:** `custom_templates/decisio.jinja` · `packages/control.yaml` amb els paràmetres, els
modes i la seva caducitat, `referencia_ventilacio`, els dos interruptors d'actuació (apagats),
l'inicialitzador i la decisió · a `rosada.yaml`, `sensor.dtd_interior_planta_baixa` i
`sensor.soterrani_humitat_maxima`, i en surt el que passa a `control.yaml` ·
`sensor.decisio_llindar_deshumidificador` i `binary_sensor.decisio_ventiladors`, que són la
decisió en forma de gràfic · `sensor.ventilacio_minuts_avui`, els minuts que la decisió
**hauria** ventilat avui · la rèplica v2 a `replica.py`, amb `--prova-ha` i `--deriva` · les
vistes *Ara*, *Històric* i *Ajustos* del tauler.

**Es prova:** els tests de la rèplica, amb els casos límit —HA que arrenca, urgència i la seva
sortida, caps de setmana i festius, cada mode, paràmetres incoherents o sense valor—; i
`replica.py --prova-ha`, que fa avaluar la macro a HA **abans de desplegar-la** (s'envia dins
de la plantilla, sense tocar cap fitxer del servidor) i la compara amb la rèplica cas a cas.

**Es desplega**, en aquest ordre: `homeassistant.reload_custom_templates` →
`input_boolean.reload` → `input_number.reload` → `automation.reload` (l'inicialitzador posa els
valors de partida) → `input_select.reload` (el mode passa a *Òptim*) → `timer.reload` →
`template.reload`.

**🚦 Porta 1:** la decisió porta `versio: v2` i les `entrades`; amb el calibratge encès diu
`calibratge`; cada mode dona el seu estat i la caducitat arrenca i s'atura; **24 h** de
`replica.py --deriva` **sense cap discrepància**; i al registre del deshumidificador **cap
ordre** que no sigui de l'usuari.

### Fase 2 — Dades i gràfics

> ✅ **Codificada el 22/09/2026.** Les entitats del deshumidificador a
> `config/packages/deshumidificador.yaml`, que **només mira i avisa**; la dispersió a
> `rosada.yaml` i els euros per tram a `consum.yaml`. `tools/analisi.py` (tests en verd) ja
> s'ha passat contra les últimes 30 h reals: hi surt el dipòsit tret a mà el 21/09 a les 21:10,
> marcat com a «pocs kWh». I va trobar dues coses: `/api/history` torna **només 24 h** si no
> se li dona el final (`calibratge.py` n'està afectat: pendent a part), i el comptador de
> l'endoll **pot tornar uns Wh enrere** després d'estar no disponible (22/09, 01:06: −22 Wh),
> que s'ha de tractar com a rebot i no com a reinici, igual que ja fa `consum.yaml`.
> 🚀 **Desplegada el 22/09/2026 a les 12:14** → [registre](home-assistant.md#registre-dinstallació).

**Entra**, al local: `sensor.soterrani_dispersio_rosada` · `sensor.deshumidificador_humitat`
(la seva HR, només amb el ventilador en marxa) · `sensor.deshumidificador_estat` (compressor,
ventilador, espera, dipòsit o sense corrent, pels watts) · `binary_sensor.deshumidificador_compressor`
i `sensor.deshumidificador_hores_compressor`, amb el comptador del **filtre** (360 h) i un
script per posar-lo a zero · `sensor.deshumidificador_cost_punta` (i `_pla`, `_vall`) · els
**avisos**: dipòsit ple (codi 32), qualsevol altra avaria (P34 és fuita de refrigerant), i
l'aparell en AUTO o Roba · una vista nova, ***Aprendre***.

**Entra**, a casa: `tools/analisi.py`, contra l'històric, amb el que no cap en una targeta —
vegeu *Què respon cada gràfic*.

**🚦 Porta 2:** les hores de compressor quadren amb les de la sèrie de watts; l'avís del
dipòsit salta en la propera prova; `analisi.py` treu el primer informe amb dades reals.

### Fase 3 — Actuació, apagada per defecte

> ✅ **Codificada el 22/09/2026.** El QUÈ dels executors també és en macros
> (`config/custom_templates/executors.jinja`): quines ordres enviar al deshumidificador i en
> quin ordre, quan no es pot actuar, i què fer amb els ventiladors. Tenen rèplica i
> **`--prova-ha` les compara amb HA: 2.000 casos, cap diferència** (i la decisió, els 3.029 de
> sempre). Els relés són a `config/custom_templates/ventiladors.jinja`, l'únic lloc que diu
> quins són. Contra l'aparell de debò, sense actuar: per portar-lo de *Manual · 35 · alta* a
> *Manual · 55 · alta*, enviaria **una sola ordre**, el llindar. `check_config` net.
> 🚀 **Desplegada el 22/09/2026 a les 12:14, amb els dos interruptors apagats**
> → [registre](home-assistant.md#registre-dinstallació).
>
> 🔧 *De pas, un canvi a la Fase 1:* els valors de partida van **per versions**
> (`input_number.parametres_versio`), no amb una marca de sí o no. Amb la marca, el
> `ventiladors_max_minuts` d'aquesta fase no hauria rebut mai el seu valor i s'hauria quedat
> al mínim del rang (15 min).

**Entra:** la **interfície dels ventiladors** (`ventiladors.jinja`, dos relés virtuals,
`binary_sensor.ventiladors_en_marxa`, `sensor.ventiladors_potencia`, `script.ventiladors_engega`
i `_atura`) · l'executor dels ventiladors, amb `min_on_ventilador`, `min_off_ventilador` i
`ventiladors_max_minuts` · `script.deshumidificador_aplica`, que porta l'aparell a la
configuració que diu la decisió en l'**ordre que ensenyen els experiments** —engegat, operació,
Manual si cal, llindar, velocitat, mode final—, **només amb les ordres que calen** (cada una és un
xiulet) i **comprovant i repetint** cada pas · l'executor del deshumidificador, que el crida quan
canvia la decisió, quan arrenca HA, **quan l'aparell torna del corrent** (els watts de l'endoll,
no `tuya-local`) i cada 15 minuts si algú l'ha tocat · el comptador de minuts de ventilació, que
passa a comptar els relés quan l'actuació és encesa.

**Es prova:** a la rèplica, `ordres()` (quines ordres enviaria) i `accio_ventiladors()`, amb
l'aparell que torna amb la **configuració de fàbrica**, en **AUTO**, en Roba i purificant, amb
el **dipòsit ple**, i els ventiladors després d'un reinici. Després, amb els **relés virtuals** i
`actuacio_ventiladors` encès, 24 h; i amb l'usuari al davant, `actuacio_deshumidificador` unes
hores, comptant xiulets.

**🚦 Porta 3 — la Porta C de [fases.md](fases.md), adaptada:** els relés virtuals segueixen la
decisió sense repicar; els temps mínims es respecten després de reiniciar HA; amb un sensor
desconnectat els ventiladors s'aturen; **l'aparell desendollat torna amb la de fàbrica i HA li
torna a posar la bona en menys de 5 minuts**; posat en AUTO des de l'app, HA avisa i el torna a
Manual; cap engegada de ventiladors passa de `ventiladors_max_minuts`.

### Fase 4 — El segon nivell (quan hi hagi la dada)

La correcció del racó dolent de [logica-v2.md](logica-v2.md#el-segon-nivell-la-correcció-del-racó-dolent):
baixar un esglaó si el pitjor racó fa més de `correccio_minuts` per sobre de l'objectiu + 2
punts, tornar a pujar amb −2 punts durant 60 min, mai per sota del 50 % ni per sobre del tram.
**No es codifica fins que se sàpiga la desviació de l'higròmetre de l'aparell** contra un Tapo
calibrat ([pendents.md](../pendents.md)): sense ella, la correcció corregiria l'error del sensor.
L'estat (esglaó i des de quan) anirà als atributs de la decisió, que es restauren en arrencar.

### Fase 5 — Els S110E

1. Instal·lar-los (instal·lador autoritzat si els ventiladors van cablejats), emparellar-los
   **per Matter** i renombrar-los **abans que gravin res**: `switch.ventilador_1` i `_2`,
   `sensor.ventilador_1_potencia` i `_2`.
2. Comportament d'arrencada **apagat** (tasca C.6), i el **temporitzador propi** si en tenen.
3. A `ventiladors.jinja`, canviar els dos relés virtuals pels de debò i posar-hi les
   potències. `reload_custom_templates` + `template.reload`. **És l'únic canvi de codi.**
4. Descomentar els `history_stats` dels ventiladors de `rosada.yaml` (`history_stats.reload`).

## Què respon cada gràfic

| Pregunta | Objectiu | On |
|---|---|---|
| Ara mateix, què faria i per què? | tots | *Ara*: estat, motiu, llindar, ventiladors, mode |
| El pitjor racó, contra el llindar que li toca | humitats | *Històric*: `soterrani_humitat_maxima` i `decisio_llindar_deshumidificador` al mateix eix (%) |
| Contra què s'ha de comparar per ventilar? | consum | *Històric*: els dos ΔTd junts · casa: `analisi.py ventilacio` (quin dels dos prediu millor com baixa el Td quan es ventila) |
| Quant ventila, i quant hauria ventilat? | aire | *Aprendre*: minuts per dia · la decisió en ombra els compta |
| Quina part del consum cau en punta, en kWh i en € | consum | *Consum* i *Aprendre*: per dia i tram |
| Quantes hores de compressor, i quan toca el filtre | consum | *Aprendre* |
| Quants litres per kWh, i a quin cost per litre | consum | casa: `analisi.py diposits` (un dipòsit ple = codi 32; els litres, mesurats) |
| Quant aguanta la sequedat després d'aturar | consum | casa: `analisi.py rebot` (la corba de la HR després de cada aturada del compressor) |
| Asseca de debò cada ventilació? | humitats | casa: `analisi.py ventilacio` (eficàcia de cada episodi, °C de Td per hora) |
| La humitat és general o d'un racó? | humitats | *Aprendre*: dispersió · casa: `analisi.py dispersio` (quin punt és el pitjor, i quanta estona) |
| La paret, quant marge té? | humitats | *Aprendre*: marge contra els 3 °C · casa: hores per sota |
| L'higròmetre de l'aparell, s'hi pot confiar? | tots | *Aprendre*: la seva HR contra la dels Tapo |

## Quan es desplega cada cosa — el trasllat

- **Fases 1 i 2 no toquen cap aparell**: es poden desplegar abans o després del trasllat del
  23–24/09. Abans és millor: la sèrie del local comença ja amb la v2. **Mai** mentre corri la
  prova del dipòsit o el calibratge no hagi acabat, i sense reiniciar HA.
- **Fase 3**, després del trasllat: primer desplegada amb **tot apagat**; la **setmana de base**
  en mode *Llindar fix* amb `actuacio_deshumidificador` encès; després, *Òptim*.
- Els **ventiladors** no s'actuen fins a la Fase 5; fins llavors, els relés virtuals.

## Fora d'aquest pla

- **L'endoll de la impressora**, perquè *Impressió* s'engegui sola pel consum.
- **Un sensor de CO₂** (SCD40): renovació per demanda en comptes de per rellotge.
- **Mesurar l'aigua al soterrani**, on amb la bomba no hi ha codi 32: pluviòmetre de balancí o
  les glopades de la bomba als watts ([pendents.md](../pendents.md)).
- **La previsió** (R3): quan es gravi, «el millor moment» per renovar pot mirar endavant.
- **Remenar l'aire** amb el ventilador del deshumidificador quan la dispersió és gran:
  primer cal veure la dispersió real (Fase 2).
