# Conveni de noms d'entitat

> **Fase A.8.** S'ha de fixar **abans d'emparellar o renombrar res**, i després no es toca.

## Per què això és seriós

Un canvi d'`entity_id` **parteix la sèrie històrica**. Home Assistant no reanomena l'històric:
crea una entitat nova i l'antiga es queda morta amb les dades velles dins. En un informe
pericial, **un salt inexplicat a la sèrie és una esquerda**, i arreglar-ho a posteriori vol
dir editar la base de dades a mà.

Els noms que posa sol l'integrador són del tipus `sensor.t315_a4c138_temperature`. Això no és
un nom: és un número de sèrie. Si un dia es reempara el dispositiu, canvia.

## La regla

```
sensor.<zona>_<punt>_<magnitud>
```

| Part | Valors permesos |
|---|---|
| `zona` | `soterrani` · `baixa` · `exterior` |
| `punt` | `fons` · `centre` · `gran` · *(buit si la zona té un sol punt)* |
| `magnitud` | `temperatura` · `humitat` · `rosada` · `bateria` · `potencia` · `energia` · `cost` |

## Taula d'entitats

### Sensors d'ambient — font: **Matter** (hub H110 via `matter-server`)

| Aparell | Ubicació | `entity_id` de temperatura | `entity_id` d'humitat |
|---|---|---|---|
| Tapo T315 | Soterrani, fons | `sensor.soterrani_fons_temperatura` | `sensor.soterrani_fons_humitat` |
| Tapo T315 | Soterrani, centre | `sensor.soterrani_centre_temperatura` | `sensor.soterrani_centre_humitat` |
| Tapo T310 | Soterrani, gran | `sensor.soterrani_gran_temperatura` | `sensor.soterrani_gran_humitat` |
| Tapo T315 | Planta baixa | `sensor.baixa_temperatura` | `sensor.baixa_humitat` |
| Tapo T310 | Exterior | `sensor.exterior_temperatura` | `sensor.exterior_humitat` |

### Temperatura de superfície — font: ESPHome

| Aparell | Ubicació | `entity_id` |
|---|---|---|
| DS18B20 | Paret freda 1 | `sensor.soterrani_paret_1_superficie` |
| DS18B20 | Paret freda 2 | `sensor.soterrani_paret_2_superficie` |

### Actuadors i mesura — font: **Matter** (vegeu la nota de sota)

| Aparell | Funció | `entity_id` |
|---|---|---|
| Tapo P110M | Deshumidificador | `switch.deshumidificador` · `sensor.deshumidificador_potencia` · `sensor.deshumidificador_energia` |
| Tapo S110E | Ventilador 1 | `switch.ventilador_1` · `sensor.ventilador_1_potencia` |
| Tapo S110E | Ventilador 2 | `switch.ventilador_2` · `sensor.ventilador_2_potencia` |
| Tapo T300 | Inundació | `binary_sensor.soterrani_inundacio` |

**L'endoll en publica nou més**, que Matter bateja sol i que en renombrar el dispositiu han
quedat amb el mateix prefix: `sensor.deshumidificador_effective_voltage` i
`…_effective_current` (tensió i corrent), `…_energy_exported`,
`select.deshumidificador_power_on_behavior` —el **comportament després d'un tall**, que ha
d'estar en `on`—, `update.deshumidificador_microprogramari`, `button.deshumidificador_identifica`
i tres sensors de diagnòstic desactivats. **No són al conveni perquè no els fa servir ningú**;
hi consten perquè existeixen i perquè la decisió sobre tensió i corrent és oberta.

> **La nota, que fins avui faltava (21/09/2026).** Que la font sigui Matter vol dir que
> l'aparell ha de **parlar Matter**: el hub **H110** i els **S110E** sí, i l'endoll també,
> perquè és un **P110M** i no un P110 pelat — confirmat pel que anuncia a la xarxa
> ([inventari.md](inventari.md)).
>
> ✅ **Tots renombrats** (verificat el 21/09/2026): els **sis del hub** i, amb l'emparellament
> de l'endoll, els **dotze del P110M**. La casella A.8 queda tancada per al maquinari que hi
> ha avui; queden els **S110E** de la Fase C.
>
> ⚠️ Matter bateja les entitats amb el model i un tros d'identificador
> (`sensor.tapo_p110m_power`). **Es renombren immediatament**, abans que gravin res, i es
> canvia l'**ID d'entitat**, no només el nom visible. Procediment:
> [emparellar-matter.md](emparellar-matter.md).
>
> ❓ **Tensió i corrent no són al conveni a posta.** Un endoll amb mesura també les publica, i
> no fan falta per a res del projecte. Queda per decidir si entren a `exclude.entities` del
> `recorder` (mai per glob) o si s'accepten i s'obliden → [pendents.md](../pendents.md).

### El deshumidificador per `tuya-local` — fixat el 21/09/2026, ABANS d'afegir-lo

> ✅ **Aplicat el mateix 21/09/2026:** afegit a les 18:57 i **les dotze entitats renombrades a
> les 18:59**, abans que gravessin res que valgués la pena. El dispositiu es diu
> *Deshumidificador Qlima*. La taula de sota és la definitiva.

El Qlima D825 parla en local per `tuya-local` (tasca B.1c,
[inventari.md](inventari.md#decisió-no-integrem-el-deshumidificador-per-tuya--es-reobre-provar-tuya-local)).
És **el mateix aparell** que alimenta el P110M, i per això comparteix el prefix
`deshumidificador`: el domini ja diu qui és qui.

| `entity_id` | Què és |
|---|---|
| `humidifier.deshumidificador` | **L'aparell**: engegat, **llindar d'HR** (35–80 %, de 5 en 5), mode (`auto` · `normal` · `sleep` · `laundry`), i l'HR que mesura ell (atribut `current_humidity`) |
| `sensor.deshumidificador_temperatura` | La temperatura que mesura ell (°C, en enters) |
| `binary_sensor.deshumidificador_avaria` | Avaria (codi de falla a l'atribut `fault_code`). ⚠️ **Encara no se sap si hi surten el P1 i el P2**: vegeu la nota de sota |
| `fan.deshumidificador` | La velocitat del ventilador |
| `select.deshumidificador_mode_aire` | Deshumidificar · purificar · totes dues |
| `switch.deshumidificador_silenci` · `_nit` · `_assecat_intern` | Configuració de l'aparell |
| `select.deshumidificador_indicadors` · `_temporitzador` | Configuració de l'aparell |
| `lock.deshumidificador_bloqueig_infantil` | El bloqueig dels botons |
| `sensor.deshumidificador_temps_restant` | El que queda del temporitzador (min) |

> **Les de configuració es graven, a posta.** Pensàvem desactivar el que no es fes servir, però
> un canvi de mode, de silenci o de nit **explica** un canvi de rendiment, i aquestes entitats
> només escriuen quan algú les toca: cap volum.
>
> ❓ **El P1 i el P2.** L'aparell publica dues dades que la configuració del D820A no coneix
> (les **106** i **107**, totes dues a 0 el 21/09/2026). Poden ser just el desgebratge i el
> dipòsit ple. Es mirarà quin número es mou el primer cop que l'aparell en mostri un →
> [pendents.md](../pendents.md).

> ⚠️ **Dos amos no.** Al principi, d'aquest aparell **només es llegeix i s'ajusta el llindar**.
> Qui l'engega i l'atura per a la lògica segueix sent `switch.deshumidificador`, el P110M. Que
> el `humidifier` mani també és una decisió que es prendrà a posta, no per accident.
>
> ⚠️ `tuya-local` bateja les entitats amb el nom del dispositiu i el de la funció en anglès.
> **Es renombren el mateix moment d'afegir-lo**, abans que gravin res, com es va fer amb el
> P110M ([runbook](runbook-servidor.md#-renombrar-entitats-sense-tocar-storage)).

### Derivades — les calcula `packages/rosada.yaml`

| `entity_id` | Què és |
|---|---|
| `sensor.soterrani_fons_punt_de_rosada` *(i `centre`, `gran`)* | Punt de rosada de cada punt |
| `sensor.planta_baixa_punt_de_rosada` · `sensor.exterior_punt_de_rosada` | Punt de rosada |
| `sensor.soterrani_punt_de_rosada_de_referencia` | **Referència interior** = la més alta dels tres punts |
| `sensor.dtd_interior_exterior` | `soterrani_rosada − exterior_rosada` — el criteri |
| `sensor.marge_de_condensacio` | `paret més freda − soterrani_rosada` — el KPI del fong |
| `sensor.residu_del_punt_de_rosada_exterior` | Sensor propi − estació oficial — **salut del sensor** |
| `sensor.decisio_del_soterrani` | **L'únic punt d'avaluació.** Què s'ha de fer i per què |

### Derivades — consum i tarifa, les calcula `packages/consum.yaml`

*(21/09/2026.)* Totes surten del comptador de l'endoll i del calendari de
[`tarifa.jinja`](../../config/custom_templates/tarifa.jinja). El perquè de cada decisió és a
[subministraments.md](../local/subministraments.md#el-cost-a-home-assistant).

| `entity_id` | Què és |
|---|---|
| `sensor.tarifa_periode` | Tram d'ara: `punta` · `pla` · `vall` |
| `sensor.tarifa_preu` | Preu del kWh d'ara, **amb impostos** (`EUR/kWh`); l'atribut `sense_impostos` diu el del contracte |
| `sensor.deshumidificador_cost` | **Euros acumulats**, una mostra cada 5 minuts (només si el comptador s'ha mogut). No es reinicia mai: el dia i el mes els fan les estadístiques. Als atributs hi ha la referència de l'última mostra |
| `sensor.deshumidificador_energia_punta` *(i `_pla`, `_vall`)* | kWh acumulats **en cada tram**. La pregunta de l'optimització: quina part del consum cau en punta |

> ⚠️ **`sensor.deshumidificador_cost` no es pot renombrar sense tocar el codi:** les variables
> del bloc el llegeixen pel seu `entity_id` —encara no hi ha `this`—. `comprova.sh` avisa si
> desapareix.
>
> Durant el calibratge (i fins que no s'endolli al local), el «deshumidificador» d'aquests
> noms és **el que hi hagi endollat**. El nom és el de la funció de l'endoll, com sempre.

### Paràmetres ajustables

`input_number.` : `delta_td_on` · `delta_td_off` · `hr_objectiu` · `marge_superficie_min` ·
`t_int_minima` · `hr_ext_bloqueig` · `min_on_ventilador` · `min_off_ventilador` ·
`min_off_deshumidificador`

`input_select.mode_soterrani` · `timer.override_manual`

## Com s'apliquen

1. A Home Assistant: **Configuració → Dispositius i serveis → Entitats**, buscar l'entitat i
   canviar-li l'**ID d'entitat** (no només el nom visible).
2. Fer-ho **abans** que l'entitat tingui històric que valgui la pena.
3. Deixar el nom visible en llenguatge natural («Soterrani — fons, temperatura») i l'`entity_id`
   segons la taula.

> ⚠️ **Un cop fixat, no es toca.** Si cal canviar-ne un, es documenta la data del canvi a
> [pendents.md](../pendents.md) perquè el forat de la sèrie quedi explicat i no sembli
> manipulació.

## Per què la referència interior és el **màxim** i no la mitjana

`sensor.soterrani_punt_de_rosada_de_referencia` pren **el punt de rosada més alt dels tres punts del soterrani**, no
la mitjana. Dues raons:

1. **La condensació és local.** Condensa allà on l'aire més humit troba la superfície més
   freda. Una mitjana amaga precisament el racó que té el problema.
2. **És el criteri conservador.** Si ventilem quan el pitjor punt millora, millorem tots. Amb
   la mitjana podríem ventilar mentre el racó dolent empitjora.

Els tres punts es registren igualment per separat: la **diferència entre ells** és el que dirà
si la humitat és general o localitzada.
