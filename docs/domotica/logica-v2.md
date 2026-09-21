# Lògica de control v2 — deshumidificador i ventilació

> **Estat: proposta (21/09/2026), no decidida ni codificada.** Surt d'una conversa amb
> l'usuari després dels experiments amb el deshumidificador ([deshumidificador.md](deshumidificador.md)),
> i d'una revisió feta el mateix vespre des de la física i el càlcul (vegeu *La revisió*, al
> final). Quan es decideixi, [decisio-stack.md](decisio-stack.md) hi apuntarà i es codificarà a
> `config/packages/rosada.yaml`, amb la rèplica de [`tools/replica.py`](../../tools/replica.py)
> al costat.
>
> **Què canvia respecte del que hi ha avui** (la Fase B de `rosada.yaml`, que només registra):
>
> 1. **L'aire amb què es compara es tria amb un paràmetre: la planta baixa o l'exterior**
>    (vegeu *Per on entra l'aire*). Es graven tots dos, per saber amb dades quin encerta.
> 2. **El llindar del deshumidificador depèn del tram de la tarifa**, triat pel **cost per
>    litre** i no pel preu del kWh, amb una urgència que passa per davant del preu.
> 3. **Estats nous:** `urgencia`, `higiene`, `impressio`, `ocupat`.
> 4. **Cap estat on HA deixi els aparells pot ser perillós si HA cau en aquell moment.**
> 5. **Els ventiladors s'engeguen quan convé** —quan l'aire de dalt asseca, per renovar l'aire,
>    per impressió o per ocupació—, no en règim continu.

## Els tres objectius, i en quin ordre manen

1. **Evitar humitats** —fong, cartró que es deforma, condensació—. Mana sempre: és la urgència.
2. **Renovar l'aire** —olors, vapors de la resina, CO₂ si hi ha algú—. Un mínim diari que no es
   negocia per preu, però que es fa al moment menys car.
3. **Minimitzar el consum** —quan i amb quin aparell es treu cada litre d'aigua—. Decideix tot
   el que els dos primers deixen lliure.

## El soterrani, tal com serà

| | |
|---|---|
| **Què hi haurà** | Jocs de taula (cartró i paper), un llit d'ús ocasional i, en una altra estança, impressores 3D de resina i de filament, d'ús molt esporàdic |
| **Ventilació** | Dos sistemes que **extreuen** aire. Models, potència i cabal: ⏳ pendents d'inventariar |
| **Per on entra l'aire** | Per **l'escala que puja a la planta baixa**. Les finestres, tancades: no es poden governar |
| **Deshumidificador** | Qlima D 825 PA Smart: llindar per `tuya-local`, watts pel P110M. Com es comporta, a [deshumidificador.md](deshumidificador.md) |

## Els principis

1. **Es compara punt de rosada, mai HR.** La HR depèn de la temperatura; el punt de rosada diu
   quanta aigua porta l'aire. A l'hivern, un aire de fora al 85 % pot assecar un soterrani al
   65 %; a l'estiu, un aire al 60 % el pot mullar i condensar. El raonament sencer, a
   [control-punt-rosada.md](control-punt-rosada.md#per-què-punt-de-rosada-i-no-humitat-relativa).
2. **El risc és la paret, no l'aire.** El fong creix on l'aire humit toca una superfície freda:
   un 62 % a 18 °C amb la paret a 13 °C són un **85 %** a tocar de la paret. Per això la urgència
   mira la paret (quan hi hagi els DS18B20) o, mentrestant, la **HR més alta** dels tres punts.
3. **El deshumidificador escalfa**: ~360 W elèctrics més ~200 W de la condensació (0,3 L/h). Part
   de la HR que baixa és per l'escalfor, no perquè hi hagi menys aigua. Per això el que es vigila
   és el punt de rosada i el marge de la paret, mai només la HR de l'aire.
4. **Per decidir quan assecar, compta el cost per litre, no el preu del kWh.** Un
   deshumidificador treu menys aigua per kWh com més sec és l'aire: la bateria freda només en
   condensa la part que està per sobre de la seva pròpia saturació. Vegeu *Per què aquests
   llindars*.
5. **Un sol punt de decisió.** Tot surt de `sensor.decisio_del_soterrani`; els automatismes
   només l'executen. Com fins ara.
6. **Fallada segura.** Cada estat en què HA deixi un aparell ha de ser acceptable si HA
   desapareix just aleshores, i **res no pot quedar «per sempre»**: el deshumidificador no
   s'apaga mai (se li puja el llindar) ni queda en continu (se li posa un llindar que s'atura
   sol), i els ventiladors han de poder apagar-se sols.
7. **Dos nivells.** L'aparell regula el llindar que li donem, amb el seu higròmetre. HA vigila
   **el pitjor racó** amb els sensors calibrats i, si cal, li mou el llindar.
8. **Primer paràmetres, després números.** Tots els llindars són `input_number` que es toquen
   des de la interfície. Els valors d'aquí són **hipòtesis de partida**, i la mateixa lògica
   genera cada dia les dades per corregir-les.

## Per què aquests llindars — el cost per litre

L'aigua que un deshumidificador pot treure de cada kg d'aire és la diferència entre la que
porta l'aire i la que cap a la temperatura de la bateria freda. Amb l'aire a 20 °C i la bateria
a ~6 °C (a 14 °C i ~2 °C a l'hivern), i els preus amb impostos de
[subministraments.md](../local/subministraments.md):

| Tram · llindar | Aigua per kg d'aire (relativa al 65 %) | **€ per litre, relatiu a «punta al 65 %»** | A l'hivern (14 °C) |
|---|---|---|---|
| Vall al **50 %** | 0,40 | **1,02** | 1,46 |
| Vall al **55 %** | 0,60 | **0,68** | 0,78 |
| Vall al **60 %** | 0,80 | 0,51 | — |
| Pla al **55 %** | 0,60 | **1,00** | — |
| Pla al **60 %** | 0,80 | **0,75** | 0,79 |
| Punta al **65 %** | 1,00 | **1,00** | 1,00 |

Dues conseqüències que corregeixen la primera versió d'aquesta proposta:

- **Pre-assecar al 50 % en vall no estalvia res.** Cada litre tret al 50 % costa el mateix que un
  litre tret en punta al 65 %, i a l'hivern un 46 % més. El descompte de la vall (2,47 vegades
  més barata) se l'endú la pèrdua de rendiment. L'única cosa que podria justificar-lo és que
  les parets i el cartró guardin la sequedat, però l'aire en guarda molt poc: passar el
  soterrani del 60 al 50 % són **0,18 L**.
- **En pla, el 55 % costa el mateix que la punta.** Al 60 % ja és un 25 % més barat.

I a l'hivern la corba és més dreta, o sigui que tot això hi pesa encara més.

> ⚠️ Són estimacions del model físic de la bateria, no mesures d'aquest aparell. La primera
> mesura de litres per kWh (la nit amb el dipòsit) les ha de confirmar.

## Per on entra l'aire — i per què canvia el criteri

Els ventiladors extreuen i l'aire de reposició **baixa per l'escala**. L'aire que entra al
soterrani, doncs, hauria de ser **el de la planta baixa**, no el de fora. Però no ho sabem del cert,
i per això **la referència és un paràmetre**:

> **ΔTd = Td del soterrani (el punt més humit) − Td de la referència**
>
> `input_select.referencia_ventilacio`: **Planta baixa** (proposta de partida) · **Exterior**

- **Es graven sempre tots dos ΔTd**, contra la planta baixa i contra l'exterior, triï el paràmetre
  el que triï. Com que el Td del soterrani es mou quan es ventila, amb unes setmanes de dades es
  podrà dir **quin dels dos prediu millor quan ventilar asseca de debò**, i canviar el paràmetre
  sense tocar codi.
- La planta baixa segueix l'exterior amb retard, i ella mateixa es renova amb aire de fora. Si
  s'hi engeguen els splits, a l'estiu hi asseca l'aire que després baixarà: una ajuda que té cost.
- Extreure deixa el soterrani en depressió, i **una part de l'aire pot entrar per les esquerdes
  del terra**. És la **prova de fum** (tasca 0.1 de [fases.md](fases.md)), que segueix sent la
  més important: si hi entra aire del terreny, ventilar pot mullar.
- ❓ **Si la porta de l'escala va oberta o tancada** canvia molt el cabal. Pendent de saber.

**Quant asseca ventilar.** Amb un cabal de 150 m³/h (hipotètic fins que se sàpiga el real), un
ΔTd de **2 °C** són ~1 g d'aigua per kg d'aire, o sigui **~0,19 L/h**; un ΔTd de **0,8 °C**, ~0,08
L/h. Si els ventiladors gasten ~100 W, són **~1,9 L/kWh** i **~0,8 L/kWh**. Com que a cada moment
els dos aparells paguen el mateix preu, **el que decideix quin surt a compte és només qui treu
més litres per kWh**. Els llindars de ΔTd són una aproximació d'això mentre no se sàpiguen el
cabal i els litres per kWh del deshumidificador; quan se sàpiguen, s'han de reescriure en aquests
termes.

⚠️ Els llindars 2,0 / 0,8 °C venen de l'error dels sensors contra el de **fora** (models barrejats).
Contra la planta baixa, i un cop calibrats, probablement es poden baixar.

## Els estats, per ordre de prioritat

El primer que es compleix, mana.

| # | Estat | Quan | Deshumidificador | Ventiladors |
|---|---|---|---|---|
| 1 | `calibratge` · `sense_dades` | Com ara | No es toca | No es toquen |
| 2 | **`urgencia`** | **HR més alta dels tres punts** ≥ `hr_urgencia` (70 %), o marge de paret < `marge_urgencia` (3,0 °C, ≈ 82 % a la paret) | Llindar **`hr_urgencia_objectiu`** (50 %), sigui quin sigui el preu. S'atura sol en arribar-hi | Només si l'aire de dalt asseca (ΔTd ≥ `delta_td_on`) |
| 3 | **`ocupat`** | A mà (`input_boolean`): algú hi dorm o hi treballa | Mode **Nit** (silenciós), al llindar del tram | **Engegats** mentre duri: una persona fa ~20 L/h de CO₂ i ~40 g/h d'aigua, i demana ~25–30 m³/h |
| 4 | **`impressio`** | A mà, o l'endoll de la impressora marca consum | Segons el tram | **Engegats**, i `impressio_despres` (60 min) més |
| 5 | `bloquejat` | Massa fred a dins (< `t_int_minima`) | Segons el tram | **Aturats** |
| 6 | `ventilar` | ΔTd ≥ `delta_td_on` (2,0 °C), amb histèresi fins a `delta_td_off` (0,8 °C) | **`hr_mentre_ventila` (70 %)**, no apagat | **Engegats** |
| 7 | **`higiene`** | Falten renovacions d'aire avui (`renovacions_dia`) i ara és **un dels millors moments** | `hr_mentre_ventila` | **Engegats** |
| 8 | `deshumidificar` | El pitjor racó per sobre de l'objectiu del tram | **Llindar del tram** | Aturats |
| 9 | `repos` | Tot a l'objectiu | Llindar del tram | Aturats |

⚠️ **`impressio` passa per davant de `bloquejat`**, a posta: els vapors de la resina són salut. A
l'hivern vol dir ventilar aire fred, que refreda les parets. La solució bona és una **extracció
local** a la impressora (una caixa amb sortida), perquè la resta del soterrani no es refredi.

### El llindar del deshumidificador, per tram

| Tram | Hores | Llindar inicial | Paràmetre |
|---|---|---|---|
| **Vall** | 00–08 entre setmana; **caps de setmana i festius sencers** | **55 %** | `hr_vall` |
| **Pla** | 08–10 · 14–18 · 22–24 | **60 %** | `hr_pla` |
| **Punta** | 10–14 · 18–22 | **65 %** | `hr_punta` |

- Són els valors que surten del cost per litre (a dalt). **El pre-assecat al 50 % queda com a
  experiment**, que és com es va proposar: dues setmanes amb `hr_vall` al 50 % per mesurar quant
  costa i **quantes hores aguanta** la sequedat; si les parets no la guarden, es torna al 55 %.
- Per al cartró, l'ideal és el 45–55 % estable, i el fong vol dies per sobre del 70–80 % a la
  superfície. Un dia que oscil·la entre el 55 de nit i el 65 de les puntes és acceptable, sempre
  amb la urgència al darrere. Si els jocs importen més que els cèntims, `hr_pla` al 55 % **no
  costa més que la punta**: només deixa d'estalviar.
- El tram el dona `sensor.tarifa_periode`, que ja coneix els caps de setmana i els festius.
- ⚠️ L'aparell només accepta **esglaons de 5 %** (40–80 i «CO»). Els paràmetres, de 5 en 5.
- ⚠️ **Mode Manual** (o Nit si hi ha algú). En AUTO o Roba l'aparell no fa cas del llindar
  ([deshumidificador.md](deshumidificador.md)). Si algú el canvia, HA avisa i el torna a Manual.
- **Velocitat alta per defecte quan asseca**: amb el compressor en marxa hi suma ~7 W. Més cabal
  vol dir una bateria una mica menys freda —menys aigua per kg, però molts més kg—, i
  normalment surt més aigua; a l'hivern, a més, allunya el glaç. **A confirmar en litres.**
- **Les ordres, poques**: en canviar de tram i en corregir. Cada ordre fa un xiulet.

### El segon nivell: la correcció del racó dolent

L'aparell mira el seu higròmetre; HA mira els tres punts calibrats. Si no coincideixen, HA mou
el llindar. Com que el llindar va de 5 en 5 i el soterrani respon a poc a poc, la correcció ha
de tenir **banda morta i límits**, o es posaria a oscil·lar:

- **Baixa un esglaó** si el pitjor racó fa més de `correccio_minuts` (30) per sobre de l'objectiu
  del tram **+ 2 punts**.
- **Torna a pujar** si fa més de 60 min per sota de l'objectiu **− 2 punts**.
- **Mai per sota de 50 %** ni per sobre del llindar del tram.
- I cal saber **la desviació del seu higròmetre**: un dia amb un Tapo al costat, com el calibratge.

### La ventilació

- **Mitjà preferent quan treu més litres per kWh** que el deshumidificador (vegeu *Quant asseca
  ventilar*). Mentre ventilen, el deshumidificador **no s'apaga, però es posa al 70 %**, el mateix
  llindar que la urgència. **Per què no al 65:** si el soterrani està per sobre del llindar, el
  deshumidificador treballaria alhora, assecant un aire que els ventiladors treuen enfora, i a
  més reduiria la diferència d'aigua que fa treballar la ventilació. **Només treballen tots dos
  junts quan és urgent**, que és quan la rapidesa val més que l'eficiència.
- **Renovar l'aire, en renovacions, no en minuts.** `renovacions_dia` (proposta de partida: **3**)
  es converteix en minuts amb el cabal real dels ventiladors. Com a ordre de magnitud: a 150
  m³/h, **30 minuts són 0,65 renovacions al dia** —ni una—, molt per sota del que es fa servir
  per a un espai tancat (de l'ordre de 0,2–0,5 renovacions per hora). Es reparteixen en **els
  moments del dia amb el ΔTd més alt**, que són els que menys mullen, o fins i tot assequen.
  Si cap moment del dia asseca, es ventila igualment i el deshumidificador ho compensa.
- **Un sensor de CO₂** (l'SCD40 que ja preveia [control-punt-rosada.md](control-punt-rosada.md#sensors))
  faria que la renovació fos per demanda i no per rellotge, sobretot amb el llit i les
  impressores.
- **Remenar no és renovar**: el ventilador del deshumidificador sol (15–48 W) trenca els racons
  estancats però no treu aigua ni renova. Queda com a idea per si els tres punts divergeixen.

## Fallada segura: què passa si HA cau en cada estat

| Si HA cau en… | El deshumidificador queda | Els ventiladors queden | Acceptable? |
|---|---|---|---|
| `repos` · `deshumidificar` | Regulant sol al llindar del tram | Aturats | ✅ |
| `ventilar` · `higiene` · `impressio` · `ocupat` | Regulant sol al **70 %** | ⚠️ **Engegats** | ✅ **només si s'apaguen sols** → temporitzador al relé S110E (❓ a comprovar si en té) |
| `urgencia` | Al **50 %**: asseca fins allà i **s'atura sol** | — | ✅ |

I, en arrencar, HA **torna a posar el llindar del tram i Manual**, per si l'aparell s'ha quedat
en un estat vell.

## Què aprèn cada dia — les dades que ajusten els paràmetres

Sense afegir cap experiment: la mateixa lògica deixa les mesures.

| Pregunta | D'on surt | Ajusta |
|---|---|---|
| **Quanta aigua treu per kWh, i com cau amb l'HR?** | L'hora del codi 32 (dipòsit ple, 3,8 L) i els kWh fins llavors, **a partir del segon dipòsit** (el primer també omple la safata); al soterrani, amb la bomba, cal una altra via | Els tres llindars: és la dada que confirma la taula del cost per litre |
| **Aguanta la sequedat el pre-assecat?** | Les dues setmanes d'experiment al 50 %: hores fins a tornar al llindar de pla | Si `hr_vall` es queda al 55 % |
| **Asseca de debò la ventilació?** | Com baixa el Td del soterrani per hora de ventiladors, amb el ΔTd que hi havia | `delta_td_on` / `delta_td_off` |
| **Contra què s'ha de comparar?** | Quin dels dos ΔTd gravats s'assembla més al que baixa el Td del soterrani quan es ventila | `referencia_ventilacio` |
| **El racó dolent segueix l'aparell?** | Quantes correccions fa el segon nivell, i de quant | La banda morta i `correccio_minuts` |

## Mètode

1. **Una setmana de base al soterrani** amb el deshumidificador fix al 55 % i els ventiladors com
   ara. Sense base no es pot dir quant estalvia la v2.
2. **A casa es poden mesurar els costos, no el rebot**: les hores que aguanta la sequedat depenen
   de les parets del soterrani.
3. **Tot per PR**, amb la rèplica offline: cada canvi de llindar o d'estat es prova contra
   l'històric abans de desplegar.

## El que falta per tancar-la

- ❓ **Models, potència i cabal dels ventiladors** (l'usuari en té fotos). Sense el cabal no es
  poden convertir ni les renovacions en minuts ni el ΔTd en litres per kWh.
- ❓ **La porta de l'escala**: oberta o tancada, habitualment.
- ❓ **Si els S110E tenen temporitzador propi** (apagada automàtica), per a la fallada segura.
- ⏳ **Els DS18B20 de paret** (B.2), perquè la urgència miri la paret i no només l'aire.
- ⏳ **La prova de fum** (0.1): si l'aire entra pel terra, la ventilació es reconsidera sencera.
- 📌 **Filament en caixes estanques amb dessecant**, faci el que faci el soterrani: a un 55 %
  ja agafa massa humitat.

## La revisió — el que es va corregir (21/09/2026)

Revisada des de la física i el càlcul contra els tres objectius. El que va canviar respecte de
la primera versió, i per què:

| Primera versió | Corregit | Per què |
|---|---|---|
| Vall 50 · pla 55 · punta 65 | **Vall 55 · pla 60 · punta 65**, i el 50 com a experiment | Cost per litre: al 50 % en vall costa com la punta; al 55 % en pla, també |
| Mentre ventila, deshumidificador al 65 % | **Al 70 %** | Al 65 treballarien junts sovint, i el deshumidificador assecaria aire que se'n va |
| Urgència en continu | **Al 50 %**, s'atura sol | Fallada segura: res «per sempre» si HA cau |
| Urgència si «el pitjor racó» ≥ 70 % | **La HR més alta dels tres**, i marge de paret **3,0 °C** | El pitjor racó per punt de rosada no és el pitjor per HR; 3,0 °C és el marge que ja fa servir `rosada.yaml` (≈ 82 % a la paret) |
| Higiene: 30 min al dia | **Renovacions al dia** (3 de partida) | 30 min a 150 m³/h no arriben a una renovació diària |
| Ocupat: llindar de pla | **Mode Nit** i ventilació contínua | El que demana una persona dormint és silenci i aire, no un llindar |
| Correcció del racó sense límits | **Banda morta de ±2 punts** i límits | Esglaons de 5 % i un procés lent oscil·larien |
| «Velocitat alta quan asseca» | **Per defecte alta, a confirmar en litres** | Més cabal refreda menys la bateria: no sempre treu més aigua |
