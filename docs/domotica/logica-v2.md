# Lògica de control v2 — deshumidificador i ventilació

> **Estat: proposta (21/09/2026), no decidida ni codificada.** Surt d'una conversa amb
> l'usuari després dels experiments amb el deshumidificador ([deshumidificador.md](deshumidificador.md)).
> Quan es decideixi, [decisio-stack.md](decisio-stack.md) hi apuntarà i es codificarà a
> `config/packages/rosada.yaml`, amb la rèplica de [`tools/replica.py`](../../tools/replica.py)
> al costat.
>
> **Què canvia respecte del que hi ha avui** (la Fase B de `rosada.yaml`, que només registra):
>
> 1. **L'aire amb què es compara es tria amb un paràmetre: la planta baixa o l'exterior**
>    (vegeu *Per on entra l'aire*). Es graven tots dos, per saber amb dades quin encerta.
> 2. **El llindar del deshumidificador depèn del tram de la tarifa**, amb una urgència que passa
>    per davant del preu.
> 3. **Estats nous:** `urgencia`, `higiene`, `impressio`, `ocupat`.
> 4. **Cap estat on HA deixi els aparells pot ser perillós si HA cau en aquell moment.**
> 5. **Els ventiladors s'engeguen quan convé** —quan l'aire de dalt asseca, per higiene, per
>    impressió o per ocupació—, no en règim continu.

## El soterrani, tal com serà

| | |
|---|---|
| **Què hi haurà** | Jocs de taula (cartró i paper), un llit d'ús ocasional i, en una altra estança, impressores 3D de resina i de filament, d'ús molt esporàdic |
| **Ventilació** | Dos sistemes que **extreuen** aire. Models i cabal: ⏳ pendents d'inventariar |
| **Per on entra l'aire** | Per **l'escala que puja a la planta baixa**. Les finestres, tancades: no es poden governar |
| **Deshumidificador** | Qlima D 825 PA Smart: llindar per `tuya-local`, watts pel P110M. Com es comporta, a [deshumidificador.md](deshumidificador.md) |

## Els principis — el que la conversa va deixar clar

1. **Es compara punt de rosada, mai HR.** La HR depèn de la temperatura; el punt de rosada diu
   quanta aigua porta l'aire. A l'hivern, un aire de fora al 85 % pot assecar un soterrani al
   65 %; a l'estiu, un aire al 60 % el pot mullar i condensar. El raonament sencer, a
   [control-punt-rosada.md](control-punt-rosada.md#per-què-punt-de-rosada-i-no-humitat-relativa).
2. **El risc és la paret, no l'aire.** El fong creix on l'aire humit toca una superfície freda:
   un 62 % a 18 °C amb la paret a 13 °C són un ~85 % a tocar de la paret. Per això hi ha una
   **urgència que no mira el preu**, lligada al marge de condensació (quan hi hagi els DS18B20)
   o, mentrestant, a l'HR del pitjor racó.
3. **Un sol punt de decisió.** Tot surt de `sensor.decisio_del_soterrani`; els automatismes
   només l'executen. Com fins ara.
4. **Fallada segura.** Cada estat en què HA deixi un aparell ha de ser acceptable si HA
   desapareix just aleshores. D'aquí surten dues regles: el deshumidificador **no s'apaga mai**
   (se li puja el llindar), i els ventiladors han de poder **apagar-se sols**.
5. **Dos nivells.** L'aparell regula el llindar que li donem, amb el seu higròmetre. HA vigila
   **el pitjor racó** amb els sensors calibrats i, si cal, li mou el llindar. Així el racó dolent
   mana, però si HA cau l'aparell segueix regulant.
6. **Primer paràmetres, després números.** Tots els llindars són `input_number` que es toquen
   des de la interfície. Els valors d'aquí són **hipòtesis de partida**, i la mateixa lògica
   genera cada dia les dades per corregir-les.

## Per on entra l'aire — i per què canvia el criteri

Els ventiladors extreuen i l'aire de reposició **baixa per l'escala**. L'aire que entra al
soterrani, doncs, hauria de ser **el de la planta baixa**, no el de fora. Però no ho sabem del cert,
i per això **la referència és un paràmetre**:

> **ΔTd = Td del soterrani (el pitjor racó) − Td de la referència**
>
> `input_select.referencia_ventilacio`: **Planta baixa** (proposta de partida) · **Exterior**

- **Es graven sempre tots dos ΔTd**, contra la planta baixa i contra l'exterior, triï el paràmetre
  el que triï. Com que el Td del soterrani es mou quan es ventila, amb unes setmanes de dades es
  podrà dir **quin dels dos prediu millor quan ventilar asseca de debò**, i canviar el paràmetre
  sense tocar codi.

- La planta baixa segueix l'exterior amb retard. Si s'hi engeguen els splits, a l'estiu hi
  asseca l'aire que després baixarà: una ajuda que té cost.
- Extreure deixa el soterrani en depressió, i **una part de l'aire pot entrar per les esquerdes
  del terra**. És la **prova de fum** (tasca 0.1 de [fases.md](fases.md)), que segueix sent la
  més important: si hi entra aire del terreny, ventilar pot mullar.
- ❓ **Si la porta de l'escala va oberta o tancada** canvia molt el cabal. Pendent de saber.
- El sensor de fora continua servint: diu cap on anirà la planta baixa, i és la referència
  contra l'estació oficial.

## Els estats, per ordre de prioritat

El primer que es compleix, mana.

| # | Estat | Quan | Deshumidificador | Ventiladors |
|---|---|---|---|---|
| 1 | `calibratge` · `sense_dades` | Com ara | No es toca | No es toquen |
| 2 | **`urgencia`** | Pitjor racó ≥ `hr_urgencia` (70 %) o marge de paret < `marge_urgencia` (2,5 °C) | **Continu**, sigui quin sigui el preu | Només si l'aire de dalt asseca |
| 3 | **`ocupat`** | A mà (`input_boolean`): algú hi dorm o hi treballa | Llindar de **pla** encara que sigui vall | Al mínim que calgui per a l'aire |
| 4 | **`impressio`** | A mà, o l'endoll de la impressora marca consum | Segons el tram | **Engegats**, i `impressio_despres` (60 min) més |
| 5 | `bloquejat` | Massa fred a dins (< `t_int_minima`) | Segons el tram | **Aturats** |
| 6 | `ventilar` | ΔTd (contra la referència triada) ≥ `delta_td_on` (2,0 °C), amb histèresi fins a `delta_td_off` (0,8 °C) | **`hr_mentre_ventila`** (65 %), no apagat | **Engegats** |
| 7 | **`higiene`** | Encara no s'ha ventilat `higiene_minuts` (30) avui, i ara és **el millor moment** | `hr_mentre_ventila` | **Engegats** |
| 8 | `deshumidificar` | El pitjor racó per sobre de l'objectiu del tram | **Llindar del tram** | Aturats |
| 9 | `repos` | Tot a l'objectiu | Llindar del tram | Aturats |

### El llindar del deshumidificador, per tram

| Tram | Hores | Llindar inicial | Paràmetre |
|---|---|---|---|
| **Vall** | 00–08 entre setmana; **caps de setmana i festius sencers** | **50 %** | `hr_vall` |
| **Pla** | 08–10 · 14–18 · 22–24 | **55 %** | `hr_pla` |
| **Punta** | 10–14 · 18–22 | **65 %** | `hr_punta` |

- El tram el dona `sensor.tarifa_periode`, que ja coneix els caps de setmana i els festius.
- **El 50 % en vall és el pre-assecat, i és un experiment en si mateix**: vegeu *Què aprèn cada
  dia*. Si surt car o no aguanta, es puja.
- El 14–18 és el **forat entre puntes**: en pla, a 0,139 €/kWh, un 60 % del preu de punta.
- ⚠️ L'aparell només accepta **esglaons de 5 %** (40–80 i «CO»). Els paràmetres, doncs, de 5 en 5.
- ⚠️ **Mode Manual sempre.** En AUTO o Roba l'aparell no fa cas del llindar
  ([deshumidificador.md](deshumidificador.md)). Si algú el canvia, HA avisa i el torna a Manual.
- **Velocitat alta quan asseca**: amb el compressor en marxa hi suma ~7 W i mou molt més aire.
- **La correcció del racó dolent:** si el pitjor racó fa més de `correccio_minuts` (30) per
  sobre de l'objectiu del tram, HA baixa el llindar un esglaó (fins a `hr_vall`); quan torna a
  l'objectiu, el retorna. És el segon nivell del principi 5.
- **Les ordres, poques**: en canviar de tram i en corregir. Cada ordre fa un xiulet.

### La ventilació

- **Mitjà preferent quan asseca**: els ventiladors gasten 30–150 W contra els ~360 W del
  compressor. Mentre ventilen, el deshumidificador **no s'apaga**: es posa al 65 % i només
  entra si la ventilació no aguanta.
- **Higiene: 30 min al dia al millor moment.** «Millor» vol dir quan l'aire de dalt és més sec
  respecte del soterrani (el ΔTd més alt de la finestra). Si cap moment del dia asseca, es
  ventila igualment al menys dolent, i el deshumidificador ho compensa.
- **Impressió**: la resina fa vapors. Ventilar durant i una hora després, faci l'aire el que faci.
  *(A més, la resina imprimeix malament per sota de ~20 °C, i el soterrani a l'hivern serà a
  12–15 °C: la impressora necessitarà escalfor pròpia.)*
- **Remenar no és ventilar**: el ventilador del deshumidificador sol (15–48 W) trenca els racons
  estancats però no treu aigua. Queda com a idea per si els tres punts del soterrani divergeixen.

## Fallada segura: què passa si HA cau en cada estat

| Si HA cau en… | El deshumidificador queda | Els ventiladors queden | Acceptable? |
|---|---|---|---|
| `repos` · `deshumidificar` | Regulant sol al llindar del tram | Aturats | ✅ |
| `ventilar` · `higiene` · `impressio` | Regulant sol al **65 %** | ⚠️ **Engegats** | ✅ **només si s'apaguen sols** → temporitzador al relé S110E (❓ a comprovar si en té) |
| `urgencia` | **En continu** fins que algú el toqui | — | ⚠️ Assecant sense parar: no fa mal, però paga punta |
| El 50 % de vall | Al 50 % | Aturats | ✅ Assecant una mica massa, res més |

I, en arrencar, HA **torna a posar el llindar del tram i Manual**, per si l'aparell s'ha quedat
en un estat vell.

## Què aprèn cada dia — les dades que ajusten els paràmetres

Sense afegir cap experiment: la mateixa lògica deixa les mesures.

| Pregunta | D'on surt | Ajusta |
|---|---|---|
| **Quant costa baixar al 50 % en vall?** | kWh i € del P110M entre les 00 i l'hora que s'hi arriba | `hr_vall` |
| **Quantes hores aguanta abans de tornar a pujar?** | Hores del 50 % al llindar de pla i de punta, amb l'aparell aturat | `hr_vall`, i si el pre-assecat surt a compte |
| **Quanta aigua treu per kWh?** | L'hora del codi 32 (dipòsit ple, 3,8 L) i els kWh fins llavors; al soterrani, amb la bomba, cal una altra via | Tota l'economia |
| **Asseca de debò la ventilació?** | Com baixa el Td del soterrani per hora de ventiladors, amb el ΔTd que hi havia | `delta_td_on` / `delta_td_off` |
| **Contra què s'ha de comparar?** | Quin dels dos ΔTd gravats —planta baixa o exterior— s'assembla més al que baixa el Td del soterrani quan es ventila | `referencia_ventilacio` |
| **El racó dolent segueix l'aparell?** | La correcció del segon nivell: quantes vegades i quant | `correccio_minuts` |

## Mètode

1. **Una setmana de base al soterrani** amb el deshumidificador fix al 55 % i els ventiladors com
   ara. Sense base no es pot dir quant estalvia la v2.
2. **A casa es poden mesurar els costos, no el rebot**: les hores que aguanta el 50 % depenen de
   les parets del soterrani.
3. **Tot per PR**, amb la rèplica offline: cada canvi de llindar o d'estat es prova contra
   l'històric abans de desplegar.

## El que falta per tancar-la

- ❓ **Models i cabal dels ventiladors** (l'usuari en té fotos).
- ❓ **La porta de l'escala**: oberta o tancada, habitualment.
- ❓ **Si els S110E tenen temporitzador propi** (apagada automàtica), per a la fallada segura.
- ⏳ **Els DS18B20 de paret** (B.2), perquè la urgència miri la paret i no només l'aire.
- ⏳ **La prova de fum** (0.1): si l'aire entra pel terra, la ventilació es reconsidera sencera.
- 📌 **Filament en caixes estanques amb dessecant**, faci el que faci el soterrani: a un 55 %
  ja agafa massa humitat.
